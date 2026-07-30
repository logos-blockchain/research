"""Multi-epoch per-node trajectory driver for a single config."""

from __future__ import annotations

from typing import Any

import numpy as np

from . import topology
from .config import SimConfig
from .epoch import simulate_epoch
from .metrics import divergence_row
from .rng import seedseq_for
from .stake import make_stake

# Early-stop (config.early_stop): detector + measurement budget. The detector uses a short
# 2-epoch delta window (convergence at beta=1 is abrupt, ~2-5 epochs); ES_MIN_EPOCH keeps it
# out of the genesis transient, and ES_MEASURE post-detection epochs form the equilibrium
# sample, so a slightly eager detection still averages over converging epochs. Thresholds are
# in units of the per-epoch sampling noise sigma_th = sqrt((1-f)/(f*T)); regimes noisier than
# that (e.g. Blend U=0 fork-race noise) never trigger and simply run their full budget.
ES_MIN_EPOCH = 6      # first epoch at which the detector may fire
ES_MEASURE = 10       # measurement epochs run after detection



def _adversary_mask(config: SimConfig, stake: np.ndarray) -> np.ndarray | None:
    """Nodes controlled by the uncle-suppressing adversary — a random coalition whose stake sums to
    ``adversary_frac`` of the total, giving smooth control of the adversary's block share. (For
    uncle suppression the deflation depends only on that block share, not on whether the coalition
    is one whale or many small nodes, so concentration is not modelled here.) ``None`` if honest.

    Seeded from a standalone ``SeedSequence([root_seed, replicate, 0xADEADBEEF])`` (independent of
    the main spawn hierarchy), and drawn only after the ``adversary_frac <= 0`` early return, so an
    ``adversary_frac == 0`` run is bit-identical to the honest baseline.
    """
    if config.adversary_frac <= 0.0:
        return None
    adv_seed = np.random.SeedSequence([config.root_seed, config.replicate, 0xADEADBEEF])
    order = np.random.default_rng(adv_seed).permutation(config.n_nodes)
    target = config.adversary_frac * float(stake.sum())
    cum = np.cumsum(stake[order])
    take = int(np.searchsorted(cum, target, side="left")) + 1   # smallest coalition >= target
    mask = np.zeros(config.n_nodes, dtype=bool)
    mask[order[:take]] = True
    return mask


def _initial_d_est(config: SimConfig, d_true: float, rng: np.random.Generator) -> np.ndarray:
    """Per-node initial estimate: common genesis, or heterogeneous around it."""
    base = config.genesis_d_factor * d_true
    n = config.n_nodes
    if config.init_dest == "common" or config.init_spread <= 0.0:
        return np.full(n, base, dtype=float)
    # heterogeneous: uniform in base*(1 ± init_spread), clamped positive
    lo = max(base * (1.0 - config.init_spread), 1.0)
    hi = base * (1.0 + config.init_spread)
    return rng.uniform(lo, hi, size=n)


def _churn_active_fraction(config: SimConfig, epoch: int) -> float:
    """Active honest-stake fraction this epoch, per the churn schedule (1.0 if no churn)."""
    if config.churn_amp <= 0.0:
        return 1.0
    a, per = config.churn_amp, config.churn_period
    if config.churn_mode == "sine":
        return 1.0 - a * (1.0 - np.cos(2.0 * np.pi * epoch / per)) / 2.0
    if config.churn_mode == "ramp":
        return 1.0 - a * min(epoch / per, 1.0)
    # step: drop to 1-a at epoch `per`, hold
    return 1.0 - a if epoch >= per else 1.0


def _churn_inactive_mask(stake: np.ndarray, active_frac: float,
                         rng: np.random.Generator) -> np.ndarray:
    """A random node subset whose stake sums to ~(1-active_frac) of the total, marked inactive.

    Greedy nearest-fill in random order: while the running inactive stake is short of the
    target, a node is deactivated only if it lands the total closer to the target than stopping
    short would (the gap is at least half the node's stake). A whale that would overshoot is
    skipped and the fill continues with smaller nodes. Under a heavy-tailed (Pareto) stake
    distribution a plain cumulative-prefix cut lets a single whale straddling the cutoff
    overshoot the amplitude badly (a 30 % label realising up to ~53 %); nearest-fill keeps the
    realised amplitude on-label.
    """
    n = stake.shape[0]
    if active_frac >= 1.0:
        return np.zeros(n, dtype=bool)
    target = (1.0 - active_frac) * float(stake.sum())
    mask = np.zeros(n, dtype=bool)
    acc = 0.0
    for i in rng.permutation(n):
        if acc >= target:
            break
        s = float(stake[i])
        if (target - acc) >= 0.5 * s:      # including node i lands closer than stopping short
            mask[i] = True
            acc += s
    return mask


def run_trajectory(config: SimConfig) -> list[dict[str, Any]]:
    """Run ``config.epochs`` per-node epochs, one divergence-summary row per epoch.

    Each of the ``N`` nodes carries its OWN ``d_est`` and self-updates from its own view.
    The topology (``path_latency``) is built once (invariant across epochs). RNG is a spawn
    hierarchy off the config's root SeedSequence: child 0 = stake, 1 = graph, 2 = init,
    3+e = epoch e — so results are deterministic and order-independent.
    """
    root = seedseq_for(config)
    children = root.spawn(config.epochs + 3)
    stake = make_stake(config, np.random.default_rng(children[0]))
    d_true = float(stake.sum())
    path_latency = topology.build_path_latency(config, np.random.default_rng(children[1]))
    d_est = _initial_d_est(config, d_true, np.random.default_rng(children[2]))
    adv_mask = _adversary_mask(config, stake)
    # exact stake fraction of the (integer-rounded) coalition, for the active-stake bookkeeping
    coalition_frac = float(stake[adv_mask].sum() / d_true) if adv_mask is not None else 0.0
    withholding = adv_mask is not None and config.adversary_strategy == "withhold"
    # churn RNG is standalone (drawn only when churn_amp>0) so churn=0 stays bit-identical
    churn_rng = (np.random.default_rng(np.random.SeedSequence([config.root_seed,
                 config.replicate, 0xC4084])) if config.churn_amp > 0.0 else None)

    def _sigma_th() -> float:
        t_win = config.period_T
        return float(np.sqrt((1.0 - config.f) / (config.f * t_win)))

    def _converged(series: list[float]) -> bool:
        """2-epoch delta window: last step within sigma_th, 2-step drift within 1.5x."""
        if len(series) < 3:
            return False
        sig = _sigma_th()
        return (abs(series[-1] - series[-2]) <= sig
                and abs(series[-1] - series[-3]) <= 1.5 * sig)

    # sawtooth schedules must run their full budget; the detector would misread a rejoin ramp
    allow_early = config.early_stop and config.adversary_period == 0

    rows: list[dict[str, Any]] = []
    stop_after: int | None = None
    for epoch in range(config.epochs):
        # The coalition is fixed; the schedule only gates whether it withholds THIS epoch. On a
        # rejoin epoch it behaves fully honestly (behaviour mask None == honest baseline). A
        # suppressing coalition (or the static default) attacks every epoch.
        attacks = config.adversary_withholds(epoch) if withholding else adv_mask is not None
        behaviour_mask = adv_mask if attacks else None
        active_stake_frac = 1.0 - coalition_frac if (withholding and attacks) else 1.0
        # organic honest churn: deactivate a scheduled stake fraction this epoch
        inactive_mask = None
        if churn_rng is not None:
            active_frac = _churn_active_fraction(config, epoch)
            inactive_mask = _churn_inactive_mask(stake, active_frac, churn_rng)
            active_stake_frac = float(stake[~inactive_mask].sum() / d_true) * active_stake_frac
        er = simulate_epoch(config, stake, d_est, path_latency, children[epoch + 3],
                            adversary_mask=behaviour_mask, coalition_mask=adv_mask,
                            inactive_mask=inactive_mask)
        row = divergence_row(config, epoch, d_est, er, d_true)
        row["adversary_withholding"] = bool(withholding and attacks)
        row["active_stake_frac"] = active_stake_frac
        rows.append(row)
        d_est = er.d_next
        if allow_early and stop_after is None and epoch >= ES_MIN_EPOCH:
            if _converged([r["mean_ratio"] for r in rows]):
                stop_after = epoch + ES_MEASURE
        if stop_after is not None and epoch >= stop_after:
            break
    return rows
