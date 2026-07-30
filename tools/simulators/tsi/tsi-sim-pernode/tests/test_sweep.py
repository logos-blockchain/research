"""Worker-count memory planning: analytic estimate, RAM cap, and the calibration probe."""

from __future__ import annotations

import os

import pytest

from tsi_sim import sweep
from tsi_sim.config import SimConfig

# The explosion/throttle behaviours below are properties of the FULL (unpruned) arrival matrix,
# so they pin prune_arrival=False; the pruned path's much smaller footprint is tested separately.
FULL = dict(prune_arrival=False)


def test_estimate_grows_with_n_and_k():
    small = sweep.estimate_worker_bytes(SimConfig(n_nodes=1000, k=256, **FULL))
    big_n = sweep.estimate_worker_bytes(SimConfig(n_nodes=4000, k=256, **FULL))
    big_k = sweep.estimate_worker_bytes(SimConfig(n_nodes=1000, k=2160, **FULL))
    assert big_n > small and big_k > small          # both N (via A + N^2) and k (via n_blocks)


def test_low_genesis_d_factor_explodes_block_estimate():
    # The collapsed-D_est regime: a 100x-low genesis estimate inflates lottery wins ~100x, so
    # the peak-epoch block count explodes. Without pruning that blows up A (the OOM that froze the
    # box); the estimate must reflect it.
    hi = SimConfig(n_nodes=1000, k=2160, stake_dist="pareto", genesis_d_factor=0.5, **FULL)
    lo = SimConfig(n_nodes=1000, k=2160, stake_dist="pareto", genesis_d_factor=0.01, **FULL)
    assert sweep.expected_peak_blocks(lo) > 20 * sweep.expected_peak_blocks(hi)
    assert sweep.expected_peak_blocks(lo) > 10 * (10 * lo.k)      # far past the ~10*k equilibrium
    assert sweep.estimate_worker_bytes(lo) > 10 * 1024**3         # unpruned -> tens of GB/worker


def test_prune_shrinks_estimate_and_keeps_all_workers(monkeypatch):
    # The whole point of prune_arrival (default on): the same gdf=0.01 config no longer needs a
    # huge per-worker matrix, so it stays well under a GB and does NOT throttle the worker pool.
    monkeypatch.setattr(sweep, "_total_ram_bytes", lambda: 51 * 1024**3)
    lo = SimConfig(n_nodes=1000, k=2160, stake_dist="pareto", genesis_d_factor=0.01)  # prune on
    assert sweep.estimate_worker_bytes(lo) < 1 * 1024**3          # vs >10 GB unpruned
    plan = sweep.plan_workers(requested=-1, configs=[lo], mem_frac=0.7, calibrate="never")
    assert plan.n_jobs == (os.cpu_count() or 1)                   # all cores, no throttle


def test_low_gdf_caps_workers_hard(monkeypatch):
    monkeypatch.setattr(sweep, "_total_ram_bytes", lambda: 51 * 1024**3)
    lo = SimConfig(n_nodes=1000, k=2160, stake_dist="pareto", genesis_d_factor=0.01, **FULL)
    plan = sweep.plan_workers(requested=-1, configs=[lo], mem_frac=0.7, calibrate="never")
    assert plan.n_jobs * plan.per_worker_bytes <= int(0.7 * 51 * 1024**3) + plan.per_worker_bytes
    assert plan.n_jobs <= 2                          # unpruned: was 14 -> ~206 GB; now a couple


def test_auto_calibration_fires_on_bytes_threshold(monkeypatch):
    # Even at small N, a heavy per-worker estimate (low gdf, unpruned) must trigger the probe.
    seen = {}

    def _probe(cfg, **k):
        seen["n"] = cfg.n_nodes
        return 3 * 1024**3
    monkeypatch.setattr(sweep, "_total_ram_bytes", lambda: 64 * 1024**3)
    monkeypatch.setattr(sweep, "measure_worker_bytes", _probe)
    lo = SimConfig(n_nodes=1000, k=2160, stake_dist="pareto", genesis_d_factor=0.01, **FULL)
    plan = sweep.plan_workers(requested=-1, configs=[lo], mem_frac=0.7, calibrate="auto")
    assert plan.calibrated and seen.get("n") == 1000     # probed despite N <= 2000


def test_arrival_matrix_guard_raises_before_allocation(monkeypatch):
    # Budget chosen so path_latency (100x100 -> ~0.18 MB) fits but the block-exploded A
    # (gdf=0.01 -> ~30k blocks -> ~25 MB) does not, so the *arrival-matrix* guard is what fires.
    from tsi_sim.engine import run_trajectory
    from tsi_sim.memguard import ArrivalMatrixTooLarge
    monkeypatch.setenv("TSI_ARRIVAL_BYTES_BUDGET", str(1_000_000))
    cfg = SimConfig(n_nodes=100, k=32, epochs=1, topology="regular", degree=4,
                    stake_dist="pareto", genesis_d_factor=0.01, prune_arrival=False)
    with pytest.raises(ArrivalMatrixTooLarge, match="arrival matrix A"):
        run_trajectory(cfg)


def test_pruned_arrival_buffer_guard_raises(monkeypatch):
    # The pruned buffer is guarded too. Budget (0.4 MB) is chosen so path_latency (~0.18 MB) fits
    # but the sliding buffer (~1.4 MB, vs a ~21 MB full matrix here) does not — so the *pruned*
    # guard fires, and the message distinguishes it from the full-matrix one.
    from tsi_sim.engine import run_trajectory
    from tsi_sim.memguard import ArrivalMatrixTooLarge
    monkeypatch.setenv("TSI_ARRIVAL_BYTES_BUDGET", str(400_000))
    cfg = SimConfig(n_nodes=100, k=32, epochs=1, topology="regular", degree=4,
                    stake_dist="pareto", genesis_d_factor=0.01, prune_arrival=True)
    with pytest.raises(ArrivalMatrixTooLarge, match="pruned arrival buffer"):
        run_trajectory(cfg)


def test_path_latency_guard_raises_before_allocation(monkeypatch):
    # The (N x N) path_latency is guarded too, BEFORE the arrival matrix is ever reached
    # (it is built first in run_trajectory) — so a large-N / small-n_blocks config can't slip past.
    from tsi_sim import topology
    from tsi_sim.memguard import ArrivalMatrixTooLarge
    monkeypatch.setenv("TSI_ARRIVAL_BYTES_BUDGET", "1024")
    cfg = SimConfig(n_nodes=300, k=8, topology="full_mesh")
    import numpy as np
    with pytest.raises(ArrivalMatrixTooLarge):
        topology.build_path_latency(cfg, np.random.default_rng(0))


def test_unset_budget_defaults_to_ram_fraction(monkeypatch):
    # "0"/unset is NOT unlimited: it resolves to a fraction of physical RAM, so a bare
    # run_trajectory / tsi-verify / mem_frac=0 run still has an absolute per-process ceiling.
    from tsi_sim import memguard
    from tsi_sim.engine import run_trajectory
    monkeypatch.setattr(memguard, "total_ram_bytes", lambda: 32 * 1024**3)
    monkeypatch.delenv("TSI_ARRIVAL_BYTES_BUDGET", raising=False)
    assert memguard.arrival_budget_bytes() == int(memguard.DEFAULT_BUDGET_FRAC * 32 * 1024**3)
    monkeypatch.setenv("TSI_ARRIVAL_BYTES_BUDGET", "0")
    assert memguard.arrival_budget_bytes() == int(memguard.DEFAULT_BUDGET_FRAC * 32 * 1024**3)
    monkeypatch.setenv("TSI_ARRIVAL_BYTES_BUDGET", str(5 * 1024**3))
    assert memguard.arrival_budget_bytes() == 5 * 1024**3      # explicit positive wins
    monkeypatch.delenv("TSI_ARRIVAL_BYTES_BUDGET", raising=False)
    rows = run_trajectory(SimConfig(n_nodes=80, k=8, epochs=1, topology="regular", degree=4))
    assert rows                                                # small config well under the ceiling


def test_mem_frac_zero_disables_cap():
    plan = sweep.plan_workers(requested=4, configs=[SimConfig(n_nodes=9999, k=2160)],
                              mem_frac=0.0, calibrate="never")
    assert plan.n_jobs == 4 and not plan.calibrated


def test_estimate_caps_workers_when_grid_is_heavy(monkeypatch):
    # Fix RAM so the cap is machine-independent: 16 GB budget*0.7 = 11.2 GB, config >> that -> 1.
    monkeypatch.setattr(sweep, "_total_ram_bytes", lambda: 16 * 1024**3)
    heavy = SimConfig(n_nodes=20200, k=2160, **FULL)   # unpruned -> tens of GB/worker
    plan = sweep.plan_workers(requested=8, configs=[heavy], mem_frac=0.7, calibrate="never")
    assert plan.n_jobs == 1 and plan.per_worker_bytes > 8 * 1024**3


def test_auto_does_not_probe_at_or_below_threshold(monkeypatch):
    called = False

    def _boom(*a, **k):
        nonlocal called
        called = True
        return 1
    monkeypatch.setattr(sweep, "measure_worker_bytes", _boom)
    plan = sweep.plan_workers(requested=-1, configs=[SimConfig(n_nodes=2000, k=2160)],
                              mem_frac=0.7, calibrate="auto")
    assert not called and not plan.calibrated       # N<=2000 uses the analytic estimate only


def test_auto_probes_above_threshold_and_uses_measurement(monkeypatch):
    measured = 2 * 1024**3                            # 2 GB peak RSS reported by the probe
    ram = 64 * 1024**3
    monkeypatch.setattr(sweep, "_total_ram_bytes", lambda: ram)
    monkeypatch.setattr(sweep, "measure_worker_bytes", lambda cfg, **k: measured)
    plan = sweep.plan_workers(requested=-1, configs=[SimConfig(n_nodes=3000, k=2160)],
                              mem_frac=0.7, calibrate="auto")
    assert plan.calibrated
    assert plan.per_worker_bytes == int(measured * 1.1)      # 10% headroom over the measurement
    fit = int(0.7 * ram // plan.per_worker_bytes)
    assert plan.n_jobs == min(os.cpu_count() or 1, fit)


def test_probe_failure_falls_back_to_estimate(monkeypatch):
    monkeypatch.setattr(sweep, "measure_worker_bytes", lambda cfg, **k: None)  # probe unavailable
    cfg = SimConfig(n_nodes=3000, k=2160)
    plan = sweep.plan_workers(requested=-1, configs=[cfg], mem_frac=0.7, calibrate="always")
    assert not plan.calibrated
    assert plan.per_worker_bytes == sweep.estimate_worker_bytes(cfg)


def test_ru_maxrss_unit_normalisation(monkeypatch):
    monkeypatch.setattr(sweep.sys, "platform", "darwin")
    assert sweep._ru_maxrss_bytes(1000) == 1000          # macOS already bytes
    monkeypatch.setattr(sweep.sys, "platform", "linux")
    assert sweep._ru_maxrss_bytes(1000) == 1000 * 1024   # Linux reports kibibytes


def test_measure_worker_bytes_real_spawn():
    # Exercise the real probe on a tiny config. Spawn needs an importable __main__; if the test
    # environment cannot bootstrap the child, the probe returns None (graceful) and we skip.
    got = sweep.measure_worker_bytes(SimConfig(n_nodes=40, k=6, epochs=2, degree=4), timeout=180)
    if got is None:
        pytest.skip("spawn-based calibration probe unavailable in this environment")
    assert got > 30 * 1024**2        # any real Python+numpy worker RSS clears tens of MB
