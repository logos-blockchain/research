"""SLOTS.md K.7's tables, read from runs/k7 (scripts/k7_wait.py); tables.py dispatches k7* here.

    python scripts/tables.py k7worst | k7ratio | k7slots | k7checks | k7played | k7holds | k7compare |
                             k7waits | k7absorbs | k7rate | k7blend | k7floor
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd

from tables import md
from tables_k1 import CASES, _eps, _held, _pivot, _share
from tables_k3 import p10, share

RUNS = pathlib.Path(__file__).resolve().parent.parent / "runs"
WORST = ("worst, 1 s", "worst, 10 s", "worst, 20 s")


def _h(v: float) -> str:
    return "past the curve" if not math.isfinite(v) or v < 0 else f"{v:.1f}"


def _worst() -> pd.DataFrame:
    """K.7's waits with K.1's lower depth at each ε, which marks an attack read at its first
    computed depth."""
    w = pd.read_csv(RUNS / "k7" / "worst.csv").rename(columns={"delta_s": "delay_s"})
    w["key"] = w.alpha.round(4)
    k1 = pd.read_csv(RUNS / "k1" / "worst.csv")
    k1["key"] = k1.alpha.round(4)
    for eps in (1e-6, 1e-9):
        k = k1[np.isclose(k1.eps, eps)][["key", "delay_s", "lb_depth"]]
        w = w.merge(k.rename(columns={"lb_depth": f"lb_depth_{eps:g}"}), on=["key", "delay_s"])
    return w


def k7worst() -> None:
    w = _worst()
    for eps in (1e-6, 1e-9):
        e = f"{eps:g}"
        print(f"ε = {_eps(eps)}, hours\n")
        print(md(_pivot(w, lambda r: f"{'≤ ' if r[f'lb_depth_{e}'] <= 20 else ''}{r[f'attack_h_{e}']:.1f}"
                                     f"{'*' if r[f'attack_extrapolated_{e}'] else ''} – {r[f'wait_h_{e}']:.1f}")))
        print()


def k7ratio() -> None:
    w = _worst()
    print(md(_pivot(w, lambda r: f"{r['k1_over_k7_1e-09']:.2f}")))


def k7slots() -> None:
    w = _worst()
    print(md(_pivot(w, lambda r: f"{r['slots_over_cont_1e-09']:.3f}")))


def k7checks() -> None:
    c = pd.read_csv(RUNS / "k7" / "checks.csv")
    print(md(pd.DataFrame({
        "α": c.alpha.map(_share), "Δ": c.delta_s.map(lambda v: f"{v} s"), "variant": c.kind,
        "wait at 1e-6 (h)": c["wait_h_1e-06"].map(lambda v: f"{v:.2f}"),
        "wait at 1e-9 (h)": c["wait_h_1e-09"].map(lambda v: f"{v:.2f}")})))


def k7played() -> None:
    p = pd.read_csv(RUNS / "k7" / "played.csv")

    def pm(v, se):
        return "0" if v == 0 else f"{v:.2e} ± {se:.1e}"
    print(md(pd.DataFrame({
        "α": p.alpha.map(_share), "Δ": p.delta_s.map(lambda v: f"{v} s"),
        "wait (h)": p.wait.map(lambda v: f"{v / 3600:.2f}"),
        "continuous reading": p.continuous.map(lambda v: f"{v:.2e}"),
        "its chain, true lengths": [pm(v, s) for v, s in zip(p.chain, p.chain_se)],
        "reading over its chain": [f"{b / v:.2f}" if v > 0 else "–" for b, v in zip(p.continuous, p.chain)],
        "bound on slots": p.bound.map(lambda v: f"{v:.2e}"),
        "the paper's attack on slots": [pm(v, s) for v, s in zip(p.attack, p.attack_se)]})))


def k7holds() -> None:
    h = pd.read_csv(RUNS / "k7" / "holds.csv")
    ks = sorted(h.k.unique(), reverse=True)
    for reading in ("⌊k/f⌋", "3⌊k/f⌋"):
        t = h[h.reading == reading]
        rows = []
        for m in WORST:
            for case, name in CASES.items():
                c = t[(t.model == m) & (t.case == case)]
                if c.empty:
                    continue
                c = c.set_index("k")
                rows.append({"model": m, "case": name,
                             **{f"k = {k}": _held(float(c.loc[k].held), 1 / 3) for k in ks}})
        print(f"K = {reading}\n")
        print(md(pd.DataFrame(rows)))
        print()


def k7compare() -> None:
    """At 10 s, without grinding and with two ground nonces: K.1's bound and K.7's."""
    h1 = pd.read_csv(RUNS / "k2" / "holds.csv")
    h7 = pd.read_csv(RUNS / "k7" / "holds.csv")
    rows = []
    for k in sorted(h7.k.unique(), reverse=True):
        def cell(h, reading, top):
            out = []
            for case in ("without", "two"):
                c = h[(h.model == "worst, 10 s") & (h.k == k) & (h.reading == reading) & (h.case == case)]
                out.append(_held(float(c.held.iloc[0]), top))
            return " / ".join(out)
        rows.append({"k": k, "K = ⌊k/f⌋: K.1's bound": cell(h1, "⌊k/f⌋", 1 / 3),
                     "K = ⌊k/f⌋: K.7's bound": cell(h7, "⌊k/f⌋", 1 / 3),
                     "K = 3⌊k/f⌋: K.1's bound": cell(h1, "3⌊k/f⌋", 1 / 3),
                     "K = 3⌊k/f⌋: K.7's bound": cell(h7, "3⌊k/f⌋", 1 / 3)})
    print(md(pd.DataFrame(rows)))


def k7waits() -> None:
    w = pd.read_csv(RUNS / "k7" / "waits.csv")
    rows = []
    for (m, case), g in w.groupby(["model", "case"], sort=False):
        g = g.set_index(g.alpha.round(4))
        a, b = g.loc[0.3], g.loc[0.3333]

        def hold(r, col):
            return "yes" if bool(r[col]) else "no"
        rows.append({"model": m, "case": {"without": "no grinding"}.get(case, case),
                     "30 %: wait (h), K.1's bound in brackets": f"{_h(a.wait_h)} ({_h(a.k1_wait_h)})",
                     "a third: wait (h), K.1's bound in brackets": f"{_h(b.wait_h)} ({_h(b.k1_wait_h)})",
                     "K = 64,800 (18 h): 30 % / a third": f"{hold(a, 'holds_64800')} / {hold(b, 'holds_64800')}",
                     "K = 194,400 (54 h): 30 % / a third": f"{hold(a, 'holds_194400')} / {hold(b, 'holds_194400')}"})
    print(md(pd.DataFrame(rows)))


def k7absorbs() -> None:
    a = pd.read_csv(RUNS / "k7" / "absorbs.csv")

    def chance(v, below):
        return "< 1e-55" if below else f"{v:.1e}"

    def fac(v, below):
        return "> 1e46" if below else (f"{v:.2g}" if v >= 1 else "none")
    print(md(pd.DataFrame({
        "α": a.alpha.map(_share), "K": a.K.map(lambda v: f"{int(v):,}"),
        "chance after K slots": [chance(v, b) for v, b in zip(a.chance, a.below_1e55)],
        "largest factor absorbed": [fac(v, b) for v, b in zip(a.absorbs, a.below_1e55)],
        "after a deflated inference: chance / factor":
            [f"{chance(v, b)} / {fac(x, b)}" for v, x, b in zip(a.chance_deflated, a.absorbs_deflated,
                                                               a.below_1e55_deflated)]})))


def k7rate() -> None:
    r = pd.read_csv(RUNS / "k7" / "rate.csv")
    rows = []
    for i in sorted(r.interval.unique(), reverse=True):
        g = r[r.interval == i]
        rows.append({"block interval": f"{i} s",
                     **{f"{_share(a)}: K.7 / K.1 (h)": f"{x:.1f} / {y:.1f}"
                        for a, x, y in zip(g.alpha, g.wait_h, g.k1_wait_h)}})
    print(md(pd.DataFrame(rows)))


def k7blend() -> None:
    b = pd.read_csv(RUNS / "k7" / "blend.csv")
    rows = []
    for (hops, rounds), g in b.groupby(["hops", "rounds"], sort=False):
        lo, hi = g[g.alpha < 0.31].iloc[0], g[g.alpha > 0.31].iloc[0]
        rows.append({"hops": hops, "rounds": rounds, "Δ": f"{int(lo.delta_s)} s",
                     "0.30: random delay / worst, K.7 (K.1) (h)":
                         f"{lo.random_wait_h:.1f} / {lo.k7_wait_h:.1f} ({lo.worst_wait_h:.1f})",
                     "a third: random delay / worst, K.7 (K.1) (h)":
                         f"{hi.random_wait_h:.1f} / {hi.k7_wait_h:.1f} ({hi.worst_wait_h:.1f})"})
    print(md(pd.DataFrame(rows)))


def k7floor() -> None:
    t = pd.read_csv(RUNS / "k7" / "floor.csv")
    print(md(pd.DataFrame({
        "K": [f"{w}, {hh:.1f} h" for w, hh in zip(t.window, t.hours)],
        "α_max": t.alpha.map(share), "delay": t.model,
        "floor φ": t.phi.map(lambda v: f"{v:,}"),
        "withheld-from chain, mean": t.expected.map(lambda v: f"{v:,.0f}"),
        "nobody withholds: waits": t.log10_wait_full.map(p10),
        "withheld from: waits": t.log10_wait_attacked.map(p10),
        "largest side held at K": t.provisional_share.map(lambda v: f"{v:.3f}"),
        "its honest part, the coalition signing": t.provisional_honest.map(lambda v: f"{v:.3f}")})))
