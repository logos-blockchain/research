"""Phase A1: the baseline over the delay axis (PLAN.md A1, Q3).

    python scripts/a1_baseline.py            # writes runs/a1/{runs.parquet,summary.csv}

Every point: N = 1000 nodes, peering degree 6, Pareto stake, f = 1/30, one epoch of
10*floor(k/f) slots at k = 256, 8 replicates. Two families:

- calibration: the TSI report's points (3 hops, continuous mixing delay U(0, delta), 0.5 s geo
  links), where its engine measured o = 0.20, 0.35, 0.60 at delta = 2, 8, 32 s (§6.10, §7);
- node-aligned: whole-round mixing delays uniform on [1, Delta_max] (the node's release
  delayer), Delta_max from 1 to 12, at 1 and 3 hops and 0.1 s and 0.5 s mean geo links.

    python scripts/a1_baseline.py release    # writes runs/a1/release.csv (about 3 minutes on 4 cores)

The release round: the engine starts a block's cascade at its slot, the Blend specification
releases every generated message at the next round (tsi_sim, blend_release_next_round). At either
release: the specification's row (3 hops, 3 rounds, 0.1 s links), 32 runs, and the depth at 1e-9
of B5's closed form at its growth, the report's convention, beside A1's own eight runs of the row
and 24 more on its seeds; and B3's withholding coalition on the
same Blend with honest relays, one copy and two, 64 runs a cell, the depth at the growth per
honest win it leaves, as G6 reads it. Both releases of a run draw the same stake, graph, lottery
and mixing delays (paired_streams), so the change in growth is measured run by run.
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from tsi_sim.config import SimConfig

from b3_race import BASE as B3_BASE
from finality_sim.baseline import DEPTHS, run
from finality_sim.private_race import strict_depth
from finality_sim.race import withhold_tree

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "a1"
REPLICATES = 8
BASE = dict(n_nodes=1000, stake_dist="pareto", topology="blend", degree=6,
            link_latency_dist="geo", k=256, epochs=1, f=1 / 30, max_uncles=0,
            prune_arrival=False)


def grid() -> list[dict]:
    pts = []
    for delta in (2.0, 8.0, 32.0):
        pts.append(dict(family="calibration", blend_hops=3, blend_delay_max=delta,
                        blend_delay_dist="continuous", link_latency_mean=0.5))
    for link in (0.1, 0.5):
        for hops in (1, 3):
            for dmax in (1, 2, 3, 5, 8, 12):
                pts.append(dict(family="rounds", blend_hops=hops, blend_delay_max=float(dmax),
                                blend_delay_dist="rounds", link_latency_mean=link))
    return pts


def one(point: dict, rep: int) -> dict:
    kw = {k: v for k, v in point.items() if k != "family"}
    cfg = SimConfig(**BASE, **kw, replicate=rep)
    m = run(cfg)
    row = dict(point, replicate=rep, orphan_share=m.orphan_share,
               occupied_per_f=m.occupied_rate / cfg.f, growth_per_f=m.growth_rate / cfg.f,
               blocks=m.n_blocks, vis_mean=float(np.mean(m.vis_mean)),
               vis_full_mean=float(np.mean(m.vis_full)),
               vis_full_p99=float(np.percentile(m.vis_full, 99)),
               vis_full_max=float(np.max(m.vis_full)))
    for d in DEPTHS:
        row[f"chain_{d}"] = m.depth_chain[d].tolist()
        row[f"seen_{d}"] = m.depth_seen[d].tolist()
    return row


def summarise(df: pd.DataFrame) -> pd.DataFrame:
    keys = ["family", "blend_hops", "blend_delay_dist", "blend_delay_max", "link_latency_mean"]
    out = []
    for key, g in df.groupby(keys, sort=False):
        r = dict(zip(keys, key))
        n = len(g)
        for col in ("orphan_share", "occupied_per_f", "growth_per_f", "vis_mean",
                    "vis_full_mean", "vis_full_p99", "vis_full_max"):
            r[col] = g[col].mean()
            if col in ("orphan_share", "vis_mean"):
                r[col + "_sem"] = g[col].std(ddof=1) / np.sqrt(n)
        for d in DEPTHS:
            chain = np.concatenate([np.asarray(x) for x in g[f"chain_{d}"]])
            seen = np.concatenate([np.asarray(x) for x in g[f"seen_{d}"]])
            r[f"chain_{d}_p50_s"] = np.percentile(chain, 50)
            r[f"seen_{d}_p95_s"] = np.percentile(seen, 95)
        out.append(r)
    return pd.DataFrame(out)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    pts = grid()
    jobs = [(p, r) for p in pts for r in range(REPLICATES)]
    rows = Parallel(n_jobs=-2, backend="loky")(delayed(one)(p, r) for p, r in jobs)
    df = pd.DataFrame(rows)
    df.to_parquet(OUT / "runs.parquet")
    s = summarise(df)
    s.to_csv(OUT / "summary.csv", index=False)
    with pd.option_context("display.width", 250, "display.max_columns", 40):
        print(s.round(3).to_string(index=False))


SPEC = dict(blend_hops=3, blend_delay_max=3.0, blend_delay_dist="rounds", link_latency_mean=0.1)
SHARES = (0.25, 0.30, 1 / 3)


def _a1_spec(next_round: bool, rep: int, paired: bool = True) -> dict:
    m = run(SimConfig(**BASE, **SPEC, blend_release_next_round=next_round, paired_streams=paired, replicate=rep))
    return dict(next_round=next_round, replicate=rep, orphan=m.orphan_share, growth=m.growth_rate / BASE["f"])


def _withheld(next_round: bool, copies: int, alpha: float, rep: int) -> dict:
    cfg = SimConfig(**B3_BASE, **SPEC, adversary_frac=alpha, blend_copies=copies,
                    blend_release_next_round=next_round, paired_streams=True, replicate=rep)
    tree, _, _, public, canonical = withhold_tree(cfg)
    win = (1 - alpha) * -np.log(1 - B3_BASE["f"])                  # honest wins per slot
    return dict(next_round=next_round, copies=copies, alpha=round(alpha, 4), replicate=rep,
                orphan=1.0 - canonical[public].sum() / public.sum(),
                growth=canonical.sum() / cfg.epoch_len / win)


def _pair(g: pd.DataFrame) -> list[dict]:
    """Both releases of one cell, and the paired change in growth: both releases of a replicate
    draw the same stake, graph, lottery and mixing delays (paired_streams)."""
    at = g[~g.next_round.astype(bool)].set_index("replicate").sort_index()
    nx = g[g.next_round.astype(bool)].set_index("replicate").sort_index()
    diff = nx.growth - at.growth
    return [dict(next_round=nr, runs=len(x), orphan=float(x.orphan.mean()),
                 orphan_sem=float(x.orphan.std(ddof=1) / np.sqrt(len(x))), growth=float(x.growth.mean()),
                 growth_sem=float(x.growth.std(ddof=1) / np.sqrt(len(x))), growth_change=float(diff.mean()),
                 growth_change_sem=float(diff.std(ddof=1) / np.sqrt(len(diff))))
            for nr, x in ((False, at), (True, nx))]


def release() -> None:
    a1 = pd.DataFrame(Parallel(n_jobs=4, backend="loky")(
        delayed(_a1_spec)(nr, r) for nr in (False, True) for r in range(32)))
    own = pd.DataFrame(Parallel(n_jobs=4, backend="loky")(          # A1's own seeds: its eight, and more
        delayed(_a1_spec)(False, r, paired=False) for r in range(32)))
    wh = pd.DataFrame(Parallel(n_jobs=4, backend="loky")(
        delayed(_withheld)(nr, c, a, r) for nr in (False, True) for c in (1, 2) for a in SHARES
        for r in range(64)))
    rows = []
    for n in (8, 32):
        g = own[own.replicate < n]
        for a in SHARES:
            rows.append(dict(setting=f"everyone producing, A1's seeds, {n} runs", copies=1, alpha=round(a, 4),
                             next_round=False, runs=n, orphan=float(g.orphan.mean()),
                             orphan_sem=float(g.orphan.std(ddof=1) / np.sqrt(n)), growth=float(g.growth.mean()),
                             growth_sem=float(g.growth.std(ddof=1) / np.sqrt(n)), growth_change=np.nan,
                             growth_change_sem=np.nan,
                             depth_1e9=strict_depth(a / (a + (1 - a) * float(g.growth.mean())), np.log(1e-9))))
    for x in _pair(a1):
        for a in SHARES:
            rows.append(dict(setting="everyone producing", copies=1, alpha=round(a, 4), **x,
                             depth_1e9=strict_depth(a / (a + (1 - a) * x["growth"]), np.log(1e-9))))
    for (c, a), g in wh.groupby(["copies", "alpha"], sort=False):
        for x in _pair(g):
            rows.append(dict(setting="coalition withholding", copies=c, alpha=a, **x,
                             depth_1e9=strict_depth(a / (a + (1 - a) * x["growth"]), np.log(1e-9))))
    t = pd.DataFrame(rows)
    t.to_csv(OUT / "release.csv", index=False)
    with pd.option_context("display.width", 250):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


if __name__ == "__main__":
    sys.exit(release() if sys.argv[1:] == ["release"] else main())
