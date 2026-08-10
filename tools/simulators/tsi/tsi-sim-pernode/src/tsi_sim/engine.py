"""Multi-epoch per-node trajectory driver for a single config."""

from __future__ import annotations

import warnings
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
    """Nodes controlled by the uncle-suppressing adversary — a coalition whose stake sums to
    ``adversary_frac`` of the total, giving smooth control of the adversary's block share.
    ``None`` if honest.

    ``adversary_selection`` picks *which* nodes, at that same total stake:

    * ``"random"`` (default) — a uniformly random set. For uncle suppression the deflation depends
      only on the summed block share, not on whether the coalition is one whale or many small
      nodes, so this is the neutral choice and concentration does not enter.
    * ``"whale"`` — the largest holders first. Same stake in far fewer nodes, so the coalition's
      block production is lumpier: it is the concentration case report §6.5 flags as untested, and
      the reason to run it is the *variance* of the coalition's share, not its mean.

    Seeded from a standalone ``SeedSequence([root_seed, replicate, 0xADEADBEEF])`` (independent of
    the main spawn hierarchy), and drawn only after the ``adversary_frac <= 0`` early return, so an
    ``adversary_frac == 0`` run is bit-identical to the honest baseline. The whale order is
    deterministic given the stake vector and consumes no randomness, but the seed is still drawn
    first so that switching selection never perturbs the rest of the stream.
    """
    if config.adversary_frac <= 0.0:
        return None
    adv_seed = np.random.SeedSequence([config.root_seed, config.replicate, 0xADEADBEEF])
    rand_order = np.random.default_rng(adv_seed).permutation(config.n_nodes)
    target = config.adversary_frac * float(stake.sum())
    mask = np.zeros(config.n_nodes, dtype=bool)

    if config.adversary_selection == "whale":
        # Largest stake first, ties broken by the random order so equal-stake runs stay unbiased.
        # Taking whales until the cumulative sum first EXCEEDS the target would overshoot badly
        # under a heavy tail (the top holder alone can be a sixth of the stake), and a coalition
        # holding visibly more than adversary_frac would confound concentration with stake. So:
        # walk descending and take every node that still FITS under the target, then close any
        # remaining gap with the smallest node that can. The coalition is therefore dominated by
        # the top holders, with small nodes only topping it up onto the target — a handful of
        # members against the random arm's hundreds, at the same stake.
        order = rand_order[np.argsort(-stake[rand_order], kind="stable")]
        st = stake[order]
        chosen = np.zeros(order.size, dtype=bool)
        cum = 0.0
        for j, s in enumerate(st):
            if cum + s <= target:
                chosen[j] = True
                cum += s
        if cum < target:
            # `st` is descending, so among the nodes that can close the gap the LAST is the
            # smallest. Every skipped node exceeds the current gap (the gap only shrinks), so a
            # candidate always exists while any node remains; the fallback is defensive only.
            cand = np.nonzero(~chosen & (st >= target - cum))[0]
            chosen[cand[-1] if cand.size else np.nonzero(~chosen)[0][0]] = True
        mask[order[chosen]] = True
        return mask

    # Fit-then-close, the whale branch's rule walked in random order instead of descending: take
    # every node that still FITS under the target, then close whatever gap remains with the
    # smallest node that can.
    #
    # This replaces a plain cumulative-prefix cut ("smallest prefix reaching the target"), which
    # let a single whale straddling the cutoff carry the coalition far past its label — the exact
    # failure ``_churn_inactive_mask`` documents for the churn amplitude, never applied here.
    # Measured over 60 replicates of the Pareto default, an adversary_frac of 0.4 realised a
    # MAJORITY coalition in ~10 % of replicates and up to 0.97, and 0.2 reached 0.90, so the
    # knob's tail was simulating a different attacker than the one it names. The median was always
    # on-label, which is why it hid: it distorted the tail, not the centre.
    #
    # Nearest-fill alone (the churn rule) is not enough: it accepts an early whale whenever
    # including it lands closer than stopping short, which is locally right and still leaves a
    # ~3 % tail of majority coalitions. Fit-then-close cannot overshoot by more than one closing
    # node. Candidate membership and RNG draw are unchanged.
    st = stake[rand_order]
    chosen = np.zeros(rand_order.size, dtype=bool)
    cum = 0.0
    for j, s in enumerate(st):
        if cum + s <= target:
            chosen[j] = True
            cum += float(s)
    if cum < target:
        cand = np.nonzero(~chosen & (st >= target - cum))[0]
        if cand.size:
            # Smallest node that closes the gap — but only if closing beats stopping short. When
            # one holder has most of the stake, nothing fits under the target and the only
            # candidate is that whale, so "close the gap" would hand over the whole network to
            # reach a 40 % label. Undershooting is then the nearer answer, and the warning below
            # reports the miss rather than letting it pass as an on-label run.
            j = cand[np.argmin(st[cand])]
            if float(st[j]) - (target - cum) < (target - cum):
                chosen[j] = True
                cum += float(st[j])
    mask[rand_order[chosen]] = True
    got = cum / float(stake.sum())
    if abs(got - config.adversary_frac) > 0.2 * config.adversary_frac:
        warnings.warn(
            f"adversary_frac={config.adversary_frac} is not reachable on this stake draw "
            f"(n_nodes={config.n_nodes}, {config.stake_dist}, replicate={config.replicate}): "
            f"realised {got:.3f}. The heavy tail leaves no subset near the label; treat this "
            f"replicate's adversary as {got:.3f}, not {config.adversary_frac}.",
            RuntimeWarning, stacklevel=2,
        )
    return mask


def _coalition_ids(config: SimConfig, stake: np.ndarray,
                   mask: np.ndarray | None) -> np.ndarray | None:
    """Split the adversarial set into ``adversary_coalitions`` rival groups of near-equal stake.

    Returns a per-node ``int8`` label: ``-1`` for honest nodes, ``0..K-1`` for coalition members.
    ``None`` when there is nothing to split (honest run, or the default single coalition), which
    keeps the single-coalition path exactly as it was.

    The split is by **stake**, not by node count: under a Pareto tail an even split of members
    would hand one group most of the adversarial power, and the question §6.9 asks is what happens
    when the same total stake is held by ``K`` *equal* rivals. Longest-processing-time first —
    walk the members in descending stake and put each into the lightest group so far — which for
    this input lands every group within one small holder of ``beta/K``.

    Deterministic given the mask and the stake vector: it draws no randomness, so adding the knob
    reseeds nothing, and ``K == 1`` returns ``None`` rather than an all-zero label for the same
    reason.
    """
    if mask is None or config.adversary_coalitions <= 1:
        return None
    members = np.nonzero(mask)[0]
    ids = np.full(config.n_nodes, -1, dtype=np.int8)
    loads = np.zeros(config.adversary_coalitions, dtype=float)
    for v in members[np.argsort(-stake[members], kind="stable")]:
        g = int(np.argmin(loads))
        ids[v] = g
        loads[g] += float(stake[v])
    return ids


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
    coal_ids = _coalition_ids(config, stake, adv_mask)
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
                            coalition_ids=coal_ids,
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
