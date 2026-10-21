"""Phase K.1 and K.2's tables for SLOTS.md, read straight from runs/k1 and runs/k2.

    python scripts/tables.py k1 | k1worst | k1ratio | k1played | k2 | k2waits | k2absorbs
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd

from tables import md

RUNS = pathlib.Path(__file__).resolve().parent.parent / "runs"


def _share(v: float) -> str:
    return "a third" if abs(v - 1 / 3) < 1e-9 else f"{v:.2f}"


def _eps(v: float) -> str:
    return f"{v:.0e}".replace("e-0", "e-")


def k1() -> None:
    r = pd.read_csv(RUNS / "k1" / "random.csv")
    for eps in (1e-6, 1e-9):
        t = r[np.isclose(r.eps, eps)]
        te, sp = t[t.blend == "testnet"].set_index("alpha"), t[t.blend == "specification"].set_index("alpha")
        print(f"ε = {_eps(eps)}\n")
        print(md(pd.DataFrame({
            "α": [_share(a) for a in sp.index],
            "testnet: wait (h)": [f"{te.loc[a].wait_h:.2f}" for a in sp.index],
            "testnet: depth rule, blocks / h": [f"{int(te.loc[a].depth)} / {te.loc[a].depth_report_h:.2f}"
                                                for a in sp.index],
            "specification: wait (h)": [f"{sp.loc[a].wait_h:.2f}" for a in sp.index],
            "specification: depth rule, blocks / h": [f"{int(sp.loc[a].depth)} / {sp.loc[a].depth_report_h:.2f}"
                                                      for a in sp.index],
            "specification: wait over the depth rule's time, report's / model's clock":
                [f"{sp.loc[a].ratio_report:.3f} / {sp.loc[a].ratio_model:.3f}" for a in sp.index]})))
        print()


def _pivot(w: pd.DataFrame, cell) -> pd.DataFrame:
    w = w.copy()
    w["cell"] = [cell(r) for _, r in w.iterrows()]
    p = w.pivot(index="alpha", columns="delay_s", values="cell").reset_index()
    p["alpha"] = p["alpha"].map(_share)
    p.columns = ["α"] + [f"{int(c)} s" for c in p.columns[1:]]
    return p


def k1worst() -> None:
    w = pd.read_csv(RUNS / "k1" / "worst.csv")
    for eps in (1e-6, 1e-9):
        t = w[np.isclose(w.eps, eps)]
        print(f"ε = {_eps(eps)}, hours\n")
        print(md(_pivot(t, lambda r: f"{'≤ ' if r.lb_depth <= 20 else ''}{r.lb_h_estimate:.1f}"
                                     f"{'*' if r.lb_extrapolated else ''} – {r.wait_h:.1f}")))
        print()


def k1ratio() -> None:
    w = pd.read_csv(RUNS / "k1" / "worst.csv")
    print(md(_pivot(w[np.isclose(w.eps, 1e-9)], lambda r: f"{r.ratio:.2f}")))


def k1played() -> None:
    p = pd.read_csv(RUNS / "k1" / "played.csv")
    print(md(pd.DataFrame({
        "timelines": p.timelines, "α": p.alpha.map(_share), "ε": p.eps.map(_eps),
        "wait (h)": p.wait_h.map(lambda v: f"{v:.2f}"),
        "closed form": p.closed.map(lambda v: f"{v:.1e}"),
        "race, rate ± se": [f"{r.rate:.1e} ± {r.se:.1e}" if r.successes else "0"
                            for _, r in p.iterrows()],
        "targets": p.targets.map(lambda v: f"{v:,}")})))


CASES = {"without": "no grinding", "one": "today's nonce, one ground", "two": "today's nonce, two ground",
         "nonce §3.1": "the nonce of §3.1 under its delay", "deflated": "a deflated inference"}
MODELS = ("random, testnet", "random, specification", "worst, 1 s", "worst, 10 s", "worst, 20 s")


def _held(v: float, top: float) -> str:
    if isinstance(v, float) and math.isnan(v):
        return "< 0.05"
    if math.isinf(v) or (not math.isnan(top) and v >= top - 1e-12):
        return "≥ a third" if abs(top - 1 / 3) < 1e-9 or math.isinf(v) else f"≥ {top:.2f}"
    return f"{v:.3f}"


def k2() -> None:
    h = pd.read_csv(RUNS / "k2" / "holds.csv")
    ks = sorted(h.k.unique(), reverse=True)
    for reading in ("⌊k/f⌋", "3⌊k/f⌋"):
        t = h[h.reading == reading]
        rows = []
        for m in MODELS:
            for case, name in CASES.items():
                c = t[(t.model == m) & (t.case == case)]
                if c.empty:
                    continue
                c = c.set_index("k")
                rows.append({"model": m, "case": name,
                             **{f"k = {k}": _held(float(c.loc[k].held), float(c.loc[k].top)) for k in ks}})
        print(f"K = {reading}\n")
        print(md(pd.DataFrame(rows)))
        print()


def k2compare() -> None:
    """The largest share, k in blocks (B5 and B6) against K in slots, at 1e-9."""
    b6 = pd.read_csv(RUNS / "b6" / "shares.csv")
    h = pd.read_csv(RUNS / "k2" / "holds.csv")
    for m in ("random, specification", "worst, 10 s"):
        rows = []
        top = 0.41 if m.startswith("random") else 1 / 3        # B6's grid top; B5's own share has none
        for k in sorted(h.k.unique(), reverse=True):
            b = b6[(b6.model == m) & (b6.k == k)]

            def blk(col):
                cap = math.nan if (col == "held_without" and m.startswith("random")) else top
                return "—" if b.empty else _held(float(b[col].iloc[0]), cap)

            def slots(reading, case):
                c = h[(h.model == m) & (h.k == k) & (h.reading == reading) & (h.case == case)].iloc[0]
                return _held(float(c.held), float(c.top))
            rows.append({"k": k,
                         "k blocks: no grinding / two ground nonces": f"{blk('held_without')} / {blk('held_two')}",
                         "K = ⌊k/f⌋ slots": f"{slots('⌊k/f⌋', 'without')} / {slots('⌊k/f⌋', 'two')}",
                         "K = 3⌊k/f⌋ slots": f"{slots('3⌊k/f⌋', 'without')} / {slots('3⌊k/f⌋', 'two')}"})
        print(f"{m}\n")
        print(md(pd.DataFrame(rows)))
        print()


def k2waits() -> None:
    w = pd.read_csv(RUNS / "k2" / "waits.csv")
    rows = []
    for (m, case), g in w.groupby(["model", "case"], sort=False):
        g = g.set_index(g.alpha.round(4))
        a, b = g.loc[0.3], g.loc[0.3333]

        def hours(r):
            return "past the curve" if r.wait_slots < 0 else f"{r.wait_h:.1f}"

        def hold(r, col):
            return "yes" if bool(r[col]) else "no"
        rows.append({"model": m, "case": {"without": "no grinding"}.get(case, case),
                     "30 %: wait (h)": hours(a), "a third: wait (h)": hours(b),
                     "K = 64,800 (18 h): 30 % / a third": f"{hold(a, 'holds_64800')} / {hold(b, 'holds_64800')}",
                     "K = 194,400 (54 h): 30 % / a third": f"{hold(a, 'holds_194400')} / {hold(b, 'holds_194400')}"})
    print(md(pd.DataFrame(rows)))


def k2absorbs() -> None:
    a = pd.read_csv(RUNS / "k2" / "absorbs.csv")

    def fac(v):
        return f"{v:.2g}" if v >= 1 else "none"
    print(md(pd.DataFrame({
        "α": a.alpha.map(_share), "K": a.K.map(lambda v: f"{int(v):,}"),
        "chance after K slots": (1e-9 / a.absorbs).map(lambda v: f"{v:.1e}"),
        "largest factor absorbed": a.absorbs.map(fac),
        "after a deflated inference: chance / factor": [f"{1e-9 / v:.1e} / {fac(v)}" for v in a.absorbs_deflated]})))
