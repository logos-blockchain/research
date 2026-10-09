"""Markdown tables for the study's notes, read straight from runs/ (no hand transcription).

    python scripts/tables.py a1 | c1 | c1settle | c3 | c4 | b3 | b3delay | b2 | b4 | b5 | b5rec | b5sweep | b5part | g1 | g3 | g4 |
                             b6 | b7 | d0 | d1b | d3 | d5 | d6 | e2 | e5 | e5balance
"""

from __future__ import annotations

import math
import pathlib
import sys

import numpy as np
import pandas as pd

RUNS = pathlib.Path(__file__).resolve().parent.parent / "runs"


def md(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(v) for v in r.to_list()) + " |")
    return "\n".join(out)


def a1() -> None:
    s = pd.read_csv(RUNS / "a1" / "summary.csv")
    s = s[s.family == "rounds"]
    t = pd.DataFrame({
        "hops": s.blend_hops, "Δ_max (rounds)": s.blend_delay_max.astype(int),
        "link (s)": s.link_latency_mean,
        "orphan share": s.orphan_share.map(lambda v: f"{v:.3f}"),
        "growth / f": s.growth_per_f.map(lambda v: f"{v:.3f}"),
        "mean delay (s)": s.vis_mean.map(lambda v: f"{v:.1f}"),
        "p99 full delay (s)": s.vis_full_p99.map(lambda v: f"{v:.1f}"),
        "30 deep, p50 (min)": (s.chain_30_p50_s / 60).map(lambda v: f"{v:.1f}"),
        "100 deep, p50 (min)": (s.chain_100_p50_s / 60).map(lambda v: f"{v:.1f}"),
    })
    print(md(t))
    c = pd.read_csv(RUNS / "a1" / "summary.csv")
    c = c[c.family == "calibration"]
    print()
    print(md(pd.DataFrame({"per-hop delay (s)": c.blend_delay_max,
                           "orphan share": c.orphan_share.map(lambda v: f"{v:.3f}"),
                           "± SEM": c.orphan_share_sem.map(lambda v: f"{v:.3f}"),
                           "mean delay (s)": c.vis_mean.map(lambda v: f"{v:.1f}")})))


def c1() -> None:
    s = pd.read_csv(RUNS / "c1" / "summary.csv")
    s["cell"] = s.apply(lambda r: f"{r.orphan_share:.3f} · {r.growth_per_f:.3f}", axis=1)
    p = s.pivot_table(index=["hops", "delta_max"], columns="interval", values="cell",
                      aggfunc="first")
    p = p[sorted(p.columns, reverse=True)].reset_index()
    p.columns = ["hops", "Δ_max"] + [f"{int(c)} s" for c in p.columns[2:]]
    print(md(p))


def c1settle() -> None:
    t = pd.read_csv(RUNS / "c1" / "settle_surface.csv")
    for a in sorted(t.alpha.unique()):
        p = t[(t.alpha == a) & (t.eps == 1e-9)].pivot_table(
            index=["hops", "delta_max"], columns="interval", values="minutes")
        p = p[sorted(p.columns, reverse=True)].reset_index()
        p["hops"] = p["hops"].astype(int)
        p["delta_max"] = p["delta_max"].astype(int)
        for c in p.columns[2:]:
            p[c] = p[c].map(lambda v: "–" if np.isnan(v) else f"{v:,.0f}")
        p.columns = ["hops", "Δ_max"] + [f"{int(c)} s" for c in p.columns[2:]]
        print(f"α = {a:.2f}, ε = 1e-9\n")
        print(md(p))
        print()


def b3() -> None:
    c = pd.read_csv(RUNS / "b3" / "curves.csv")
    o = pd.read_csv(RUNS / "b3" / "orphans.csv")
    rows = []
    for _, r in o.iterrows():
        g = c[(c.config == r.config) & (c.alpha == r.alpha)]
        q = r.adversary_slots / (r.adversary_slots + r.canonical)
        row = {"configuration": r.config, "α": r.alpha, "q": f"{q:.3f}",
               "orphan share": f"{r.orphan:.3f}"}
        for thr in (1e-3, 1e-4):
            for pm, w, lab in ((0, 0, "no lead, ties"), (0, 1, "no lead, strict"),
                               (1, 1, "premined, strict")):
                ps = g[(g.premine == pm) & (g.win_at == w)].sort_values("depth")
                hit = ps[ps.p <= thr]
                row[f"{lab} ≤ {thr:.0e}"] = int(hit.depth.iloc[0]) if len(hit) else "> 60"
        rows.append(row)
    print(md(pd.DataFrame(rows)))


def c4() -> None:
    e = pd.read_csv(RUNS / "c4" / "engine.csv")
    g = e.groupby(["curve", "blend"], sort=False).mean(numeric_only=True).reset_index()
    print(md(pd.DataFrame({
        "curve": g.curve, "Blend": g.blend,
        "orphan share": g.orphan_share.map(lambda v: f"{v:.3f}"),
        "canonical growth / f": g.growth_per_f.map(lambda v: f"{v:.3f}"),
        "blocks made / f": g.produced_per_f.map(lambda v: f"{v:.2f}"),
        "interval p50 / p99 (s)": [f"{a:.0f} / {b:.0f}"
                                   for a, b in zip(g.interval_p50, g.interval_p99)]})))
    print()
    r = pd.read_csv(RUNS / "c4" / "race.csv")
    kmax = max(int(c[1:]) for c in r.columns if c.startswith("s") and c[1:].isdigit())
    rows = []
    for (c, b), gg in r.groupby(["curve", "blend"], sort=False):
        row = {"curve": c, "Blend": b}
        for a, ga in gg.groupby("alpha", sort=False):
            if a < 0.2:
                continue
            tot = ga.sum(numeric_only=True)
            per_block = 1 / (ga.honest_per_f.mean() / 30) / 60            # minutes
            cells = []
            for eps in (1e-3, 1e-4):
                p = np.array([tot[f"s{k}"] / tot.scored for k in range(1, kmax + 1)])
                hit = np.nonzero(p <= eps)[0]
                cells.append(f"{hit[0] + 1} ({(hit[0] + 1) * per_block:.0f} min)" if hit.size
                             else f"> {kmax}")
            row[f"α = {a:.2f}: 1e-3 / 1e-4"] = " / ".join(cells)
        rows.append(row)
    print(md(pd.DataFrame(rows)))


def b3delay() -> None:
    t = pd.read_csv(RUNS / "b3" / "delay.csv")
    cols = [("lb", "lower bound", None), ("at_confirmation", "attack, at confirmation", "targets"),
            ("ever", "attack, any moment after", "targets"),
            ("private", "private attack alone", "private_targets"), ("ub", "upper bound", None)]

    def cell(r, col, n):
        v = r[col]
        if n is not None and v == 0:
            return f"< {1 / r[n]:.0e}"
        return f"{v:.1e}"
    rows = []
    for (a, d), g in t.groupby(["adv", "delay_s"], sort=False):
        g = g.set_index("depth")
        rows.append({"α": f"{a:.2f}", "Δ": f"{int(d)} s",
                     **{name: f"{cell(g.loc[10], c, n)} / {cell(g.loc[40], c, n)}"
                        for c, name, n in cols}})
    print(md(pd.DataFrame(rows)))


def b2() -> None:
    d = pd.read_csv(RUNS / "b2" / "depths.csv")
    for eps in (1e-6, 1e-9):
        t = d[d.eps == eps].copy()
        first = 20                                   # the lower bound's first computed depth

        def lower(v, extra):
            if v <= first:
                return f"≤ {first}"
            return f"{math.floor(v + 1e-9)}{'*' if extra else ''}"   # the attack reaches it

        t["cell"] = [f"{lower(r.lb_depth, r.lb_extrapolated)} – {int(r.ub_depth):,}"
                     for _, r in t.iterrows()]
        p = t.pivot(index="adv", columns="delay_s", values="cell").reset_index()
        p["adv"] = p["adv"].map(lambda v: f"{v:.2f}")
        p.columns = ["α"] + [f"{int(c)} s" for c in p.columns[1:]]
        print(f"ε = {eps:.0e}\n")
        print(md(p))
        print()


def b4() -> None:
    t = pd.read_csv(RUNS / "b4" / "elapsed.csv")

    def fail(v):
        return "0" if v == 0 else f"{v:.1e}"
    print(md(pd.DataFrame({
        "timelines": t.timelines, "α": t.alpha.map(lambda v: f"{v:.2f}"),
        "ε": t.eps.map(lambda v: f"{v:.0e}".replace("e-0", "e-")),
        "depth rule: blocks": t.depth,
        "depth rule: minutes, mean / p90": [f"{a:.1f} / {b:.1f}"
                                            for a, b in zip(t.depth_mean_min, t.depth_p90_min)],
        "elapsed-time rule: blocks, mean": t.elapsed_blocks.map(lambda v: f"{v:.1f}"),
        "elapsed-time rule: minutes, mean / p90": [f"{a:.1f} / {b:.1f}" for a, b in
                                                   zip(t.elapsed_mean_min, t.elapsed_p90_min)],
        "race beats the rule, depth / elapsed": [f"{fail(a)} / {fail(b)}"
                                                 for a, b in zip(t.depth_fail, t.elapsed_fail)]})))


def held(v: float) -> str:
    """A share held, as b5_what_k_holds.held_worst returns it."""
    return "< 0.05" if np.isnan(v) else "≥ 1/3" if np.isinf(v) else f"{v:.3f}"


def b5() -> None:
    r = pd.read_csv(RUNS / "b5" / "random_delay.csv")
    ks = [c for c in r.columns if c.startswith("k=")]
    t = pd.DataFrame({"Blend": r.blend, "growth / f": r.growth.map(lambda v: f"{v:.3f}"),
                      "ε": r.eps.map(lambda v: f"{v:.0e}".replace("e-0", "e-"))})
    for c in ks:
        t[c.replace("k=", "k = ") if c == ks[0] else c[2:]] = r[c].map(lambda v: f"{v:.3f}")
    print(md(t))
    print()
    w = pd.read_csv(RUNS / "b5" / "worst_case.csv")
    w = w[w.eps == 1e-9]
    t = pd.DataFrame({"Δ": w.delay_s.map(lambda v: f"{int(v)} s")})

    for c in ks:
        t[c.replace("k=", "k = ") if c == ks[0] else c[2:]] = w[c].map(held).values
    print(md(t))


def b5rec() -> None:
    e = pd.read_csv(RUNS / "b5" / "recovery_engine.csv")
    print(md(pd.DataFrame({
        "Blend": e.blend, "window (slots)": e.window,
        "growth / f": e.growth_per_f.map(lambda v: f"{v:.3f}"),
        "variance / mean, engine": e.dispersion.map(lambda v: f"{v:.2f}"),
        "± SEM": e.dispersion_sem.map(lambda v: f"{v:.2f}"),
        "binomial model": e.binomial_dispersion.map(lambda v: f"{v:.2f}")})))
    print()
    w = pd.read_csv(RUNS / "b5" / "recovery_window.csv")
    ks = [int(c.rsplit("k", 1)[1]) for c in w.columns if c.startswith("log10_fail_k")]
    pick = ["random, testnet", "random, specification", "worst, 10 s"]
    t = w[w.model.isin(pick) & (w.alpha >= 0.1)]
    out = pd.DataFrame({"delay": t.model, "α": t.alpha.map(lambda v: f"{v:.2f}")})
    for k in ks:
        out[f"k = {k} ({k / (4 / 30) / 3600:.3g} h)"] = t[f"log10_fail_k{k}"].map(
            lambda v: f"{10 ** v:.0e}")
    print(md(out))
    print()
    cols = ["random, testnet", "random, specification", "worst, 1 s", "worst, 10 s",
            "worst, 20 s"]
    out = pd.DataFrame({"α": sorted(w.alpha.unique())})
    for c in cols:
        g = w[w.model == c].set_index("alpha")
        out[c] = [("–" if np.isnan(g.loc[a, "window_h_1e-09"]) else
                   f"{g.loc[a, 'window_h_1e-09']:.1f}") + " / " +
                  ("–" if np.isnan(g.loc[a, "window_h_1e-12"]) else
                   f"{g.loc[a, 'window_h_1e-12']:.1f}") for a in out["α"]]
    out["α"] = out["α"].map(lambda v: f"{v:.2f}")
    print(md(out))
    print()
    s = pd.read_csv(RUNS / "b5" / "recovery_share.csv")
    s = s[s.model.isin(cols[:2] + cols[3:]) & s.eps.isin([1e-9, 1e-12])]
    ks = [c for c in s.columns if c.startswith("k=")]
    out = pd.DataFrame({"delay": s.model, "ε per window": s.eps.map(lambda v: f"{v:.0e}")})
    for c in ks:
        out[c.replace("k=", "k = ") if c == ks[0] else c[2:]] = s[c].map(lambda v: f"{v:.3f}")
    print(md(out))


def c3() -> None:
    r = pd.read_csv(RUNS / "c3" / "regions.csv")
    t = r.copy()
    for c in t.columns[1:]:
        t[c] = t[c].map(lambda v: f"{v:.4f}")
    print(md(t))


def b6() -> None:
    t = pd.read_csv(RUNS / "b6" / "grinding.csv")

    def factor(v):
        if v < 10:
            return f"{v:.1f}"
        if v < 1e4:
            return f"{float(f'{v:.2g}'):,.0f}"
        return f"{v:.0e}".replace("e+0", "e").replace("e+", "e")

    def span(lo, hi):
        lo, hi = (f"{v:,.0f}" for v in (lo, hi))
        return lo if lo == hi else f"{lo}–{hi}"
    print(md(pd.DataFrame({
        "delay": t.model, "α": t.alpha.map(lambda v: f"{v:.2f}"),
        "epochs with a choice at the cut-off": t.p_choice.map(lambda v: f"{100 * v:.0f} %"),
        "factor at 1e-9, one nonce": [f"{factor(a)}–{factor(b)}"
                                      for a, b in zip(t["factor_lo_1e-09"], t["factor_hi_1e-09"])],
        "two nonces": [f"{factor(a)}–{factor(b)}" for a, b in zip(t["pair_lo_1e-09"], t["pair_hi_1e-09"])],
        "set by the budget": t["budget_binds_1e-09"].map(lambda v: "yes" if v else "–"),
        "depth at 1e-9 → one nonce → two nonces": [
            f"{r['depth_1e-09']:,.0f} → {span(r['ground_lo_1e-09'], r['ground_hi_1e-09'])} → "
            f"{span(r['ground2_lo_1e-09'], r['ground2_hi_1e-09'])}" for _, r in t.iterrows()]})))
    print()
    d = pd.read_csv(RUNS / "b6" / "delays.csv")
    rows = []
    for (a, b), g in d.groupby(["alpha", "budget_bits"]):
        row = {"α": f"{a:.2f}", "nonces evaluated": f"2^{b}"}
        for _, x in g.sort_values("delay_s").iterrows():
            row[f"{x.delay_s:.0f} s"] = f"{x['depth_1e-09']:,.0f} → {x['ground2_hi_1e-09']:,.0f}"
        rows.append(row)
    print(md(pd.DataFrame(rows)))
    print()
    h = pd.read_csv(RUNS / "b6" / "shares.csv")
    rows = []
    for m, g in h.groupby("model", sort=False):
        row = {"delay": m}
        for i, (_, x) in enumerate(g.iterrows()):
            row[f"k = {x.k}" if i == 0 else f"{x.k}"] = f"{held(x.held_without)} → {held(x.held_two)}"
        rows.append(row)
    print(md(pd.DataFrame(rows)))
    print()
    r = pd.read_csv(RUNS / "b6" / "recovery.csv")
    longest = {2160: 72, 1620: 54, 1080: 36, 432: 14.4, 216: 7.2, 120: 4}
    r = r[(r.model == "random, specification") & (r.c == 1.0)]

    def days(v):
        if np.isinf(v):
            return "≥ 3650"
        if v < 1 / 24:
            return "< 1 h"
        return f"{24 * v:.0f} h" if v < 2 else f"{v:,.0f}"

    def turnover(g, col):
        lo, hi = (g[g.tau_per_day == tau][col].iloc[0] for tau in (2.43e-3, 1.25e-3))
        if 1 / 24 <= lo < 2 <= hi < 10:
            return f"{24 * lo:.0f}–{24 * hi:.0f} h"
        lo, hi = days(lo), days(hi)
        return lo if lo == hi else f"{lo}–{hi}"
    rows = []
    for k, w in longest.items():
        row = {"k": f"{k}", "window": f"{w:g} h"}
        for a in (0.20, 0.25, 0.30, 0.3333):
            g = r[(r.k == k) & (r.window_h == w) & (r.alpha.round(4) == a)]
            row[f"α = {a:.2f}"] = f"{turnover(g, 'h_days')} / {turnover(g, 'h_days_ground')}"
        rows.append(row)
    print(md(pd.DataFrame(rows)))


def b7() -> None:
    b = pd.read_csv(RUNS / "b7" / "budget.csv")
    m = pd.read_csv(RUNS / "b7" / "minimum.csv")
    cols = [("random, specification", 0.3), ("random, specification", 0.3333), ("worst, 10 s", 0.3),
            ("worst, 10 s", 0.3333)]

    def name(model, a):
        return f"{model}, α = {a:.2f}"

    def span(lo, hi):
        lo, hi = (f"{v:,.0f}" for v in (lo, hi))
        return lo if lo == hi else f"{lo}–{hi}"
    rows = [{"nonce": "not ground"} | {name(*c): f"{b[(b.model == c[0]) & (b.alpha == c[1])]['depth_1e-09'].iloc[0]:,.0f}"
                                     for c in cols}]
    for bits in sorted(b.budget_bits.unique()):
        row = {"nonce": f"hash chain, 2^{bits} evaluated"}
        for c in cols:
            x = b[(b.model == c[0]) & (b.alpha == c[1]) & (b.budget_bits == bits)].iloc[0]
            row[name(*c)] = span(x.depth_two_lo, x.depth_two_hi)
        rows.append(row)
    for k in (2160, 1620, 1080):
        cut = {"nonce": f"smallest contributions, k = {k}, at the cut-off"}
        est = {"nonce": f"smallest contributions, k = {k}, estimated"}
        for c in cols:
            x = m[(m.model == c[0]) & (m.alpha == c[1]) & (m.k == k)].iloc[0]
            cut[name(*c)] = f"{x.depth_two_cutoff:,.0f}"
            est[name(*c)] = span(x.depth_two_lo, x.depth_two_hi)
        rows += [cut, est]
    print(md(pd.DataFrame(rows)))
    print()

    def count(v):
        if v < 10:
            return f"{v:.2f}"
        if v < 1e4:
            return f"{v:,.0f}"
        return f"{v:.0e}".replace("e+0", "e").replace("e+", "e")
    rows = []
    for (model, a), g in m.groupby(["model", "alpha"], sort=False):
        if a < 0.25:
            continue
        row = {"delay": model, "α": f"{a:.2f}"}
        for _, x in g[g.k >= 432].sort_values("k", ascending=False).iterrows():
            row[f"k = {x.k}, m = {x.sub_windows}"] = count(x.mean_g)
        rows.append(row)
    print(md(pd.DataFrame(rows)))
    print()
    rows = []
    for _, x in m[(m.alpha >= 0.25) & (m.k == 2160)].iterrows():
        rows.append({"delay": x.model, "α": f"{x.alpha:.2f}", "p_own": f"{x.own:.2f}",
                     "removal": f"{x.coin:.2f}", "p_disp": f"{x.p_disp:.2f}",
                     "at the cut-off": f"{x.mean_g:.2f}",
                     "last sub-window": f"{x.c_last_lo:.2f}–{x.c_last_hi:.2f}",
                     "factor per nonce": f"{x.factor_lo:.2f}–{x.factor_hi:.2f}"})
    print(md(pd.DataFrame(rows)))
    print()
    rows = []
    for _, x in m[(m.model == "worst, 10 s") & (m.alpha.round(4) == 0.3333)].iterrows():
        rows.append({"k": f"{x.k}", "epochs in ten years": f"{YEARS * 365.25 * 86400 / (10 * (30 * x.k)):,.0f}",
                     "m, one window": f"{x.m_life}", "m, two windows": f"{x.m}",
                     "sub-window (slots)": f"{x.sub_slots:,}"})
    print(md(pd.DataFrame(rows)))
    print()
    r = pd.read_csv(RUNS / "b7" / "recovery.csv")

    def days(v):
        return "≥ 3650" if np.isinf(v) else "< 1 h" if v < 1 / 24 else f"{v:,.0f}"

    def turnover(g, col):
        lo, hi = (days(g[g.tau_per_day == tau][col].iloc[0]) for tau in (2.43e-3, 1.25e-3))
        return lo if lo == hi else f"{lo}–{hi}"
    rows = []
    for (model, k, w), g in r.groupby(["model", "k", "window_h"], sort=False):
        row = {"delay": model, "k": f"{k}", "window": f"{w:g} h"}
        for a in (0.25, 0.30, 0.3333):
            x = g[g.alpha.round(4) == a]
            row[f"α = {a:.2f}"] = f"{turnover(x, 'h_days')} / {turnover(x, 'h_days_minimum')}"
        rows.append(row)
    print(md(pd.DataFrame(rows)))


YEARS = 10


def g1() -> None:
    t = pd.read_csv(RUNS / "g1" / "lasts.csv")
    rows = []
    for (model, a), g in t.groupby(["model", "alpha"], sort=False):
        row = {"delay": model, "α": f"{a:.2f}"}
        for _, x in g.iterrows():
            row[f"{int(x.minutes)} min"] = f"{x.p_lasts:.2g}" if x.p_lasts >= 1e-3 else f"{x.p_lasts:.0e}"
        rows.append(row)
    print(md(pd.DataFrame(rows)))
    print()
    f = pd.read_csv(RUNS / "g1" / "factor.csv")
    rows = []
    for (model, a, k), g in f.groupby(["model", "alpha", "k"], sort=False):
        if a < 0.3:
            continue
        x = g.iloc[0]
        row = {"delay": model, "α": f"{a:.2f}", "k": f"{k}", "not ground": f"{x['depth_1e-09']:,.0f}",
               "B7's estimate": (f"{x.depth_two_lo:,.0f}" if x.depth_two_lo == x.depth_two_hi
                                 else f"{x.depth_two_lo:,.0f}–{x.depth_two_hi:,.0f}")}
        for _, y in g.sort_values("minutes").iterrows():
            row[f"T = {int(y.minutes)} min"] = f"{y.factor:.3f}, {y.depth_two:,.0f}"
        rows.append(row)
    print(md(pd.DataFrame(rows)))
    print()
    r = pd.read_csv(RUNS / "g1" / "recovery.csv")

    def days(v):
        return "≥ 3650" if np.isinf(v) else "< 1 h" if v < 1 / 24 else f"{v:,.0f}"

    def turnover(g, col):
        lo, hi = (days(g[g.tau_per_day == tau][col].iloc[0]) for tau in (2.43e-3, 1.25e-3))
        return lo if lo == hi else f"{lo}–{hi}"
    rows = []
    for (model, k, w), g in r.groupby(["model", "k", "window_h"], sort=False):
        row = {"delay": model, "k": f"{k}", "window": f"{w:g} h"}
        for a in (0.30, 0.3333):
            x = g[g.alpha.round(4) == a]
            row[f"α = {a:.2f}"] = f"{turnover(x, 'h_days')} / {turnover(x, 'h_days_delayed')}"
        rows.append(row)
    print(md(pd.DataFrame(rows)))


def g3() -> None:
    t = pd.read_csv(RUNS / "g3" / "blend_delay.csv")

    def cell(depth, hours, ground, ground_h):
        if np.isinf(depth):
            return "–"
        return f"{depth:,.0f} ({hours:.1f} h), {ground:,.0f} ({ground_h:.1f} h)"
    rows = []
    for (h, r), g in t.groupby(["hops", "rounds"], sort=False):
        x = g.iloc[0]
        row = {"hops": f"{h}", "rounds": f"{r}", "p99 delay": f"{x.p99_s:.1f} s", "Δ": f"{x.delta_s} s",
               "orphans": f"{x.orphan:.2f}", "growth / f": f"{x.growth:.3f}",
               "path captured": f"{x.capture:.3f}", "blending": f"{x.blending:.2f}"}
        for _, y in g.iterrows():
            a = f"{y.alpha:.2f}"
            row[f"random, {a}"] = cell(y.random_depth, y.random_h, y.random_ground_depth, y.random_ground_h)
            row[f"worst, {a}"] = cell(y.worst_depth, y.worst_h, y.worst_ground_depth, y.worst_ground_h)
        rows.append(row)
    print(md(pd.DataFrame(rows)))


def g4() -> None:
    t = pd.read_csv(RUNS / "g4" / "time_rule.csv")

    def pair(n, m):
        return f"{int(n)}, {m:.0f} min" if n > 0 else "the depth rule's"
    print(md(pd.DataFrame({
        "Blend": t.blend, "α": t.alpha.map(lambda v: f"{v:.2f}"),
        "depth rule, full / withheld from": [f"{int(p)}: {a:.0f} / {b:.0f} min" for p, a, b in
                                              zip(t.plain_depth, t.plain_min_full, t.plain_min_held)],
        "elapsed time, B4's rates, full": [pair(n, m) for n, m in zip(t.b4_full_n, t.b4_full_min)],
        "withheld from": [pair(n, m) for n, m in zip(t.b4_held_n, t.b4_held_min)],
        "adjusted rates, full": [pair(n, m) for n, m in zip(t.adjusted_full_n, t.adjusted_full_min)],
        "withheld from ": [pair(n, m) for n, m in zip(t.adjusted_held_n, t.adjusted_held_min)],
        "reading density, full": [f"{pair(n, m)}, 1e{c:.0f}" for n, m, c in
                                  zip(t.density_n, t.density_min_full, t.density_log10_chance)]})))
    print()
    print(md(pd.DataFrame({
        "Blend": t.blend, "α": t.alpha.map(lambda v: f"{v:.2f}"),
        "B4's rates: blocks on top, minutes, p90": [f"{b:.1f}, {m:.0f}, {p:.0f}" for b, m, p in
                                                     zip(t.b4_full_sim_blocks, t.b4_full_sim_min, t.b4_full_sim_p90)],
        "adjusted rates: blocks on top, minutes, p90": [f"{b:.1f}, {m:.0f}, {p:.0f}" for b, m, p in
                                                         zip(t.adjusted_full_sim_blocks, t.adjusted_full_sim_min,
                                                             t.adjusted_full_sim_p90)]})))


def g6() -> None:
    t = pd.read_csv(RUNS / "g6" / "relays.csv")
    labels = {(False, "hold"): "honest", (True, "hold"): "hostile, holding", (True, "drop"): "hostile, dropping"}
    rows = []
    for _, x in t.iterrows():
        rows.append({"α": f"{x.alpha:.2f}", "relays": labels[(bool(x.hostile), x.action)],
                     "copies": int(x.copies), "coalition's share of relays": f"{x.node_share:.3f}",
                     "orphans ± sem": f"{x.orphan:.3f} ± {x.orphan_sem:.3f}",
                     "blocks by the fallback": f"{x.fallback:.3f}" if x.hostile else "–",
                     "growth / win": f"{x.growth:.3f}", "race depth at 1e-3": f"{x.race_depth_1e3}",
                     "closed form at 1e-9": f"{x.closed_depth_1e9:,.0f} ({x.hours_1e9:.1f} h)"})
    print(md(pd.DataFrame(rows)))


def g7() -> None:
    t = pd.read_csv(RUNS / "g7" / "inference.csv")
    print(md(pd.DataFrame({
        "α": t.alpha.map(lambda v: f"{v:.2f}"), "raise": t.raise_factor.map(lambda v: f"{v:.2f}"),
        "Δ = 10 s reads as": t.delay_eq_s.map(lambda v: f"{v:.1f} s"),
        "B2's depth at 1e-9": [f"{int(b):,} → {int(d):,} ({h:.1f} h)" for b, d, h in zip(t.worst_depth_base, t.worst_depth, t.worst_hours)],
        "orphans, growth / win": [f"{o:.3f}, {b:.3f} → {g:.3f}" for o, b, g in zip(t.orphan, t.growth_base, t.growth)],
        "B5's closed form at 1e-9": [f"{int(b):,} → {int(d):,} ({h:.1f} h)" for b, d, h in zip(t.random_depth_base, t.random_depth, t.random_hours)],
        "k = 2160 on the honest chain": t.k_hours.map(lambda v: f"{v:.1f} h"),
        "extra wins an epoch": t.extra_wins.map(lambda v: f"{v:,.0f}"),
        "selection, Brownian / played": [f"{b:.0f} / {m:.0f} ({s:.2%} of its wins)" for b, m, s in zip(t.excess_brownian, t.excess_mc, t.excess_share)]})))
    print()
    c = pd.read_csv(RUNS / "g7" / "clamp.csv")
    rows = []
    for _, x in c.iterrows():
        row = {"cap a period": f"{x.cap:.0%}"}
        for a in (0.25, 0.3, 0.3333):
            row[f"α = {a:.2f}"] = f"{int(x[f'periods_{a}'])} periods ({x[f'days_{a}']:.0f} d)"
        rows.append(row)
    print(md(pd.DataFrame(rows)))


def h1() -> None:
    s = pd.read_csv(RUNS / "h1" / "seats.csv")
    rows = []
    for a, g in s.groupby("alpha", sort=False):
        row = {"α": f"{a:.2f}", "honest side": f"{g.honest_side.iloc[0]:.3f}"}
        for _, x in g.iterrows():
            tag = "every honest vote counts" if x.undelivered == 0 else f"{x.undelivered:.0%} of honest votes lost"
            row[f"seats, {tag}"] = "none" if x.seats < 0 else f"{int(x.seats):,} (θ = {int(x.threshold):,})"
        rows.append(row)
    print(md(pd.DataFrame(rows)))
    print()
    d = pd.read_csv(RUNS / "h1" / "detector.csv")
    sides = [c for c in d.columns if c.startswith("side_")]
    rows = []
    for _, x in d.iterrows():
        row = {"α": f"{x.alpha:.2f}", "window": f"{x.window_h:g} h", "expected, honest alone": f"{x.expected_full:,.0f}",
               "threshold": f"{int(x.threshold):,}"}
        for c in sides:
            v = x[c]
            row[f"side {float(c[5:]):.3f}"] = f"{v:.3g}" if 1e-3 <= v < 0.999 else (f"{v:.0e}" if v < 1e-3 else f"{v:.4f}")
        rows.append(row)
    print(md(pd.DataFrame(rows)))


def h2() -> None:
    f = pd.read_csv(RUNS / "h2" / "factor.csv")
    rows = []
    for (model, a), g in f.groupby(["model", "alpha"], sort=False):
        row = {"delay": model, "α": f"{a:.2f}", "not ground": f"{g['depth_1e-09'].iloc[0]:,.0f}"}
        for _, x in g.sort_values("minutes").iterrows():
            row[f"margin {int(x.minutes)} min"] = f"{x.factor:.3f}, {x.depth_two:,.0f}"
        rows.append(row)
    print(md(pd.DataFrame(rows)))
    print()
    sp = pd.read_csv(RUNS / "h2" / "span.csv")
    rows = []
    for _, x in sp.iterrows():
        row = {"k": f"{int(x.k):,}", "m": int(x.sub_windows), "sub-window W": f"{x.sub_window_slots / 3600:.2f} h",
               "margin": f"{int(x.margin_min)} min", "T_a = W + margin": f"{x.t_a_slots / 3600:.2f} h"}
        for r in (3, 5, 10, 15):
            row[f"honest time, R = {r}"] = f"{x[f'honest_hours_r{r}']:.1f} h"
        row["phase 4⌊k/f⌋"] = f"{x.phase_slots / 3600:.0f} h"
        row["largest R"] = f"{x.largest_ratio:.1f}"
        rows.append(row)
    print(md(pd.DataFrame(rows)))
    print()
    gm = pd.read_csv(RUNS / "h2" / "gmin.csv")
    print(md(pd.DataFrame({
        "delay": gm.model, "α": gm.alpha.map(lambda v: f"{v:.2f}"), "k": gm.k.map(lambda v: f"{v:,}"),
        "E[G_min], sampled": gm.sampled.map(lambda v: f"{v:.3f}"),
        "given the slots": [f"{c:.3f} ± {s:.3f}" for c, s in zip(gm.conditional, gm.conditional_sem)],
        "bound": gm.bound.map(lambda v: f"{v:.3f}"), "E[D]": gm.e_d.map(lambda v: f"{v:.1f}"),
        "E[A]": gm.e_a.map(lambda v: f"{v:.1f}"),
        "depth with two nonces, sampled → bound": [f"{int(s):,} → {int(b):,}" for s, b in zip(gm.depth_two_sampled, gm.depth_two)]})))


def h3() -> None:
    c = pd.read_csv(RUNS / "h3" / "counting.csv")
    rows = []
    for _, x in c.iterrows():
        row = {"α": f"{x.alpha:.2f}", "catch-up ratio": f"{x.ratio:.2f}"}
        for name, label in (("full", "full rate"), ("withheld", "withheld from"), ("worst", "worst-case rate")):
            d, hrs = x[f"depth_{name}"], x[f"hours_{name}"]
            row[f"depth at 1e-9, {label}"] = f"{int(d):,} ({hrs:.1f} h)" if d > 0 else "–"
        rows.append(row)
    print(md(pd.DataFrame(rows)))
    print()
    p = pd.read_csv(RUNS / "h3" / "precheck.csv")

    def rate(v):
        return f"{v:.1e}" if v > 0 else "0"
    print(md(pd.DataFrame({
        "α": p.alpha.map(lambda v: f"{v:.2f}"), "rule": p.rule, "B2's attack depth at 1e-3": p.lb_depth,
        "targets": p.targets.map(lambda v: f"{v:,}"), "accepted": p.accepted_share.map(lambda v: f"{v:.3f}"),
        "mean depth at acceptance": p.mean_depth.map(lambda v: f"{v:.1f}"),
        "attack wins at acceptance": p.fail_at_acceptance.map(rate), "ever": p.fail_ever.map(rate)})))
    print()
    pl = pd.read_csv(RUNS / "h3" / "played.csv")
    print(md(pd.DataFrame({
        "α": pl.alpha.map(lambda v: f"{v:.2f}"), "targets accepted": pl.accepted.map(lambda v: f"{v:,}"),
        "mean depth at acceptance": pl.mean_depth.map(lambda v: f"{v:.1f}"),
        "minutes": pl.mean_minutes.map(lambda v: f"{v:.0f}"),
        "the race beats the rule": pl.race_beats.map(lambda v: f"{v:.1e}" if v > 0 else "0")})))
    print()
    ob = pd.read_csv(RUNS / "h3" / "observed.csv")

    def depth(v):
        return f"{int(v):,}" if v > 0 else "–"
    print(md(pd.DataFrame({
        "α": ob.alpha.map(lambda v: f"{v:.2f}"), "B2, worst case": ob.b2_depth.map(depth),
        "B5, random delay": ob.closed_depth.map(depth),
        "no forks, full rate": ob.full_0.map(depth),
        "no forks, withheld from": [f"{depth(d)} ({h:.1f} h)" if d > 0 else "–"
                                    for d, h in zip(ob.withheld_0, ob.hours_withheld_0)],
        "two forks, withheld from": ob.withheld_2.map(depth), "four forks, withheld from": ob.withheld_4.map(depth),
        "a balancing coalition, worst-case rate": ob.balancing.map(depth),
        "a coalition publishing every win as a fork": ob.publishing.map(depth)})))
    print()
    fk = pd.read_csv(RUNS / "h3" / "forks.csv")
    print(md(pd.DataFrame({
        "α": fk.alpha.map(lambda v: f"{v:.2f}"), "targets": fk.targets.map(lambda v: f"{v:,}"),
        "none": fk.none.map(lambda v: f"{v:.3f}"), "mean": fk["mean"].map(lambda v: f"{v:.3f}"),
        "90th percentile": fk.p90.map(lambda v: f"{v:.0f}"), "99th percentile": fk.p99.map(lambda v: f"{v:.0f}"),
        "most": fk.most})))
    print()
    po = pd.read_csv(RUNS / "h3" / "played_observed.csv")
    print(md(pd.DataFrame({
        "α": po.alpha.map(lambda v: f"{v:.2f}"), "timelines": po.timelines,
        "targets": po.targets.map(lambda v: f"{v:,}"),
        "accepted": [f"{a / t:.3f}" for a, t in zip(po.accepted, po.targets)],
        "mean depth at acceptance": po.mean_depth.map(lambda v: f"{v:.1f}"),
        "minutes": po.mean_minutes.map(lambda v: f"{v:.0f}"),
        "the race beats the rule": po.race_beats.map(lambda v: f"{v:.1e}" if v > 0 else "0")})))


def b5part() -> None:
    t = pd.read_csv(RUNS / "b5" / "partition.csv")
    sides = [c for c in t.columns if c.startswith("side_") and c != "side_whole"]
    rows = []
    for _, x in t[t.window_h.isin([36, 72])].iterrows():
        row = {"delay": x.model, "α": f"{x.alpha:.2f}", "window": f"{x.window_h:g} h",
               "side beaten in expectation": f"≤ {x.beaten_side:.3f}"}
        for c in sides:
            row[f"side {float(c[5:]):.3f}"] = f"{x[c]:.2g}" if x[c] >= 1e-3 else f"{x[c]:.0e}"
        row["the whole honest chain"] = f"{x.side_whole:.0e}"
        rows.append(row)
    print(md(pd.DataFrame(rows)))
    print()
    s = pd.read_csv(RUNS / "b5" / "ties.csv")
    print(md(pd.DataFrame({"k": s.k, "window": s.window_h.map(lambda v: f"{v:g} h"),
                           "blocks a side, mean": s["mean"].map(lambda v: f"{v:,.0f}"),
                           "P(tie)": s.p_tie.map(lambda v: f"{v:.4f}")})))


def duration(days: float) -> str:
    if days >= 10:
        return f"{days:,.0f} d"
    if days >= 1:
        return f"{days:.1f} d"
    if days * 24 >= 1:
        return f"{days * 24:.1f} h"
    if days * 1440 >= 1:
        return f"{days * 1440:.0f} min"
    return f"{days * 86400:.0f} s"


def d5() -> None:
    t = pd.read_csv(RUNS / "d5" / "times.csv")
    rows = []
    for s, g in t.groupby("share", sort=False):
        row = {"share": f"{100 * s:g} %"}
        for _, x in g.iterrows():
            row[x.setting] = f"{duration(x.identify_days)} / {duration(x.size_days)}"
        rows.append(row)
    print(md(pd.DataFrame(rows)))
    print()
    e = pd.read_csv(RUNS / "d5" / "epoch.csv")
    print(md(pd.DataFrame({
        "votes": e.setting,
        "confidence for a 1.26 % holder": e.confidence.map(lambda v: f"{v:.2f}"),
        "nodes it must split into": e.nodes.map(lambda v: "–" if np.isnan(v) else f"{v:,.0f}"),
        "every share above it sized": e.sized_above.map(
            lambda v: "–" if np.isnan(v) else f"{100 * v:.2g} %")})))


def d1b() -> None:
    t = pd.read_csv(RUNS / "d1b" / "committee.csv")
    rows = []
    for a, g in t.groupby("alpha", sort=False):
        row = {"α": "1/3" if abs(a - 1 / 3) < 1e-3 else f"{a:.2f}"}
        for _, x in g.iterrows():
            row[f"uptime {x.uptime:g}"] = ("impossible" if np.isinf(x.honest_share)
                                           else f"{x.honest_share:.2f} / {x.holders:,.0f}")
        rows.append(row)
    print(md(pd.DataFrame(rows)))


def d0() -> None:
    m = pd.read_csv(RUNS / "d0" / "emission_map.csv")
    d = m[(m.awake == 1.0) & (m.inflation == 1.0) & (m.eps == 1e-9)]
    t = pd.DataFrame({"α": d.alpha, "seats": d.seats.map(lambda v: f"{v:,.0f}"),
                      **{f"{r} s": d[f"x_R{r}"].map(lambda v: f"×{v:,.0f}")
                         for r in (90, 600, 3600)}})
    print(md(t))
    print()
    d = m[m.eps == 1e-9].pivot_table(index="alpha", columns=["awake", "inflation"], values="seats",
                                     dropna=False)
    t = pd.DataFrame({"α": d.index.map(lambda v: f"{v:.2f}")})
    for (awake, infl), name in (((1.0, 1.0), "all count"), ((1.0, 1.05), "all count, D/D̂ ≤ 1.05"),
                                ((0.9, 1.0), "90 % count"), ((0.9, 1.05), "90 % count, D/D̂ ≤ 1.05"),
                                ((0.8, 1.0), "80 % count")):
        t[name] = [("none" if np.isnan(v) else f"{v:,.0f}") for v in d[(awake, infl)]]
    print(md(t))


def d3() -> None:
    b = pd.read_csv(RUNS / "d0" / "blend_load.csv")
    b = b[b.alpha.isin((0.10, 0.20, 0.25, 0.30))]
    print(md(pd.DataFrame({
        "α": b.alpha.map(lambda v: f"{v:.2f}"), "round": b.round_s.map(lambda v: f"{v // 60:.0f} min"),
        "votes / s": b.votes.map(lambda v: f"{v:.2f}"),
        "votes on top of cover: F_1 / verifications per s": [
            f"{a:.1f} / {c:.0f}" for a, c in zip(b.f1_on_top, b.verify_on_top)],
        "cover raised: F_1 / verifications per s": [
            f"{a:,.0f} / {c:,.0f}" for a, c in zip(b.f1_in_cover, b.verify_in_cover)]})))


def d6() -> None:
    a = pd.read_csv(RUNS / "d6" / "agreement.csv")
    g = a.groupby(["blend", "lag"], sort=False).agreement
    t = pd.DataFrame({"mean": g.mean(), "p1": g.quantile(0.01)}).reset_index()
    out = pd.DataFrame({"Blend": t.blend.unique()})
    for lag in t.lag.unique():
        sub = t[t.lag == lag].set_index("blend")
        out[f"L = {lag}"] = [f"{sub.loc[b, 'mean']:.3f} / {sub.loc[b, 'p1']:.3f}"
                             for b in out.Blend]
    print(md(out))
    print()
    c = pd.read_csv(RUNS / "d6" / "certificates.csv")
    c = c[c.lag == 60]
    rows = []
    for (b, al), gg in c.groupby(["blend", "alpha"], sort=False):
        rows.append({"Blend": b, "α": f"{al:.2f}", "seats / quorum":
                     f"{gg.seats.iloc[0]:,} / {gg.quorum.iloc[0]:,}",
                     "rounds": len(gg), "certified": f"{gg.all_certified.mean():.3f}",
                     "time to quorum p50 / p95 (s)":
                     f"{gg.p50.median():.1f} / {gg.p95.median():.1f}"})
    print(md(pd.DataFrame(rows)))


def _depths(g: pd.DataFrame, kmax: int, per_slot: float, eps_list=(1e-3, 1e-4)) -> str:
    tot = g.sum(numeric_only=True)
    p = np.array([tot[f"s{k}"] / tot.scored for k in range(1, kmax + 1)])
    cells = []
    for eps in eps_list:
        hit = np.nonzero(p <= eps)[0]
        cells.append(f"{hit[0] + 1} ({(hit[0] + 1) / per_slot / 60:.1f})" if hit.size
                     else f"> {kmax}")
    return " / ".join(cells)


def e2() -> None:
    s = pd.read_csv(RUNS / "e2" / "structure.csv")
    base = 1 - (1 - 1 / 30) ** 1.0
    rows = []
    for (f, blend), g in s.groupby(["f", "blend"], sort=False):
        own = g[g.window == g.window.max()]
        narrow = g[g.window == 30]
        rows.append({"f_A": f"{f:.3g}", "Blend": blend, "window": int(own.window.iloc[0]),
                     "blocks per slot / Cryptarchia's": f"{own.blocks_per_slot.mean() / base:.2f}",
                     "s per layer": f"{1 / own.layers_per_slot.mean():.1f}",
                     "references mean / p99": f"{own.refs_mean.mean():.2f} / "
                                              f"{own.refs_p99.mean():.1f}",
                     "long only, w = 30 / own w": f"{narrow.long_ref_share.mean():.3f} / "
                                                  f"{own.long_ref_share.mean():.3f}"})
    print(md(pd.DataFrame(rows)))
    print()
    r = pd.read_csv(RUNS / "e2" / "race.csv")
    c = pd.read_csv(RUNS / "c4" / "race.csv")
    chain = {"constant": 1 / 30, "constant, 20 s": 1 / 20, "constant, 15 s": 1 / 15}
    rows = []
    for (f, blend), g in r[r.horizon == "since the fork"].groupby(["f", "blend"], sort=False):
        row = {"structure": "DAG", "f": f"{f:.3g}", "Blend": blend}
        for a, ga in g.groupby("alpha", sort=False):
            row[f"α = {a:.2f}"] = _depths(ga, 60, ga.layers_per_slot.mean())
        rows.append(row)
    for (curve, blend), g in c[c.curve.isin(list(chain))].groupby(["curve", "blend"], sort=False):
        row = {"structure": "chain", "f": f"{chain[curve]:.3g}", "Blend": blend}
        for a, ga in g.groupby("alpha", sort=False):
            row[f"α = {a:.2f}"] = _depths(ga, 60, ga.honest_per_f.mean() / 30)
        rows.append(row)
    print(md(pd.DataFrame(rows)))
    print()
    t = pd.read_csv(RUNS / "e2" / "fit.csv")
    rows = []
    for (st, f, blend), g in t.groupby(["structure", "f", "blend"], sort=False):
        row = {"structure": st, "f": f"{f:.3g}", "Blend": blend}
        for _, x in g.iterrows():
            row[f"α = {x.alpha:.2f}"] = ("–" if np.isnan(x["depth_1e-09"]) else
                                       f"{x['depth_1e-09']:.0f} ({x['minutes_1e-09']:.0f})")
        rows.append(row)
    print(md(pd.DataFrame(rows)))
    print()
    rows = []
    for (f, blend), g in r[r.horizon == "last w slots"].groupby(["f", "blend"], sort=False):
        row = {"f": f"{f:.3g}", "Blend": blend}
        for a, ga in g.groupby("alpha", sort=False):
            tot = ga.sum(numeric_only=True)
            row[f"α = {a:.2f}"] = (f"{tot.s10 / tot.scored:.2f} / {tot.s40 / tot.scored:.2f}")
        rows.append(row)
    print(md(pd.DataFrame(rows)))


def e5() -> None:
    t = pd.read_csv(RUNS / "e5" / "race.csv")
    rows = []
    for (f, d, w), g in t.groupby(["f", "delay_s", "window"], sort=False):
        row = {"f": f"{f:.3g}", "Δ": f"{int(d)} s", "window": f"{int(w)}"}
        for a, ga in g.groupby("alpha", sort=False):
            row[f"α = {a:.2f}"] = _depths(ga, 60, ga.layers_per_slot.mean(), (1e-3,))
        rows.append(row)
    print(md(pd.DataFrame(rows)))


def b5sweep() -> None:
    t = pd.read_csv(RUNS / "b5" / "recovery_sweep.csv")

    def days(v):
        if np.isinf(v):
            return "≥ 3650"
        if v < 1 / 24:
            return "< 1 h"
        return f"{v * 24:.0f} h" if v < 2 else f"{v:.0f}"
    for c in (1.0, 0.1):
        sub = t[(t.model == "random, specification") & (t.window_h == 4) & (t.c == c)]
        out = pd.DataFrame({"turnover per day": [f"{x * 100:g} %" for x in sub.tau_per_day.unique()]})
        for a in sub.alpha.unique():
            col = sub[sub.alpha == a].set_index("tau_per_day")["h_days_1e-09"]
            out[f"α = {a:.2f}"] = [days(col.loc[x]) for x in sub.tau_per_day.unique()]
        print(md(out))
        print()
    sub = t[(t.model == "random, specification") & (t.alpha == 0.25) & (t.c == 1.0)]
    out = pd.DataFrame({"turnover per day": [f"{x * 100:g} %" for x in sub.tau_per_day.unique()]})
    for w in sub.window_h.unique():
        col = sub[sub.window_h == w].set_index("tau_per_day")["h_days_1e-09"]
        out[f"{w} h window"] = [days(col.loc[x]) for x in sub.tau_per_day.unique()]
    print(md(out))


def e5balance() -> None:
    t = pd.read_csv(RUNS / "e5" / "balance.csv")
    out = pd.DataFrame({"f_A": [f"{f:.3g}" for f in t.f.unique()]})
    for d in t.delay_s.unique():
        sub = t[t.delay_s == d].set_index("f")
        out[f"Δ = {d} s"] = [f"{sub.loc[f, 'dag_adversarial_ties']:.3f} / "
                             f"{sub.loc[f, 'dag_fixed_ties']:.3f} / {sub.loc[f, 'chain']:.3f}"
                             for f in t.f.unique()]
    print(md(out))
    print()
    h = pd.read_csv(RUNS / "e5" / "hold.csv")
    rows = []
    for (f, d), g in h.groupby(["f", "delay_s"], sort=False):
        row = {"f_A": f"{f:.3g}", "Δ": f"{int(d)} s"}
        for a, ga in g.groupby("alpha", sort=False):
            gh = ga.set_index("hours").held
            row[f"α = {a:.2f}"] = f"{gh.loc[1]:.2f} / {gh.loc[24]:.2f}"
        rows.append(row)
    print(md(pd.DataFrame(rows)))


if __name__ == "__main__":
    {"a1": a1, "c1": c1, "c1settle": c1settle, "c3": c3, "c4": c4, "b3": b3, "b3delay": b3delay, "b2": b2, "b4": b4, "b5": b5,
     "b5rec": b5rec, "b5sweep": b5sweep, "b5part": b5part, "b6": b6, "b7": b7, "d0": d0, "d1b": d1b, "d3": d3, "d5": d5, "d6": d6,
     "e2": e2, "e5": e5, "e5balance": e5balance, "g1": g1, "g3": g3, "g4": g4, "g6": g6,
     "g7": g7, "h1": h1, "h2": h2, "h3": h3}[sys.argv[1]]()
