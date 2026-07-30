"""The mining benchmark must turn effort searches into a measured mint rate:
per-core and whole-machine tokens/s, with failed searches excluded."""
from pathlib import Path

import equix_bench.mining as mining
from equix_bench.mining import measure_point
from equix_bench.protocol import Result, Run
from equix_bench.registry import Adapter


def _result(wall_ns, attempts, achieved, ok=True, target=1000):
    runs = [Run(index=0, wall_ns=wall_ns, solutions=1 if achieved else 0, compile_ns=0,
                attempts=attempts, achieved_effort=achieved, verify_result=None)]
    # Winning-token wire bytes are emitted only when the target was reached:
    # a 16-byte solution and an 8-byte nonce, as the real runners produce.
    minted = achieved >= target
    return Result(ok=ok, impl_name="equix-rust", impl_version="1", impl_commit="c",
                  operation="effort", runtime_requested="try-compile", runtime_effective="compiled",
                  env={}, runs=runs, solutions_hex=["ab" * 16] if minted else None,
                  peak_rss_kb=4000, error=None,
                  winning_nonce_hex="00" * 8 if minted else None)


def _adapter():
    return Adapter(name="equix-rust", exec=["/bin/true"], protocol_version=1,
                   capabilities=["effort"], runtimes=[], env={})


def test_measure_point_rates_and_scaling(monkeypatch):
    # Every search: 0.5 s, 100 attempts, reaches the target -> 2 tokens/s/core.
    monkeypatch.setattr(mining, "run",
                        lambda a, s, r, timeout=900.0: _result(500_000_000, 100, 1000))
    p = measure_point(_adapter(), "abcd", effort=1000, samples=5, workers=4,
                      tokens_per_worker=3, nonce_bytes=8, max_attempts=1_000_000,
                      repo_root=Path("."), timeout=10)
    assert p.samples == 5
    assert abs(p.tokens_per_sec_1core - 2.0) < 1e-9   # 5 tokens / 2.5 s
    assert abs(p.token_s_mean - 0.5) < 1e-9
    assert p.attempts_mean == 100
    # 4 workers, each streams 3 tokens (3/1.5s = 2/s), no contention -> 8 tokens/s.
    assert p.ok_workers == 4
    assert abs(p.tokens_per_sec_machine - 8.0) < 1e-9
    assert abs(p.scaling_efficiency - 1.0) < 1e-9
    # Message sizes measured from every minted token: constant 16 B + 8 B.
    assert (p.solution_bytes_min, p.solution_bytes_max, p.nonce_bytes_wire) == (16, 16, 8)


def test_measure_point_excludes_failed_searches(monkeypatch):
    # achieved (500) never reaches target (1000) -> every sample rejected.
    monkeypatch.setattr(mining, "run",
                        lambda a, s, r, timeout=900.0: _result(500_000_000, 100, 500))
    p = measure_point(_adapter(), "abcd", effort=1000, samples=4, workers=2,
                      tokens_per_worker=2, nonce_bytes=8, max_attempts=1_000_000,
                      repo_root=Path("."), timeout=10)
    assert p.samples == 0
    assert p.tokens_per_sec_1core == 0
    assert p.tokens_per_sec_machine == 0


def test_distinct_nonce_ranges_do_not_overlap(monkeypatch):
    # Record the nonce_start each invocation used; ranges must be STRIDE-spaced
    # and disjoint between the 1-core samples and the concurrent worker streams.
    seen = []
    def rec(a, spec, r, timeout=900.0):
        seen.append(spec.nonce_start)
        return _result(100_000_000, 10, 1000)
    monkeypatch.setattr(mining, "run", rec)
    measure_point(_adapter(), "abcd", effort=1000, samples=3, workers=2,
                  tokens_per_worker=2, nonce_bytes=8, max_attempts=1_000_000,
                  repo_root=Path("."), timeout=10)
    S = mining.STRIDE
    # 3 sequential 1-core samples at 0,S,2S; then worker0 streams 3S,4S, worker1 5S,6S.
    assert seen[:3] == [0, S, 2 * S]
    assert sorted(seen[3:]) == [3 * S, 4 * S, 5 * S, 6 * S]
    assert len(set(seen)) == len(seen)  # all disjoint
