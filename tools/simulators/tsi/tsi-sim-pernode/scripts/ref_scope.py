"""Where may the density count read its references from? (§6.13)

The spec's epoch pseudocode draws ``referenced_uncles`` from the chain blocks that lie in the
observation window, so a block past the window's end cannot add occupied slots to a window that
has already closed. The earlier wording gated on the uncle's own slot alone and let any chain
block reach back: a block up to ``w_u`` slots past the end could still contribute.

Three arms, and the two exact ones carry no sampling noise at all:

* **Slot loss (paired, noiseless).** ``ref_scope`` is a MEASUREMENT rule that consumes no RNG
  and is excluded from ``key()``, so both scopes read a bit-identical block tree. Measuring the
  same tree twice therefore isolates the rule's effect exactly: the difference in ``m`` is the
  occupied slots the scoping drops. The loss is a boundary phenomenon — the orphans in the last
  stretch of the window whose every referencer landed past the end — so its size is set by the
  uncle cap and the suppression rate (how long a reference queues) rather than by ``k``, which
  is why the deployed geometry is measured directly below rather than extrapolated.
  All trees are drawn at ``genesis_d_factor = 1.0`` so occupancy sits at the design density
  ``f*T = 6*k``; drawing them at 0.5 doubles the density and distorts the ratio.
* **Accuracy.** What the estimator lands on over a trajectory — the form the recommendation is
  stated in, and (as it turns out) too noisy to see the effect at all.
* **Crossing check** (``crossing_check``). Whether the scoping perturbs the §6.12 paired
  *anchor* difference, whose standard error (0.00018) is the same order as the per-arm loss.
  Run at the crossing sweep's own geometry, one tree per arm.

Run:  python scripts/ref_scope.py    (writes runs/ref_scope{,_loss,_anchor}.parquet)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from tsi_sim import lottery, topology
from tsi_sim.blocktree import build_tree_pernode
from tsi_sim.config import SimConfig
from tsi_sim.engine import _adversary_mask, run_trajectory
from tsi_sim.measure import measure
from tsi_sim.rng import seedseq_for
from tsi_sim.stake import stake_for

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
RUNS.mkdir(exist_ok=True)

REPS = 10
N_JOBS = 10
SCOPES = ["window", "chain"]
DELAYS = [4.0, 8.0]                # the deployed point and the report's design point
ADVS = [0.0, 0.3]
K_DEPLOYED = 2160                  # reference geometry; measured directly by crossing_check

# The adopted rules: parent-anchored window at W = 12 (§6.12).
BASE = dict(n_nodes=600, stake_dist="pareto", topology="blend", degree=6,
            link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
            max_uncles=4, uncle_strategy="oldest", window_absorption=12.0,
            uncle_window_anchor="parent", k=256, epochs=10, genesis_d_factor=1.0,
            early_stop=False, prune_arrival=False, windowed_fork_choice=False)


def _accuracy(scope: str, delay: float, adv: float, rep: int) -> dict:
    cfg = SimConfig(**BASE, ref_scope=scope, blend_delay_max=delay, adversary_frac=adv,
                    adversary_strategy="suppress", replicate=rep)
    t = pd.DataFrame(run_trajectory(cfg))
    t = t[t.epoch >= t.epoch.max() // 2]
    return dict(scope=scope, blend_delay_max=delay, adversary_frac=adv, rep=rep,
                mean_ratio=float(t.mean_ratio.mean()), p_ref=float(t.p_ref.mean()),
                fork_rate=float(t.fork_rate.mean()))


def _slot_loss(delay: float, adv: float, rep: int) -> dict:
    """Exact per-tree slot loss: measure ONE tree under both scopes.

    No RNG is consumed by the scope, so this is the same tree twice — the difference is the
    rule's effect and nothing else.
    """
    cfg = SimConfig(**{**BASE, "epochs": 2}, blend_delay_max=delay, adversary_frac=adv,
                    adversary_strategy="suppress", replicate=rep)
    kids = seedseq_for(cfg).spawn(cfg.epochs + 3)
    stake = stake_for(cfg)
    mask = _adversary_mask(cfg, stake)
    pl = topology.build_path_latency(cfg, np.random.default_rng(kids[1]))
    d = np.full(cfg.n_nodes, cfg.genesis_d_factor * float(stake.sum()))
    ws, wn = lottery.sample_wins(lottery.win_probs(stake, d, cfg.f), cfg.epoch_len,
                                 np.random.default_rng(kids[3]))
    slots, groups = lottery.group_by_slot(ws, wn)
    tree, A = build_tree_pernode(slots, groups, pl, cfg, np.random.default_rng(kids[4]),
                                 adversary_mask=mask)
    T, E = cfg.period_T, cfg.epoch_len
    kw = dict(countable=True, w=cfg.effective_uncle_window, parent_anchor=True)
    win = measure(tree, A, slots, T, cutoff=E, scope_refs=True, **kw)
    chain = measure(tree, A, slots, T, cutoff=E, scope_refs=False, **kw)
    lost = chain.m.astype(np.int64) - win.m.astype(np.int64)
    return dict(blend_delay_max=delay, adversary_frac=adv, rep=rep,
                m_window=float(win.m.mean()), m_chain=float(chain.m.mean()),
                lost_mean=float(lost.mean()), lost_max=int(lost.max()),
                occupied=float(chain.m.mean()), T=int(T),
                rel=float(lost.mean() / chain.m.mean()))


def _anchor_scope(anchor: str, rep: int) -> dict:
    """Does the scoping perturb the §6.12 paired ANCHOR difference (the W-crossing)?

    The crossing is a paired difference between the two anchors, quoted at a standard error of
    0.00018 — the same order as the scoping's effect on a single arm. What matters there is not
    how much each arm loses but whether the two lose *differently*. Run at the crossing sweep's
    own geometry (k = 2160, N = 1000, δ_max = 8, U = 2, W = 12, 30 % suppression,
    ``paired_streams`` so both anchors share the lottery and graph) and read the loss per anchor
    off ONE tree per arm, so the arm-to-arm comparison carries no sampling noise either.
    """
    cfg = SimConfig(n_nodes=1000, stake_dist="pareto", topology="blend", degree=6,
                    link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
                    blend_delay_max=8.0, window_absorption=12.0, max_uncles=2,
                    uncle_strategy="oldest", init_dest="common", k=2160, epochs=2,
                    f=1 / 30, genesis_d_factor=1.0, early_stop=False, adversary_frac=0.3,
                    adversary_strategy="suppress", paired_streams=True,
                    prune_arrival=False, windowed_fork_choice=False,
                    uncle_window_anchor=anchor, replicate=rep)
    kids = seedseq_for(cfg).spawn(cfg.epochs + 3)
    stake = stake_for(cfg)
    mask = _adversary_mask(cfg, stake)
    pl = topology.build_path_latency(cfg, np.random.default_rng(kids[1]))
    d = np.full(cfg.n_nodes, cfg.genesis_d_factor * float(stake.sum()))
    ws, wn = lottery.sample_wins(lottery.win_probs(stake, d, cfg.f), cfg.epoch_len,
                                 np.random.default_rng(kids[3]))
    slots, groups = lottery.group_by_slot(ws, wn)
    tree, A = build_tree_pernode(slots, groups, pl, cfg, np.random.default_rng(kids[4]),
                                 adversary_mask=mask)
    T, E = cfg.period_T, cfg.epoch_len
    kw = dict(countable=True, w=cfg.effective_uncle_window,
              parent_anchor=anchor == "parent")
    win = measure(tree, A, slots, T, cutoff=E, scope_refs=True, **kw)
    chain = measure(tree, A, slots, T, cutoff=E, scope_refs=False, **kw)
    lost = float((chain.m.astype(np.int64) - win.m.astype(np.int64)).mean())
    return dict(anchor=anchor, rep=rep, occupied=float(chain.m.mean()), lost=lost,
                rel=lost / float(chain.m.mean()))


def crossing_check(reps: int = 12) -> None:
    rows = pd.DataFrame(Parallel(n_jobs=N_JOBS)(
        delayed(_anchor_scope)(a, r) for a in ("uncle", "parent") for r in range(reps)))
    rows.to_parquet(RUNS / "ref_scope_anchor.parquet")
    print("\n=== effect on the §6.12 paired anchor difference (k=2160 capstone geometry) ===")
    print(rows.groupby("anchor")[["occupied", "lost", "rel"]].mean().to_string())
    piv = rows.pivot_table(index="rep", columns="anchor", values="lost")
    delta = piv["uncle"] - piv["parent"]
    occ = rows.occupied.mean()
    se = delta.std(ddof=1) / np.sqrt(len(delta))
    print(f"\nper-replicate difference in slots lost (uncle - parent): "
          f"{delta.mean():+.3f} +/- {se:.3f} slots of {occ:.0f} occupied")
    print(f"  => perturbation of the paired anchor difference: "
          f"{delta.mean() / occ:+.7f} (crossing SE is 0.00018)")


def main() -> None:
    loss_jobs = [(d, v, r) for d in DELAYS for v in ADVS for r in range(REPS)]
    loss = pd.DataFrame(Parallel(n_jobs=N_JOBS)(
        delayed(_slot_loss)(*j) for j in loss_jobs))
    loss.to_parquet(RUNS / "ref_scope_loss.parquet")
    print("=== exact slot loss (paired on identical trees, k=256) ===")
    print(loss.groupby(["blend_delay_max", "adversary_frac"])[
        ["m_chain", "m_window", "lost_mean", "lost_max", "rel"]].mean().to_string())

    acc_jobs = [(s, d, v, r) for s in SCOPES for d in DELAYS for v in ADVS
                for r in range(REPS)]
    acc = pd.DataFrame(Parallel(n_jobs=N_JOBS)(
        delayed(_accuracy)(*j) for j in acc_jobs))
    acc.to_parquet(RUNS / "ref_scope.parquet")
    print("\n=== accuracy over trajectories (k=256) ===")
    piv = acc.pivot_table(index=["blend_delay_max", "adversary_frac"], columns="scope",
                          values=["mean_ratio", "p_ref"])
    print(piv.to_string())
    d = acc.pivot_table(index=["blend_delay_max", "adversary_frac", "rep"], columns="scope",
                        values="mean_ratio")
    diff = (d["window"] - d["chain"])
    print(f"\npaired mean_ratio delta (window - chain): {diff.mean():+.6f} "
          f"+/- {diff.std(ddof=1) / np.sqrt(len(diff)):.6f} (n={len(diff)})")


if __name__ == "__main__":
    main()
