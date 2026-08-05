"""Regenerate every number the report quotes, with its across-topology standard error.

Run from this directory:  python report_numbers.py
Each printed value is mean +- SEM over the independent topology seeds, computed from the
parquets checked in beside this script (see README.md for what each run is).
"""
import os
import sys

import numpy as np
import pandas as pd

_here = os.path.dirname(os.path.abspath(__file__))
D = sys.argv[1] if len(sys.argv) > 1 else os.path.join(_here, "default")
R = sys.argv[2] if len(sys.argv) > 2 else os.path.join(_here, "redundancy")
PC = sys.argv[3] if len(sys.argv) > 3 else os.path.join(_here, "percolation")
P = pd.read_parquet(D + "/propagation.parquet")
A = pd.read_parquet(D + "/adversary.parquet")
Z = pd.read_parquet(D + "/deanon.parquet")
PR = pd.read_parquet(R + "/propagation.parquet")
ZR = pd.read_parquet(R + "/deanon.parquet")
PP = pd.read_parquet(PC + "/propagation.parquet")


def sem(s):
    return s.std(ddof=1) / np.sqrt(s.count()) if s.count() > 1 else np.nan


def cell(df, col):
    return df[col].mean(), sem(df[col])


print(f"rounds/cell: default {P.n_rounds.iloc[0]}x{P.graph_seed.nunique()}"
      f" | redundancy {PR.n_rounds.iloc[0]}x{PR.graph_seed.nunique()}"
      f" | percolation {PP.n_rounds.iloc[0]}x{PP.graph_seed.nunique()}")

print("\n### 3.1 full delay (s), N=1e5 mbd=3 u=0 : mean+-SEM")
b = P[(P.n_nodes == 100000) & (P.max_blend_delay == 3) & (P.unresponsive_frac == 0.0)]
for bh in sorted(b.blend_hops.unique()):
    out = []
    for d in sorted(b.degree.unique()):
        m, e = cell(b[(b.blend_hops == bh) & (b.degree == d)], "full_delay_ms_mean")
        out.append(f"d{d}:{m/1000:.2f}+-{e/1000:.3f}")
    print(f" bh={bh}  " + " ".join(out))
print(" per-hop cost (s) by degree:")
for d in sorted(b.degree.unique()):
    g = b[b.degree == d].groupby("blend_hops").full_delay_ms_mean.mean() / 1000
    print(f"   d={d:<3} 1->2 {g[2]-g[1]:.2f}  2->3 {g[3]-g[2]:.2f}  3->5 {(g[5]-g[3])/2:.2f}")

print("\n### 3.2 composition N=1e5 deg8 bh3 ; and N-scaling")
g = b[(b.degree == 8) & (b.blend_hops == 3)]
for c in ("path_delay_ms_mean", "broadcast_delay_ms_mean", "full_delay_ms_mean",
          "cover50_ms", "cover90_ms", "cover99_ms"):
    m, e = cell(g, c)
    print(f"   {c:<24} {m:8.0f} +- {e:.0f} ms")
for n in sorted(P.n_nodes.unique()):
    m, e = cell(P[(P.n_nodes == n) & (P.degree == 8) & (P.blend_hops == 3)
                  & (P.max_blend_delay == 3) & (P.unresponsive_frac == 0)], "full_delay_ms_mean")
    print(f"   N={n:<8} full {m/1000:.2f}+-{e/1000:.3f} s")
print("   cover99 by degree (N=1e5,bh3):",
      {int(d): round(b[(b.degree == d) & (b.blend_hops == 3)].cover99_ms.mean())
       for d in sorted(b.degree.unique())})

print("\n### 3.3 observed / eclipsed (exact) N=1e5 random")
ab = A[(A.n_nodes == 100000) & (A.adversary_mode == "random")]
print(ab.groupby(["f_adv", "degree"]).observed_frac.mean().unstack().round(3).to_string())
print(ab.groupby(["f_adv", "degree"]).eclipsed_frac.mean().unstack().round(4).to_string())
print(" random vs worstcase_coverage observed, AT DEGREE 8 (not averaged over degrees):")
wc = A[(A.n_nodes == 100000) & (A.degree == 8)
       & A.adversary_mode.isin(["random", "worstcase_coverage"])]
print(wc.groupby(["f_adv", "adversary_mode"]).observed_frac.mean().unstack().round(3).to_string())
print(" ...and eclipse random vs worstcase_eclipse at degree 4:")
we = A[(A.n_nodes == 100000) & (A.degree == 4)
       & A.adversary_mode.isin(["random", "worstcase_eclipse"])]
print(we.groupby(["f_adv", "adversary_mode"]).eclipsed_frac.mean().unstack().round(4).to_string())

print("\n### 3.4 deanon (exact) N=1e5 random deg8 : deanon_rate by f_adv x hops")
zz = Z[(Z.n_nodes == 100000) & (Z.adversary_mode == "random") & (Z.degree == 8)]
print(zz.groupby(["f_adv", "blend_hops"]).deanon_rate.mean().unstack().round(5).to_string())
print(" full_deanon vs degree (bh=2):")
print(Z[(Z.n_nodes == 100000) & (Z.adversary_mode == "random") & (Z.blend_hops == 2)]
      .groupby(["f_adv", "degree"]).full_deanon_rate.mean().unstack().round(4).to_string())

print("\n### 3.5 delivery (N=1e5 deg8 mbd3): mean+-SEM   [theory (1-u)^bh]")
dv = P[(P.n_nodes == 100000) & (P.degree == 8) & (P.max_blend_delay == 3)]
for bh in sorted(dv.blend_hops.unique()):
    out = []
    for u in sorted(dv.unresponsive_frac.unique()):
        if u == 0:
            continue
        m, e = cell(dv[(dv.blend_hops == bh) & (dv.unresponsive_frac == u)], "delivery_rate")
        out.append(f"u{u}:{m:.3f}+-{e:.3f}[{(1-u)**bh:.3f}]")
    print(f" bh={bh}  " + " ".join(out))
print("\n### 3.5 coverage (N=1e5 bh1 mbd3): mean+-SEM")
cc = P[(P.n_nodes == 100000) & (P.blend_hops == 1) & (P.max_blend_delay == 3)]
for d in sorted(cc.degree.unique()):
    out = []
    for u in (0.2, 0.3, 0.5):
        m, e = cell(cc[(cc.degree == d) & (cc.unresponsive_frac == u)], "frac_reached")
        out.append(f"u{u}:{m:.4f}+-{e:.4f}")
    print(f" deg={d:<3} " + " ".join(out))

print("\n### 3.5 PERCOLATION run: coverage vs u (N=1e5, bh=1); u_c = 1-1/(d-1)")
for d in sorted(PP.degree.unique()):
    uc = 1 - 1 / (d - 1)
    g = PP[PP.degree == d].groupby("unresponsive_frac").frac_reached.mean()
    print(f" deg={d:<3} u_c={uc:.2f}  " + " ".join(f"{u:.1f}:{v:.3f}" for u, v in g.items()))

print("\n### 3.8 REDUNDANCY: delivery vs R (N=20k deg8 bh3): mean+-SEM  [1-(1-p1)^R]")
pr = PR[(PR.degree == 8) & (PR.blend_hops == 3)]
for u in sorted(pr.unresponsive_frac.unique()):
    if u == 0:
        continue
    p1 = pr[(pr.unresponsive_frac == u) & (pr.redundancy == 1)].delivery_rate.mean()
    out, vals = [], []
    for Rn in (1, 2, 3, 4):
        m, e = cell(pr[(pr.unresponsive_frac == u) & (pr.redundancy == Rn)], "delivery_rate")
        vals.append(m)
        out.append(f"R{Rn}:{m:.3f}+-{e:.3f}[{1-(1-p1)**Rn:.3f}]")
    mono = all(y >= x - 1e-9 for x, y in zip(vals, vals[1:]))
    print(f" u={u}  " + " ".join(out) + ("" if mono else "   <<< NON-MONOTONIC"))
print(" coverage vs R (should be flat -- no union bonus):")
for d in sorted(PR.degree.unique()):
    for u in (0.3, 0.5):
        g = PR[(PR.degree == d) & (PR.blend_hops == 1) & (PR.unresponsive_frac == u)]
        print(f"   deg={d} u={u}: " +
              " ".join(f"R{Rn}:{g[g.redundancy==Rn].frac_reached.mean():.4f}" for Rn in (1, 2, 3, 4)))
print(" deanon vs R (exact, N=20k deg8 bh3 f=0.2 random):")
zr = ZR[(ZR.degree == 8) & (ZR.blend_hops == 3) & (ZR.f_adv == 0.2)
        & (ZR.adversary_mode == "random")]
print(zr.groupby("redundancy")[["deanon_rate", "full_deanon_rate"]].mean().round(4).to_string())
