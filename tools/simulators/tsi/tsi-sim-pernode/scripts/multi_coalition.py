"""Do K rival selfish coalitions deflate D-hat further than one coalition of the same size? (fig39)

§6.9 settles the *withholding* commons exactly — deflation depends on the total abstaining stake
and not on how it is partitioned — and then flags the selfish case as conjectural, on two counts
taken from the literature:

  (a) total orphaning, hence raw D-hat deflation, *can exceed* the single-coalition value, so the
      §6.6 figure at alpha = 0.4 is not a multi-coalition upper bound; and
  (b) several individually sub-threshold coalitions may be *jointly* profitable, i.e. the 1/3
      threshold is not a per-coalition safety argument.

Both are now testable. The per-node engine runs one private chain per coalition, and a rival's
unreleased blocks are invisible to every other coalition by the same arrival sentinel that hides
them from honest nodes — so the chains race each other as well as the public chain, which is the
whole mechanism the conjecture rests on. `adversary_coalitions = K` splits a fixed adversarial
stake into K near-equal rivals (`engine._coalition_ids`), holding beta constant so K is the only
thing that moves.

Two arms:
  * **accuracy** — D-hat/D, fork rate and p_ref against (beta, K), which answers (a) directly;
  * **profitability** — each coalition's share of the canonical chain against its OWN stake, which
    answers (b). A coalition profits when its canonical share exceeds its stake share; the joint
    question is whether that holds for every one of K rivals that are each below 1/3.

Both arms record the REALISED stake shares rather than trusting the knob. That is no longer a
correction for the sizing defect §9 describes (fixed: the coalition now lands within 0.1 % of its
label), but it stays because a Pareto draw can still leave `beta` unreachable — one holder above
the target — and the split into K rivals is only as even as the tail permits.

Run:  python scripts/multi_coalition.py   (writes runs/multi_coalition{,_split}.parquet + fig39)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from tsi_sim import lottery, topology
from tsi_sim.blocktree import build_tree_pernode
from tsi_sim.config import SimConfig
from tsi_sim.engine import _adversary_mask, _coalition_ids, run_trajectory
from tsi_sim.epoch import _canonical_producer_split
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
BETAS = [0.2, 0.3, 0.4]
KS = [1, 2, 3, 4]

# Full scan / no prune: the selfish path forces both anyway (a private chain's release reorders
# the fork-choice frontier), stated here so the geometry is explicit rather than implied.
BASE = dict(n_nodes=600, stake_dist="pareto", topology="blend", degree=6,
            link_latency_mean=0.5, link_latency_dist="geo", blend_hops=3, blend_delay_max=8.0,
            max_uncles=2, uncle_strategy="oldest", window_absorption=10.0,
            k=256, epochs=10, genesis_d_factor=0.5, early_stop=False,
            adversary_strategy="selfish", prune_arrival=False, windowed_fork_choice=False)


def _accuracy(beta: float, K: int, rep: int) -> dict:
    """What K rivals at a fixed total stake do to the estimator."""
    cfg = SimConfig(**BASE, adversary_frac=beta, adversary_coalitions=K, replicate=rep)
    t = pd.DataFrame(run_trajectory(cfg))
    t = t[t.epoch >= t.epoch.max() // 2]
    adv, hon = t.adv_blocks.sum(), t.honest_blocks.sum()
    return dict(beta=beta, K=K, rep=rep, mean_ratio=float(t.mean_ratio.mean()),
                fork_rate=float(t.fork_rate.mean()), p_ref=float(t.p_ref.mean()),
                mean_orphan_rate=float(t.mean_orphan_rate.mean()),
                joint_share=float(adv / (adv + hon)) if adv + hon else 0.0)


def _profit(beta: float, K: int, rep: int, ratio: float) -> list[dict]:
    """Each coalition's canonical share against its own stake, on one rebuilt epoch.

    ``ratio`` is the accuracy arm's measured ``D-hat/D`` for this cell, and it matters: the
    lottery is driven by the estimate, so rebuilding at the GENESIS d_est would produce blocks at
    roughly twice the equilibrium rate and measure profitability in a regime the chain never
    occupies. Seeding at ``ratio * D_true`` puts the rebuild at the operating point the
    trajectory actually converges to under this attack.
    """
    cfg = SimConfig(**{**BASE, "epochs": 2}, adversary_frac=beta,
                    adversary_coalitions=K, replicate=rep)
    kids = seedseq_for(cfg).spawn(cfg.epochs + 3)
    stake = stake_for(cfg)
    mask = _adversary_mask(cfg, stake)
    ids = _coalition_ids(cfg, stake, mask)
    pl = topology.build_path_latency(cfg, np.random.default_rng(kids[1]))
    d = np.full(cfg.n_nodes, max(ratio, 0.05) * float(stake.sum()))
    ws, wn = lottery.sample_wins(lottery.win_probs(stake, d, cfg.f), cfg.epoch_len,
                                 np.random.default_rng(kids[3]))
    slots, groups = lottery.group_by_slot(ws, wn)
    tree, A = build_tree_pernode(slots, groups, pl, cfg, np.random.default_rng(kids[4]),
                                 adversary_mask=mask, coalition_ids=ids)
    total = float(stake.sum())
    # Blocks that reached nobody: private chains still hidden when the epoch ended. The lead cap
    # should keep this near zero — a large value means `wait` stopped terminating and the arm is
    # measuring the epoch boundary rather than the attack, so it is reported, not assumed away.
    adv_blk = np.array([bool(mask[int(tree.leader[b])]) for b in range(1, tree.n_blocks)])
    never = (A[:, 1:] > cfg.epoch_len).all(axis=0)
    stranded = float((adv_blk & never).sum() / max(int(adv_blk.sum()), 1))
    # K == 1 has no id vector (the single-coalition path is left untouched), so synthesise one.
    groups_of = [mask] if ids is None else [ids == g for g in range(K)]
    out = []
    for g, gmask in enumerate(groups_of):
        won, hon = _canonical_producer_split(tree, A, gmask, cfg.period_T, cfg.epoch_len)
        out.append(dict(beta=beta, K=K, rep=rep, coalition=g, stranded=stranded,
                        stake_share=float(stake[gmask].sum() / total),
                        canonical_share=float(won / (won + hon)) if won + hon else 0.0))
    return out


def sweep() -> tuple[pd.DataFrame, pd.DataFrame]:
    jobs = [(b, k, r) for b in BETAS for k in KS for r in range(REPS)]
    par = Parallel(n_jobs=N_JOBS, backend="loky", inner_max_num_threads=1)
    acc = pd.DataFrame(par(delayed(_accuracy)(*j) for j in jobs))
    # the profit arm rebuilds at each cell's MEASURED operating point, so accuracy runs first
    at = {(r.beta, r.K, r.rep): r.mean_ratio for r in acc.itertuples()}
    spl = pd.DataFrame([r for rows in par(delayed(_profit)(b, k, rp, at[(b, k, rp)])
                                          for b, k, rp in jobs) for r in rows])
    acc.to_parquet(RUNS / "multi_coalition.parquet", index=False)
    spl.to_parquet(RUNS / "multi_coalition_split.parquet", index=False)
    return acc, spl


def report(acc: pd.DataFrame, spl: pd.DataFrame) -> None:
    print("\n=== (a) does splitting the SAME stake deflate D-hat further? ===")
    # MEDIAN, not mean: the deflation feedback of §6.2 is bistable, so a cell that drops a
    # replicate onto the collapsed branch has a bimodal sample and its mean sits between two
    # branches, describing neither. `low` counts those replicates so the tail stays visible.
    print(f"{'beta':>6} {'K':>3} | {'median D_hat/D':>15} {'IQR':>15} {'low':>4} "
          f"{'fork':>6} {'p_ref':>7} {'joint sh':>9}")
    for b in BETAS:
        for k in KS:
            g = acc[(acc.beta == b) & (acc.K == k)]
            med = g.mean_ratio.median()
            lo, hi = g.mean_ratio.quantile(0.25), g.mean_ratio.quantile(0.75)
            n_low = int((g.mean_ratio < med - 0.15).sum())
            print(f"{b:6.2f} {k:3d} | {med:15.4f} {f'[{lo:.3f}, {hi:.3f}]':>15} {n_low:4d} "
                  f"{g.fork_rate.median():6.3f} {g.p_ref.median():7.3f} "
                  f"{g.joint_share.median():9.4f}")
        one = acc[(acc.beta == b) & (acc.K == 1)].mean_ratio.median()
        by_k = acc[acc.beta == b].groupby("K").mean_ratio.median()
        worst, got = by_k.idxmin(), by_k.min()
        verdict = ("SPLITTING DEFLATES FURTHER" if got < one - 0.005
                   else "the single coalition bounds it")
        print(f"       -> worst K = {worst} at {got:.4f} vs K=1 {one:.4f}: {verdict}\n")

    print("=== (b) are individually sub-threshold coalitions each profitable? ===")
    print(f"{'beta':>6} {'K':>3} | {'own stake':>10} {'canonical':>10} {'ratio':>8} "
          f"{'stranded':>9}  verdict")
    for b in BETAS:
        for k in KS:
            g = spl[(spl.beta == b) & (spl.K == k)]
            st, cs = g.stake_share.median(), g.canonical_share.median()
            strand = g.stranded.median()
            sub = "sub-1/3" if st < 1 / 3 else "over-1/3"
            pays = "PAYS" if cs > st * 1.005 else "does not pay"
            # A stranded fraction above ~0.2 means private chains were still hidden at the epoch
            # boundary, so the cell measures the boundary and not the attack — flag, do not hide.
            flag = "  <-- BOUNDARY-DOMINATED" if strand > 0.2 else ""
            print(f"{b:6.2f} {k:3d} | {st:10.4f} {cs:10.4f} {cs / st:8.3f} {strand:9.3f}  "
                  f"{sub}, {pays}{flag}")
        print()


def fig39(acc: pd.DataFrame, spl: pd.DataFrame) -> None:
    import matplotlib.pyplot as plt
    style.apply_style()
    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8))

    ax = axes[0]
    for i, b in enumerate(BETAS):
        g = (acc[acc.beta == b].groupby("K").mean_ratio.agg(["mean", "sem"]).reset_index())
        ax.errorbar(g.K, g["mean"], yerr=g["sem"], marker="o", ms=4, capsize=2,
                    color=style.OKABE_ITO[i + 1], label=rf"$\beta$ = {b:.1f}")
    ax.axhline(1.0, color="0.5", lw=0.9, ls="--")
    ax.set_xticks(KS)
    ax.set_xlabel("number of rival coalitions $K$ (total stake held fixed)")
    ax.set_ylabel(r"$\hat D / D^*$")
    ax.set_title("Accuracy vs how the same stake is split")
    ax.legend(fontsize=7)

    ax = axes[1]
    for i, b in enumerate(BETAS):
        g = spl[spl.beta == b].groupby("K")[["stake_share", "canonical_share"]].mean()
        ax.plot(g.index, g.canonical_share / g.stake_share, marker="o", ms=4,
                color=style.OKABE_ITO[i + 1], label=rf"$\beta$ = {b:.1f}")
    ax.axhline(1.0, color="0.5", lw=0.9, ls="--")
    ax.set_xticks(KS)
    ax.set_xlabel("number of rival coalitions $K$")
    ax.set_ylabel("canonical share / own stake\n(per coalition; > 1 = selfish mining pays)")
    ax.set_title("Profitability of each rival")
    ax.legend(fontsize=7)

    style.save(fig, FIGS / "fig39_multi_coalition", provenance="scripts/multi_coalition.py")
    plt.close(fig)


def main() -> None:
    print("=== K rival selfish coalitions at fixed total stake (§6.9) ===")
    acc, spl = sweep()
    report(acc, spl)
    fig39(acc, spl)
    print(f"wrote {RUNS}/multi_coalition{{,_split}}.parquet + fig39")


if __name__ == "__main__":
    main()
