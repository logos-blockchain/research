"""Accuracy of the drafted selection rule against a selfish (SM1) coalition, by reference window.

Usage: window_summary.py <results/coalition-fork-point.parquet> <results/coalition-own-slot.parquet>
                         <results/coalition-today.parquet> [<results/coalition-w240.parquet>]
The W = 240 sweep repeats W = 144. Its W = 144 arm must equal the first sweep's, and only its W = 240 arm is added.
Replicates whose realised coalition share misses its label by more than 0.01 are dropped from every arm.
"""
import sys, numpy as np, pandas as pd
from tsi_sim.config import SimConfig
from tsi_sim.engine import _adversary_mask
from tsi_sim.plotting.figures_pernode import CONFIG_COLS, equilibrium, rho_for, sem
from tsi_sim.stake import stake_for
import dataclasses
F = {f.name for f in dataclasses.fields(SimConfig)}
KEYS = ["blend_delay_max", "adversary_frac", "replicate"]
dfs = []
for i, (p, tag) in enumerate(zip(sys.argv[1:], ("fork point", "own slot", "today", "fork point"))):
    d = pd.read_parquet(p); default = SimConfig()
    for c in CONFIG_COLS:
        if c not in d.columns: d[c] = getattr(default, c)
    d["arm"] = tag + (" W=" + d.window_absorption.astype(int).astype(str) if tag != "today" else " (first block of a fork, W=12)")
    if i == 3:
        rows = lambda x: x[x.window_absorption == 144.0].sort_values(KEYS + ["epoch"]).mean_ratio.to_numpy()
        print("W = 144 arm of the W = 240 sweep equals the first sweep's:", np.array_equal(rows(d), rows(dfs[0])))
        d = d[d.window_absorption != 144.0]
    dfs.append(d)
df = pd.concat(dfs, ignore_index=True)
assert df.paired_streams.all()
bad = set()
for _, r in df[df.epoch == 0].drop_duplicates(KEYS).iterrows():
    cfg = SimConfig(**{c: r[c].item() if hasattr(r[c], "item") else r[c] for c in r.index if c in F})
    st = stake_for(cfg); m = _adversary_mask(cfg, st); a = float(st[m].sum() / st.sum()) if m is not None else 0.0
    if abs(a - r.adversary_frac) > 0.01: bad.add(tuple(r[k] for k in KEYS))
print("dropped replicates (delay, share, replicate):", sorted(bad))
eqs = []
for a, d in df.groupby("arm"):
    e = equilibrium(d); e["arm"] = a; eqs.append(e)
eq = pd.concat(eqs, ignore_index=True)
eq = eq[[tuple(r) not in bad for r in eq[KEYS].to_numpy().tolist()]]
delays = sorted(eq.blend_delay_max.unique()); rho = dict(zip(delays, rho_for(df, delays)))
order = ["today (first block of a fork, W=12)"] + [f"fork point W={w}" for w in (12, 24, 48, 96, 144, 240)] + [f"own slot W={w}" for w in (12, 24)]
for dl in delays:
    for al in sorted(eq.adversary_frac.unique()):
        c = eq[(eq.blend_delay_max == dl) & (eq.adversary_frac == al)]
        ref = c[c.arm == "fork point W=12"].set_index("replicate").mean_ratio
        print(f"\nrho {rho[dl]:.2f} without a coalition, coalition {al} of the total active stake")
        for a in order:
            x = c[c.arm == a].set_index("replicate")
            if x.empty: continue
            g = (x.mean_ratio - ref.loc[x.index]).to_numpy()
            print(f"  {a:38s} D^/D {x.mean_ratio.mean():.4f}  gap to W=12 {100*g.mean():+5.2f} ± {100*sem(g):.2f} pp  uncounted honest slots, % of occupied: depth 1 {100*x.lost_honest_d1_share.mean():.2f}, 2 {100*x.lost_honest_d2_share.mean():.2f}, >=3 {100*x.lost_honest_d3plus_share.mean():.2f}; coalition share of the chain {x.adv_block_share.mean():.3f}; n={len(x)}")
