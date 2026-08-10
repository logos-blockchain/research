"""Does the uncle cap need margin under a private-chain attack? — REPORT §8.3 item 5.

Item 5: "Under attack-inflated orphaning the honest-load cap may need extra margin (owed uncles
beyond `U` defer and can age out of `W`); this report does not size it." It could not be sized
before, because the per-node engine had no private-chain strategy (§6.8) — the selfish results
came from a global race model in which uncle recovery is a free knob, not a queue with a cap.

With `adversary_strategy="selfish"` in the engine, the whole loop is present: the attack orphans
honest blocks in runs, the survivors queue for the `U` uncle slots of each canonical block, and
whatever does not drain within `W` ages out. This sweeps the cap against the attack to find the
smallest `U` that still recovers, and compares it to the honest rule `U = ceil(rho) + 1`.

Three quantities separate the two failure modes the item conflates:

  * ``p_ref_honest`` — of the honest blocks the attacker orphaned, how many got referenced at
    all. Falls for TWO different reasons, which is why the next column matters.
  * ``deep_ref_share`` — the share of examined references rejected by the first-fork rule. An
    override discards a *chain*, and only its first block is countable (§2.1), so this isolates
    "unreferenceable by construction" from "queue too small".
  * ``D_hat/D`` — what the estimator actually lands on, the thing the cap is sized to protect.

If raising `U` lifts recovery, the cap is the binding constraint and item 5 needs a bigger
number. If it does not, the loss is structural and no cap buys it back.

Run:  python scripts/selfish_uncle_margin.py   (writes runs/selfish_uncle_margin.parquet)
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
from tsi_sim.memguard import ArrivalMatrixTooLarge
from tsi_sim.rng import seedseq_for
from tsi_sim.stake import stake_for

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
RUNS.mkdir(exist_ok=True)

EPOCHS = 16
REPS = 8
N_JOBS = 12

BASE = dict(n_nodes=1000, stake_dist="pareto", topology="blend", degree=6,
            link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3,
            k=256, epochs=EPOCHS, genesis_d_factor=0.5, early_stop=False,
            adversary_strategy="selfish")

ALPHAS = [0.0, 0.2, 0.3, 0.4]
DELAYS = [8.0, 16.0]          # rho ~ 0.56 (design point) and ~1.0 (the load boundary)
CAPS = [1, 2, 3, 4]           # spec allows up to MAX_UNCLES = 4
WINDOWS = [10, 20]            # W = 10/f (recommended) and the 20/f widening of §3.4


def _cell(alpha: float, delay: float, u: int, w: int, rep: int) -> dict:
    cfg = SimConfig(**BASE, blend_delay_max=delay, max_uncles=u, window_absorption=w,
                    adversary_frac=alpha, replicate=rep)
    row = dict(alpha=alpha, blend_delay_max=delay, max_uncles=u, window_absorption=w, rep=rep)
    try:
        t = pd.DataFrame(run_trajectory(cfg))
        t = t[t.epoch >= EPOCHS // 2]
        row |= dict(collapsed=False,
                    mean_ratio=float(t.mean_ratio.mean()),
                    fork_rate=float(t.fork_rate.mean()),
                    p_ref=float(t.p_ref.mean()),
                    p_ref_honest=float(t.p_ref_honest.mean()),
                    deep_ref_share=float(t.deep_ref_share.mean()),
                    max_reorg_depth=int(t.max_reorg_depth.max()),
                    adv_share=float(t.adv_blocks.sum()
                                    / max(t.adv_blocks.sum() + t.honest_blocks.sum(), 1)))
    except ArrivalMatrixTooLarge:
        row |= dict(collapsed=True)
    return row


def sweep() -> pd.DataFrame:
    jobs = [(a, d, u, w, r) for a in ALPHAS for d in DELAYS for u in CAPS
            for w in WINDOWS for r in range(REPS)]
    df = pd.DataFrame(Parallel(n_jobs=N_JOBS, backend="loky", inner_max_num_threads=1)(
        delayed(_cell)(a, d, u, w, r) for a, d, u, w, r in jobs))
    df.to_parquet(RUNS / "selfish_uncle_margin.parquet", index=False)
    return df


def _decompose_cell(alpha: float, u: int, rep: int, delay: float = 8.0, w: int = 10) -> dict:
    """Split the honest orphans into "unreferenceable" and "eligible but unreferenced".

    ``p_ref_honest`` alone cannot answer item 5, because it falls for two unrelated reasons: a
    block can be *structurally* uncountable (buried behind the first block of an override, so no
    proposer may reference it — §2.1) or countable but starved of an uncle slot (the queue the
    cap `U` drains). Only the second is a cap-sizing problem. ``deep_ref_share`` does not
    separate them either: the proposer's candidate filter drops deep-fork blocks before they are
    ever proposed, so no deep reference is examined and the metric is 0 by construction here.
    This walks the tree and measures both directly.
    """
    cfg = SimConfig(**{**BASE, "epochs": 4}, blend_delay_max=delay, max_uncles=u,
                    window_absorption=w, adversary_frac=alpha, replicate=rep,
                    prune_arrival=False, windowed_fork_choice=False)
    stake = stake_for(cfg)
    mask = _adversary_mask(cfg, stake)
    flat = np.zeros(cfg.n_nodes, dtype=bool) if mask is None else mask
    kids = seedseq_for(cfg).spawn(cfg.epochs + 3)
    pl = topology.build_path_latency(cfg, np.random.default_rng(kids[1]))
    d_est = np.full(cfg.n_nodes, cfg.genesis_d_factor * float(stake.sum()))
    p = lottery.win_probs(stake, d_est, cfg.f)
    ws, wn = lottery.sample_wins(p, cfg.epoch_len, np.random.default_rng(kids[3]))
    slots, groups = lottery.group_by_slot(ws, wn)
    tree, A = build_tree_pernode(slots, groups, pl, cfg, np.random.default_rng(kids[4]),
                                 adversary_mask=mask)

    E, T, nb = cfg.epoch_len, cfg.period_T, tree.n_blocks
    ids = np.arange(nb)
    arrived = (A <= E).any(axis=0)
    arrived[0] = True
    h = np.where(arrived, tree.height, np.iinfo(np.int64).min)
    canon = np.zeros(nb, dtype=bool)
    b = int(np.lexsort((-ids, -tree.slot, h))[-1])
    while b > 0:
        canon[b] = True
        b = int(tree.parent[b])
    canon[0] = True
    in_win = (tree.slot >= 0) & (tree.slot < T)
    hon_orph = in_win & ~canon & ~flat[tree.leader]
    countable = hon_orph & canon[tree.parent]          # first block of its fork
    referenced = np.zeros(nb, dtype=bool)
    for cb in np.nonzero(canon)[0]:
        for un in tree.uncles[cb]:
            referenced[un] = True
    n, nc = int(hon_orph.sum()), int(countable.sum())
    return dict(alpha=alpha, max_uncles=u, rep=rep, honest_orphans=n,
                countable_share=(nc / n) if n else np.nan,
                referenced_of_countable=(int((countable & referenced).sum()) / nc)
                if nc else np.nan,
                referenced_of_all=(int((hon_orph & referenced).sum()) / n) if n else np.nan)


def decompose(reps: int = 6) -> pd.DataFrame:
    jobs = [(a, u, r) for a in (0.0, 0.2, 0.3) for u in (1, 2, 4) for r in range(reps)]
    df = pd.DataFrame(Parallel(n_jobs=N_JOBS, backend="loky", inner_max_num_threads=1)(
        delayed(_decompose_cell)(a, u, r) for a, u, r in jobs))
    df.to_parquet(RUNS / "selfish_uncle_margin_decomp.parquet", index=False)
    return df


def report_decomposition(df: pd.DataFrame) -> None:
    print("\n=== why p_ref_honest falls: structure vs queue (delta = 8, W = 10) ===")
    print(f"{'alpha':>6} {'U':>2} | {'countable share':>16} {'referenced OF those':>20}"
          f" {'referenced of all':>18}")
    for a in sorted(df.alpha.unique()):
        for u in sorted(df.max_uncles.unique()):
            g = df[(df.alpha == a) & (df.max_uncles == u)]
            print(f"{a:6.2f} {u:2d} | {g.countable_share.mean() * 100:14.1f}%"
                  f" {g.referenced_of_countable.mean() * 100:18.1f}%"
                  f" {g.referenced_of_all.mean() * 100:16.1f}%")


BAR = 0.98        # the §3.6 recovery bar, as a fraction of the true stake


def report(df: pd.DataFrame) -> None:
    ok = df[~df.collapsed]
    for w in WINDOWS:
        print(f"\n=== W = {w} block-intervals ===")
        print(f"{'delta':>6} {'alpha':>6} | " + "  ".join(f"U={u}" for u in CAPS)
              + " |  smallest U >= bar   p_ref_h  deep_ref  fork")
        for d in DELAYS:
            for a in ALPHAS:
                g = ok[(ok.window_absorption == w) & (ok.blend_delay_max == d) & (ok.alpha == a)]
                if g.empty:
                    continue
                cells, best = [], None
                for u in CAPS:
                    gu = g[g.max_uncles == u]
                    m = gu.mean_ratio.mean() if len(gu) else np.nan
                    cells.append(f"{m:.3f}")
                    if best is None and m >= BAR:
                        best = u
                ref = g[g.max_uncles == max(CAPS)]
                print(f"{d:6.1f} {a:6.2f} | " + "  ".join(cells)
                      + f" |  {str(best):>4}            {ref.p_ref_honest.mean():7.3f}"
                      + f"  {ref.deep_ref_share.mean():8.3f}  {ref.fork_rate.mean():5.3f}")
    n_col = int(df.collapsed.sum())
    if n_col:
        print(f"\n{n_col} of {len(df)} runs collapsed into the §6.2 branch (excluded above)")


def main() -> None:
    print(f"=== selfish uncle-margin sweep ({len(ALPHAS)*len(DELAYS)*len(CAPS)*len(WINDOWS)*REPS}"
          f" runs; recovery bar {BAR}) ===")
    report(sweep())
    report_decomposition(decompose())
    print(f"\nwrote {RUNS}/selfish_uncle_margin{{,_decomp}}.parquet")


if __name__ == "__main__":
    main()
