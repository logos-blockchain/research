"""Should the uncle reference window be measured to the uncle, or to its PARENT? (fig38)

The spec bounds the uncle's own slot: `0 < sl_A - sl_U <= w_u`. Its **parent** is unbounded —
the only requirement is that it lie on the referencing chain. So a block minted now, hanging off
a chain block from arbitrarily far back, is a legal first-fork uncle: recent by its own slot,
ancient by its parent's. Verifying it means deriving the epoch state and ledger root as of that
ancient parent, per reference, and an adversary mints them at no cost beyond lottery wins it
already has.

The proposal: measure the window to the parent instead, `sl_A - sl_parent(U) <= w_u`.

That is strictly tighter rather than an additional rule. A block strictly postdates its parent
and a referenced uncle strictly precedes its referencer (both pinned in
`tests/test_slot_ordering.py`), so

    sl_A - sl_U  <  sl_A - sl_parent(U)  <=  w_u

and bounding the parent bounds the uncle for free. A "both windows" variant would be identical
to the parent one, so only two arms are simulated.

Two questions, and they trade off:
  * **What does it buy?**  The effort an adversary can force, measured as the age of the oldest
    chain state a validator must reach for a *counted* reference.
  * **What does it cost?**  Honest recovery. A latency orphan's parent is recent by construction,
    so the prediction is ~nothing — but the parent gap runs about one block-interval longer than
    the uncle gap, so the same numeric `w_u` is effectively a tighter window and the margin
    shrinks as delay grows. This sweeps delay to find where it starts to bind.

Run:  python scripts/uncle_parent_window.py   (writes runs/uncle_parent_window.parquet + fig38)
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
from tsi_sim.plotting import style
from tsi_sim.rng import seedseq_for
from tsi_sim.stake import stake_for

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
FIGS = HERE / "report-figures"
RUNS.mkdir(exist_ok=True)
FIGS.mkdir(exist_ok=True)

REPS = 10
N_JOBS = 10
ANCHORS = ["uncle", "parent"]
DELAYS = [4.0, 8.0, 16.0]          # the deployed point, the report's design point, the boundary
ADVS = [0.0, 0.3]

BASE = dict(n_nodes=600, stake_dist="pareto", topology="blend", degree=6,
            link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
            max_uncles=4, uncle_strategy="oldest", window_absorption=10.0,
            k=256, epochs=10, genesis_d_factor=0.5, early_stop=False,
            prune_arrival=False, windowed_fork_choice=False)


def _recovery(anchor: str, delay: float, adv: float, rep: int) -> dict:
    """Accuracy arm: what the estimator lands on under each rule."""
    cfg = SimConfig(**BASE, uncle_window_anchor=anchor, blend_delay_max=delay,
                    adversary_frac=adv, adversary_strategy="deep_parent", replicate=rep)
    t = pd.DataFrame(run_trajectory(cfg))
    t = t[t.epoch >= t.epoch.max() // 2]
    return dict(anchor=anchor, blend_delay_max=delay, adversary_frac=adv, rep=rep,
                mean_ratio=float(t.mean_ratio.mean()), p_ref=float(t.p_ref.mean()),
                fork_rate=float(t.fork_rate.mean()),
                range_ratio=float(t.range_ratio.max()))


def _effort(anchor: str, delay: float, adv: float, rep: int) -> dict:
    """Effort arm: how far back a validator must reach for the references that COUNT.

    Rebuilds one epoch's tree and reads the parent gap of every reference the counting rule
    would accept — the direct proxy for historical state a validator must materialise.
    """
    cfg = SimConfig(**{**BASE, "epochs": 2}, uncle_window_anchor=anchor,
                    blend_delay_max=delay, adversary_frac=adv,
                    adversary_strategy="deep_parent", replicate=rep)
    kids = seedseq_for(cfg).spawn(cfg.epochs + 3)
    stake = stake_for(cfg)
    mask = _adversary_mask(cfg, stake)
    pl = topology.build_path_latency(cfg, np.random.default_rng(kids[1]))
    d = np.full(cfg.n_nodes, cfg.genesis_d_factor * float(stake.sum()))
    ws, wn = lottery.sample_wins(lottery.win_probs(stake, d, cfg.f), cfg.epoch_len,
                                 np.random.default_rng(kids[3]))
    slots, groups = lottery.group_by_slot(ws, wn)
    tree, _A = build_tree_pernode(slots, groups, pl, cfg, np.random.default_rng(kids[4]),
                                  adversary_mask=mask)
    s, par = tree.slot, tree.parent
    gaps = np.array([int(s[b] - s[par[u]])
                     for b in range(1, tree.n_blocks) for u in tree.uncles[b]], dtype=np.int64)
    if gaps.size == 0:
        gaps = np.zeros(1, dtype=np.int64)
    return dict(anchor=anchor, blend_delay_max=delay, adversary_frac=adv, rep=rep,
                n_refs=int(gaps.size), gap_median=float(np.median(gaps)),
                gap_p99=float(np.percentile(gaps, 99)), gap_max=int(gaps.max()),
                distinct_parent_slots=int(np.unique(gaps).size))


def sweep() -> tuple[pd.DataFrame, pd.DataFrame]:
    jobs = [(a, d, v, r) for a in ANCHORS for d in DELAYS for v in ADVS for r in range(REPS)]
    par = Parallel(n_jobs=N_JOBS, backend="loky", inner_max_num_threads=1)
    rec = pd.DataFrame(par(delayed(_recovery)(*j) for j in jobs))
    eff = pd.DataFrame(par(delayed(_effort)(*j) for j in jobs))
    rec.to_parquet(RUNS / "uncle_parent_window.parquet", index=False)
    eff.to_parquet(RUNS / "uncle_parent_window_effort.parquet", index=False)
    return rec, eff


def report(rec: pd.DataFrame, eff: pd.DataFrame, w: int) -> None:
    print(f"\n=== what it COSTS: honest recovery (adversary_frac = 0), w_u = {w} slots ===")
    print(f"{'δ_max':>6} {'ρ':>6} | {'uncle-anchored':>18} {'parent-anchored':>18} {'Δ':>9}")
    for d in DELAYS:
        row = []
        for a in ANCHORS:
            g = rec[(rec.anchor == a) & (rec.blend_delay_max == d) & (rec.adversary_frac == 0)]
            row.append((g.mean_ratio.mean(), g.mean_ratio.sem()))
        rho = SimConfig(**BASE, blend_delay_max=d).f * (3 * d / 2 + 4 * 0.5)
        print(f"{d:6.0f} {rho:6.2f} | {row[0][0]:10.4f}±{row[0][1]:.4f} "
              f"{row[1][0]:10.4f}±{row[1][1]:.4f} {row[1][0] - row[0][0]:+9.4f}")

    print("\n=== what it BUYS: age of chain state a counted reference reaches (slots) ===")
    print(f"{'δ_max':>6} {'adv':>5} | {'anchor':>7} {'refs':>6} {'median':>9} "
          f"{'p99':>9} {'max':>9}")
    for d in DELAYS:
        for v in ADVS:
            for a in ANCHORS:
                g = eff[(eff.anchor == a) & (eff.blend_delay_max == d) & (eff.adversary_frac == v)]
                flag = "" if g.gap_max.max() <= w else "   <-- EXCEEDS w_u"
                print(f"{d:6.0f} {v:5.1f} | {a:>7} {g.n_refs.mean():6.0f} "
                      f"{g.gap_median.mean():9.0f} {g.gap_p99.mean():9.0f} "
                      f"{g.gap_max.max():9.0f}{flag}")


def fig38(rec: pd.DataFrame, eff: pd.DataFrame, w: int) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8))

    ax = axes[0]
    for i, a in enumerate(ANCHORS):
        g = (rec[(rec.anchor == a) & (rec.adversary_frac == 0)]
             .groupby("blend_delay_max").mean_ratio.agg(["mean", "sem"]).reset_index())
        ax.errorbar(g.blend_delay_max, g["mean"], yerr=g["sem"], marker="o", ms=4, capsize=2,
                    color=style.OKABE_ITO[i + 1], label=f"{a}-anchored window")
    ax.axhline(1.0, color="0.5", lw=0.9, ls="--")
    ax.set_xlabel(r"Blend per-hop delay $\delta_{max}$ (s)")
    ax.set_ylabel(r"$\hat D / D^*$  (honest)")
    ax.set_title("Cost: honest recovery is unchanged")
    ax.legend(fontsize=7, loc="lower left")

    ax = axes[1]
    x = np.arange(len(DELAYS))
    for i, a in enumerate(ANCHORS):
        vals = [eff[(eff.anchor == a) & (eff.blend_delay_max == d)
                    & (eff.adversary_frac == 0.3)].gap_max.max() for d in DELAYS]
        ax.bar(x + (i - 0.5) * 0.36, vals, 0.36, color=style.OKABE_ITO[i + 1],
               label=f"{a}-anchored")
    ax.axhline(w, color=style.OKABE_ITO[0], lw=1.2, ls="--", label=rf"$w_u$ = {w} slots")
    ax.set_yscale("log")
    ax.set_xticks(x, [f"{d:.0f}" for d in DELAYS])
    ax.set_xlabel(r"Blend per-hop delay $\delta_{max}$ (s)")
    ax.set_ylabel("oldest chain state a counted\nreference reaches (slots, log)")
    ax.set_title("Benefit: a 30 % adversary's reach, bounded")
    ax.legend(fontsize=7, loc="upper left")

    style.save(fig, FIGS / "fig38_uncle_parent_window",
               provenance="scripts/uncle_parent_window.py")
    plt.close(fig)


def main() -> None:
    w = SimConfig(**BASE, blend_delay_max=4.0).effective_uncle_window
    print(f"=== uncle- vs parent-anchored reference window (w_u = {w} slots) ===")
    rec, eff = sweep()
    report(rec, eff, w)
    fig38(rec, eff, w)
    print(f"\nwrote {RUNS}/uncle_parent_window{{,_effort}}.parquet + fig38")


if __name__ == "__main__":
    main()
