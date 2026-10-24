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


def a1release() -> None:
    t = pd.read_csv(RUNS / "a1" / "release.csv")
    rel = {False: "at the slot", True: "at the next round"}
    seeds = {"everyone producing, A1's seeds, 8 runs": "A1's, its row", "everyone producing, A1's seeds, 32 runs": "A1's",
             "everyone producing": "paired"}
    rows = []
    for (setting, nr), g in t[t.setting.isin(seeds)].groupby(["setting", "next_round"], sort=False):
        x = g.iloc[0]
        rows.append({"seeds": seeds[setting], "runs": int(x.runs), "released": rel[bool(nr)],
                     "orphan share ± sem": f"{x.orphan:.3f} ± {x.orphan_sem:.3f}",
                     "growth / f ± sem": f"{x.growth:.3f} ± {x.growth_sem:.3f}",
                     "change, run by run": f"{x.growth_change:+.4f} ± {x.growth_change_sem:.4f}" if nr else "–",
                     "depth at 1e-9: 25 % / 30 % / a third": " / ".join(f"{d:,.0f}" for d in g.depth_1e9)})
    print(md(pd.DataFrame(rows)))
    print()
    w = t[t.setting == "coalition withholding"]
    rows = []
    for (c, a), g in w.groupby(["copies", "alpha"], sort=False):
        s, n = g[~g.next_round.astype(bool)].iloc[0], g[g.next_round.astype(bool)].iloc[0]
        rows.append({"α": f"{a:.2f}", "copies": int(c), "runs": int(s.runs),
                     "orphans: at the slot / next round": f"{s.orphan:.3f} / {n.orphan:.3f}",
                     "growth / win: at the slot / next round": f"{s.growth:.3f} / {n.growth:.3f}",
                     "change, run by run": f"{n.growth_change:+.4f} ± {n.growth_change_sem:.4f}",
                     "depth at 1e-9": f"{s.depth_1e9:,.0f} / {n.depth_1e9:,.0f} (+{n.depth_1e9 / s.depth_1e9 - 1:.0%})"})
    print(md(pd.DataFrame(rows)))


def a1conv() -> None:
    t = pd.read_csv(RUNS / "a1" / "convention.csv")
    rows = []
    for (setting, n), g in t.groupby(["setting", "runs"], sort=False):
        x = g.iloc[0]
        row = {"setting": setting, "runs": int(n), "orphan share ± sem": f"{x.orphan:.3f} ± {x.orphan_sem:.3f}",
               "growth / f ± sem": f"{x.growth_per_f:.3f} ± {x.growth_per_f_sem:.3f}",
               "growth / win": f"{x.growth_per_win:.3f}"}
        for a, label in ((0.3, "30 %"), (0.3333, "a third")):
            y = g[(g.alpha - a).abs() < 1e-3].iloc[0]
            row[f"depth at 1e-9, {label}: per f / exact / per win"] = (
                f"{y.depth_per_f:,.0f} / {y.depth_exact:,.0f} / {y.depth_per_win:,.0f}")
        rows.append(row)
    print(md(pd.DataFrame(rows)))


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
    t = pd.read_csv(RUNS / "g1" / "open.csv")

    def share(v, n):
        if n and v == 0:
            return f"< {1 / n:.0e}"
        return f"{v:.2g}" if v >= 1e-3 else f"{v:.0e}"
    rows = []
    for (model, a), g in t.groupby(["model", "alpha"], sort=False):
        row = {"delay": model, "α": f"{a:.2f}"}
        for _, x in g.iterrows():
            row[f"{int(x.minutes)} min"] = share(x.p_open, int(x.windows))
        rows.append(row)
    print(md(pd.DataFrame(rows)))
    print()
    f = pd.read_csv(RUNS / "g1" / "factor.csv")
    rows = []
    for _, x in f.iterrows():
        row = {"delay": x.model, "α": f"{x.alpha:.2f}", "k": f"{x.k}", "not ground": f"{x['depth_1e-09']:,.0f}",
               "B7's estimate": (f"{x.depth_two_lo:,.0f}" if x.depth_two_lo == x.depth_two_hi
                                 else f"{x.depth_two_lo:,.0f}–{x.depth_two_hi:,.0f}"),
               "at the cut-off": f"{x.g_min:.3f}, {x.depth_g_min:,.0f}"}
        for m in (5, 10, 20, 30):
            row[f"margin {m} min"] = f"{x[f'factor_{m}']:.3f}, {x[f'depth_{m}']:,.0f}"
        rows.append(row)
    print(md(pd.DataFrame(rows)))
    print()
    print(md(pd.DataFrame({
        "delay": f.model, "α": f.alpha.map(lambda v: f"{v:.2f}"), "k": f.k.map(str),
        "every value formed at the sub-window's start, 10 min": [f"{a:.3f}, {b:,.0f}" for a, b in
                                                               zip(f.open_factor_10, f.depth_open_10)]})))
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
    rows, factors = [], []
    for (h, r), g in t.groupby(["hops", "rounds"], sort=False):
        x = g.iloc[0]
        row = {"hops": f"{h}", "rounds": f"{r}", "p99 delay": f"{x.p99_s:.1f} s", "Δ": f"{x.delta_s} s",
               "orphans": f"{x.orphan:.2f}", "growth / f": f"{x.growth:.3f}",
               "path captured": f"{x.capture:.3f}", "blending": f"{x.blending:.2f}"}
        frow = {"hops": f"{h}", "rounds": f"{r}"}
        for _, y in g.iterrows():
            a = f"{y.alpha:.2f}"
            row[f"random, {a}"] = cell(y.random_depth, y.random_h, y.random_ground_depth, y.random_ground_h)
            row[f"worst, {a}"] = cell(y.worst_depth, y.worst_h, y.worst_ground_depth, y.worst_ground_h)
            frow[f"random, {a}"] = f"{y.g_min_random:.3g}" + (f", {y.deep_random:.1%} deeper"
                                                              if y.deep_random >= 1e-3 else "")
            frow[f"worst, {a}"] = "–" if np.isinf(y.worst_depth) else f"{y.g_min_worst:.3g}"
        rows.append(row)
        factors.append(frow)
    print(md(pd.DataFrame(rows)))
    print()
    print(md(pd.DataFrame(factors)))


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
    labels = {(False, "hold"): "honest", (True, "hold"): "hostile, holding",
              (True, "deadline"): "hostile, holding to the deadline", (True, "drop"): "hostile, dropping"}
    rows = []
    for _, x in t.iterrows():
        drop = x.hostile and x.action == "drop"
        rows.append({"α": f"{x.alpha:.2f}", "relays": labels[(bool(x.hostile), x.action)],
                     "copies": int(x.copies), "coalition's share of relays": f"{x.node_share:.3f}",
                     "orphans ± sem": f"{x.orphan:.3f} ± {x.orphan_sem:.3f}",
                     "blocks by the fallback, orphaned": f"{x.fallback:.3f}, {x.fallback_orphan:.2f}" if drop else "–",
                     "growth / win": f"{x.growth:.3f}", "race depth at 1e-3": f"{x.race_depth_1e3}",
                     "closed form at 1e-9": f"{x.closed_depth_1e9:,.0f} ({x.hours_1e9:.1f} h)"})
    print(md(pd.DataFrame(rows)))
    print()
    rows = []
    for _, x in t[t.hostile & (t.action == "drop")].iterrows():
        rows.append({"α": f"{x.alpha:.2f}", "copies": int(x.copies), "blocks by the fallback": f"{x.fallback:.3f}",
                     "honest nodes exposed in a run's epoch: engine, Poisson": f"{x.exposed_run:.3f}, {x.exposed_run_poisson:.3f}",
                     "in an epoch at k = 2160": f"{x.exposed_epoch_2160:.6f}"})
    print(md(pd.DataFrame(rows)))


def g7() -> None:
    t = pd.read_csv(RUNS / "g7" / "inference.csv")
    print(md(pd.DataFrame({
        "α": t.alpha.map(lambda v: f"{v:.2f}"), "raise": t.raise_factor.map(lambda v: f"{v:.2f}"),
        "Δ = 10 s reads as": t.delay_eq_s.map(lambda v: f"{v:.1f} s"),
        "B2's depth at 1e-9": [f"{int(b):,} → {int(d):,} ({h:.1f} h)" for b, d, h in zip(t.worst_depth_base, t.worst_depth, t.worst_hours)],
        "B5's closed form at 1e-9, A1's growth": [f"{int(d):,} ({b:.1f} → {h:.1f} h)" for d, b, h in zip(t.random_depth, t.random_hours_base, t.random_hours)],
        "k = 2160, random delay / worst case": [f"{rb:.1f} → {r:.1f} h / {wb:.1f} → {w:.1f} h" for rb, r, wb, w in
                                                zip(t.k_hours_random_base, t.k_hours_random, t.k_hours_worst_base, t.k_hours_worst)],
        "extra wins an epoch": t.extra_wins.map(lambda v: f"{v:,.0f}"),
        "selection, Brownian / played": [f"{b:.0f} / {m:.0f} ({s:.2%} of its wins)" for b, m, s in zip(t.excess_brownian, t.excess_mc, t.excess_share)]})))
    print()
    e = pd.read_csv(RUNS / "g7" / "engine.csv")
    one = e[(e.copies == 1) & ~e.next_round.astype(bool)].reset_index(drop=True)
    two = e[(e.copies == 2) & e.next_round.astype(bool)].reset_index(drop=True)
    depth = lambda v: f"{v}" if v > 0 else "–"
    print(md(pd.DataFrame({
        "α": one.alpha.map(lambda v: f"{v:.2f}"), "arm": one.arm,
        "orphans": [f"{a:.3f} / {b:.3f}" for a, b in zip(one.orphan, two.orphan)],
        "growth / win ± sem": [f"{a:.3f} ± {s:.3f} / {b:.3f} ± {t:.3f}" for a, s, b, t in
                               zip(one.growth, one.growth_sem, two.growth, two.growth_sem)],
        "race depth at 1e-3": [f"{depth(a)} / {depth(b)}" for a, b in zip(one.race_depth_1e3, two.race_depth_1e3)],
        "closed form at 1e-9": [f"{a:,.0f} ({h:.1f} h) / {b:,.0f} ({i:.1f} h)" for a, h, b, i in
                                zip(one.closed_depth_1e9, one.hours_1e9, two.closed_depth_1e9, two.hours_1e9)]})))
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
    tags = {"every vote": "seats, every honest vote counts", "a tenth": "a tenth of honest votes lost",
            "dropping relays, one copy": "relays at α dropping, one copy",
            "dropping relays, two copies": "two copies"}
    for a, g in s.groupby("alpha", sort=False):
        row = {"α": f"{a:.2f}", "honest side": f"{g.honest_side.iloc[0]:.3f}"}
        for _, x in g.iterrows():
            seats = "none" if x.seats < 0 else f"{int(x.seats):,} (θ = {int(x.threshold):,})"
            row[tags[x.case]] = seats if x.case in ("every vote", "a tenth") else f"{x.undelivered:.0%} lost: {seats}"
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
    bd = pd.read_csv(RUNS / "h2" / "binding.csv")
    print(md(pd.DataFrame({
        "delay": bd.model, "α": bd.alpha.map(lambda v: f"{v:.2f}"), "k": bd.k.map(lambda v: f"{v:,}"),
        "one per win": [f"{m:.3f} ± {e:.3f}" for m, e in zip(bd.per_win, bd.per_win_sem)],
        "one per parent": [f"{m:.3f} ± {e:.3f}" for m, e in zip(bd.per_parent, bd.per_parent_sem)],
        "one per chain prefix": [f"{m:.1f} ± {e:.1f}" for m, e in zip(bd.per_prefix, bd.per_prefix_sem)],
        "windows left out": [f"{int(s)}" for s in bd.skipped]})))
    print()
    fm = pd.read_csv(RUNS / "h2" / "formation.csv")
    rows = []
    for (model, a, k), g in fm.groupby(["model", "alpha", "k"], sort=False):
        g = g.set_index("margin")

        def pair(col, fmt="{:.3f}"):
            return " / ".join(fmt.format(g.loc[m, col]) for m in (10, 20))
        rows.append({"delay": model, "α": f"{a:.2f}", "k": f"{k:,}", "open": pair("open", "{:.2f}"),
                     "every value at the start": pair("open_factor"), "per win": pair("per_win"),
                     "parent's win tag": " / ".join(f"{g.loc[m, 'tag_lo']:.3f}–{g.loc[m, 'tag']:.3f}" for m in (10, 20)),
                     "parent's contribution": pair("chained", "{:.4f}")})
    print(md(pd.DataFrame(rows)))
    print()
    rows = []
    for _, x in fm[fm.margin == 10].iterrows():
        seen = f"{x.multi:.1e}" if x.multi_seen else f"< {1 / x.windows:.0e}"
        rows.append({"delay": x.model, "α": f"{x.alpha:.2f}", "k": f"{x.k:,}", "branches seen": seen,
                     "the walk's bound": f"{x.multi_bound:.1e}",
                     "blind switch, sampled / bound": f"{x.blind_chained:.1e} / {x.blind_bound:.1e}",
                     "depth, one evaluator, sampled": f"{x['depth_1e-09']:,.0f} → {x.depth_chained:,.0f}",
                     "depth, one evaluator, bound": f"{x.depth_bound:,.0f}",
                     "evaluators within k, bound": ("none" if x.largest_evaluators_bound == 0 else
                                                    f"{x.largest_evaluators_bound:.1e}")})
    print(md(pd.DataFrame(rows)))
    print()
    sw = pd.read_csv(RUNS / "h2" / "margin.csv")
    rows = []
    for (model, a), g in sw.groupby(["model", "alpha"], sort=False):
        row = {"delay": model, "α": f"{a:.2f}", "not ground": f"{g['depth_1e-09'].iloc[0]:,.0f}"}
        for _, x in g.sort_values("margin").iterrows():
            row[f"margin {int(x.margin)} min"] = f"{x.chained:.4f}, {x.depth_chained:,.0f}"
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
        "bound": gm.bound.map(lambda v: f"{v:.3f}"), "of which crossing": gm.cross.map(lambda v: f"{v:.3f}"),
        "E[D]": gm.e_d.map(lambda v: f"{v:.1f}"), "E[A]": gm.e_a.map(lambda v: f"{v:.1f}"),
        "depth with two nonces, sampled → bound": [f"{int(s):,} → {int(b):,}" for s, b in zip(gm.depth_two_sampled, gm.depth_two)]})))


def h3() -> None:
    c = pd.read_csv(RUNS / "h3" / "counting.csv")
    rows = []
    for _, x in c.iterrows():
        row = {"α": f"{x.alpha:.2f}", "catch-up ratio": f"{x.ratio:.2f}"}
        for name, label in (("full", "full rate"), ("withheld", "withheld from"), ("worst", "worst-case rate")):
            d, hrs = x[f"depth_{name}"], x[f"hours_{name}"]
            row[f"depth at 1e-9, {label}"] = f"{int(d):,} ({hrs:.1f} h)" if d > 0 else "–"
        row["mean of 2A + H over 2n, withheld from"] = f"{x.mean_withheld:.2f}"
        row["at the worst-case rate"] = f"{x.mean_worst:.2f}"
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
        "attack wins at acceptance": p.fail_at_acceptance.map(rate), "ever": p.fail_ever.map(rate),
        "at acceptance, per target": (p.fail_at_acceptance * p.accepted_share).map(rate)})))
    print()
    pl = pd.read_csv(RUNS / "h3" / "played.csv")
    print(md(pd.DataFrame({
        "α": pl.alpha.map(lambda v: f"{v:.2f}"), "targets accepted": pl.accepted.map(lambda v: f"{v:,}"),
        "mean depth at acceptance": pl.mean_depth.map(lambda v: f"{v:.1f}"),
        "minutes": pl.mean_minutes.map(lambda v: f"{v:.0f}"),
        "the race beats the rule": pl.race_beats.map(lambda v: f"{v:.1e}" if v > 0 else "0"),
        "wins B5's closed form expects": pl.expected.map(lambda v: f"{v:.1e}")})))
    print()
    ob = pd.read_csv(RUNS / "h3" / "observed.csv")

    def depth(v):
        return f"{int(v):,}" if v > 0 else "–"

    def timed(d, h):
        return f"{depth(d)} ({h:.1f} h)" if d > 0 else "–"
    print(md(pd.DataFrame({
        "α": ob.alpha.map(lambda v: f"{v:.2f}"),
        "B2, worst case": [timed(d, h) for d, h in zip(ob.b2_depth, ob.b2_hours_withheld)],
        "B5, random delay": ob.closed_depth.map(depth),
        "full rate": ob.full_0.map(depth),
        "withheld from": [timed(d, h) for d, h in zip(ob.withheld_0, ob.hours_withheld_0)],
        "withheld from, at 5e-10": ob.withheld_0_half.map(depth),
        "withheld from, ties to the coalition": ob.withheld_0_ties.map(depth),
        "worst-case rate": [timed(d, h) for d, h in zip(ob.worst_0, ob.hours_worst_0)]})))
    print()
    wk = pd.read_csv(RUNS / "h3" / "walk.csv")
    print(md(pd.DataFrame({
        "α": wk.alpha.map(lambda v: f"{v:.2f}"),
        "mean gain a block, the rule's law / the walk / with a second leader":
            [f"{r:.3f} / {w:.3f} / {w2:.3f}" for r, w, w2 in zip(wk.ratio, wk.walk_mean, wk.walk2_mean)],
        "tail factor a block": [f"{r:.3f} / {w:.3f} / {w2:.3f}"
                                for r, w, w2 in zip(wk.ratio, wk.walk_decay, wk.walk2_decay)],
        "P(L ≥ 100)": [f"{r:.1e} / {w:.1e} / {w2:.1e}"
                       for r, w, w2 in zip(wk.rule_lead100, wk.walk_lead100, wk.walk2_lead100)],
        "depth at 1e-9, the client's ties": [f"{r} / {w} / {w2}" for r, w, w2 in zip(wk.rule, wk.walk, wk.walk2)],
        "ties to the coalition": [f"{r} / {w} / {w2}"
                                  for r, w, w2 in zip(wk.rule_ties, wk.walk_ties, wk.walk2_ties)]})))
    print()
    ad = pd.read_csv(RUNS / "h3" / "adaptive.csv")

    def times(v):
        return f"{v:.2g} ε" if v < 0.1 else f"{v:.2f} ε"
    print(md(pd.DataFrame({
        "α": ad.alpha.map(lambda v: f"{v:.2f}"), "ε": ad.eps.map(lambda v: f"{v:.0e}"),
        "law": ad.law.map({"bound": "the rule's", "renewal": "the worst-case walk"}),
        "every win private": ad.own.map(times), "induction": ad.induction.map(times),
        "free timing": ad.free_timing.map(times), "upper bound": ad.upper_bound.map(times)})))
    print()
    vw = pd.read_csv(RUNS / "h3" / "views.csv")
    print(md(pd.DataFrame({
        "α": vw.alpha.map(lambda v: f"{v:.2f}"), "ε": vw.eps.map(lambda v: f"{v:.0e}"),
        "likeliest view above ε": [f"{n} blocks in {t:,} slots, {c} of them the coalition's"
                                   for n, t, c in zip(vw.n, vw.t, vw.coalition)],
        "fails given the view": vw.risk.map(lambda v: f"{v:.1e}"),
        "the rule's bound there": vw.bound.map(lambda v: f"{v:.1e}"),
        "the view's chance": vw.chance.map(lambda v: f"{v:.0e}"),
        "of chance 1e-12 or more, the view that fails most often":
            [f"{n} in {t:,}, {c} the coalition's: {r:.1e} against {b:.1e}" if n > 0 else "none"
             for n, t, c, r, b in zip(vw.worst_n, vw.worst_t, vw.worst_coalition, vw.worst_risk, vw.worst_bound)],
        "all views above ε": vw.above.map(lambda v: f"{v:.0e}"),
        "most honest blocks in one": vw.worst_honest,
        "the play per target": vw.per_target.map(lambda v: f"{v:.0e}")})))
    print()
    po2 = pd.read_csv(RUNS / "h3" / "precheck_observed.csv")
    print(md(pd.DataFrame({
        "α": po2.alpha.map(lambda v: f"{v:.2f}"), "forks counted": po2.forks,
        "targets": po2.targets.map(lambda v: f"{v:,}"), "accepted": po2.accepted.map(lambda v: f"{v:,}"),
        "attack wins at acceptance, per target": po2.fail_per_target.map(rate),
        "per accepted target": po2.fail_per_acceptance.map(lambda v: "–" if v != v else rate(v)),
        "mean depth at acceptance": po2.mean_depth.map(lambda v: "–" if v != v else f"{v:.1f}"),
        "mean forks at acceptance": po2.mean_forks.map(lambda v: "–" if v != v else f"{v:.1f}")})))
    print()
    print(md(pd.DataFrame({
        "α": ob.alpha.map(lambda v: f"{v:.2f}"),
        "no forks, withheld from": ob.withheld_0.map(depth),
        "two forks": ob.withheld_2.map(depth), "four forks": ob.withheld_4.map(depth),
        "a balancing coalition, its honest forks": ob.balancing.map(depth),
        "with its own blocks": ob.balancing_own.map(depth),
        "a coalition publishing every win as a fork": ob.publishing.map(depth)})))
    print()
    cp = pd.read_csv(RUNS / "h3" / "copies.csv")
    print(md(pd.DataFrame({
        "α": cp.alpha.map(lambda v: f"{v:.2f}"), "blocks signed a win": cp.copies,
        "depth at 1e-9, forks counted as blocks": cp.blocks.map(depth),
        "as slots": cp.slots.map(depth)})))
    print()
    fk = pd.read_csv(RUNS / "h3" / "forks.csv")
    print(md(pd.DataFrame({
        "α": fk.alpha.map(lambda v: f"{v:.2f}"), "targets": fk.targets.map(lambda v: f"{v:,}"),
        "none": fk.none.map(lambda v: f"{v:.3f}"), "two or more": fk.two_or_more.map(lambda v: f"{v:.3f}"),
        "mean": fk["mean"].map(lambda v: f"{v:.3f}"),
        "90th percentile": fk.p90.map(lambda v: f"{v:.0f}"), "99th percentile": fk.p99.map(lambda v: f"{v:.0f}"),
        "most": fk.most,
        "a fork reaches the client, slots after its slot: 99th percentile": fk.late_p99.map(lambda v: f"{v:.1f}"),
        "latest": fk.late_most.map(lambda v: f"{v:.1f}"),
        "accepted with a fork still in flight": fk.in_flight})))
    print()
    po = pd.read_csv(RUNS / "h3" / "played_observed.csv")
    print(md(pd.DataFrame({
        "α": po.alpha.map(lambda v: f"{v:.2f}"), "timelines": po.timelines,
        "targets": po.targets.map(lambda v: f"{v:,}"),
        "accepted": [f"{a / t:.3f}" for a, t in zip(po.accepted, po.targets)],
        "mean depth at acceptance": po.mean_depth.map(lambda v: f"{v:.1f}"),
        "minutes": po.mean_minutes.map(lambda v: f"{v:.0f}"),
        "the race beats the rule": po.race_beats.map(lambda v: f"{v:.1e}" if v > 0 else "0"),
        "wins B5's closed form expects": po.expected.map(lambda v: f"{v:.1e}")})))


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


def i2() -> None:
    t = pd.read_csv(RUNS / "i2" / "discriminant.csv")
    print(md(pd.DataFrame({
        "discriminant": t.bits.map(lambda v: f"{int(v):,} bits"),
        "RSA modulus of Table 4": t.rsa.map(lambda v: f"{int(v):,} bits" if v == v else "–"),
        "discrete log, Table 4's rows": t.dl_rows.map(lambda v: f"2^{v:.1f}"),
        "discrete log, stated method": t.dl_stated.map(lambda v: f"2^{v:.1f}"),
        "class group, stated method": [f"2^{a:.1f}–2^{b:.1f}" for a, b in zip(t.cl_stated_lo, t.cl_stated_hi)],
        "years at 10^18 a second": [f"{a:.3g} / {b:.3g}" for a, b in zip(t.years_1e18_rows, t.years_1e18_stated)],
        "operations a second within 4.49 h": [f"{a:.1e} / {b:.1e}" for a, b in
                                              zip(t.ops_within_delay_rows, t.ops_within_delay_stated)]})))


def b5eng() -> None:
    t = pd.read_csv(RUNS / "b5" / "partition_engine.csv")
    rows = []
    for _, x in t.iterrows():
        if x.alpha > 0:
            rows.append({"α": f"{x.alpha:.2f}", "side set": f"{x.side:.2f}", "side held": f"{x.share_small:.3f}",
                         "density: side / fork": f"{x.density_small:,.0f} / {x.fork:,.0f}",
                         "growth per occupied slot: side, rest, A1": f"{x.growth_small:.3f}, {x.growth_other:.3f}, {x.growth_a1:.3f}",
                         "fork denser, engine ± sem": f"{x.beaten:.3f} ± {x.beaten_sem:.3f}",
                         "closed form at A1's growth (z)": f"{x.closed_form:.3f} ({x.z_a1:+.1f})",
                         "closed form at the side's growth (z)": f"{x.closed_form_side_growth:.3f} ({x.z_side:+.1f})",
                         "chain longer at rejoin: side, rest": f"{x.small_longer:.3f}, {x.other_longer:.3f}"})
    print(md(pd.DataFrame(rows)))
    print()
    v = pd.read_csv(RUNS / "b5" / "partition_engine_variants.csv")
    print(md(pd.DataFrame([{"sides": f"{x.share_small:.3f} / {x.share_other:.3f}", "copies": int(x.copies),
                            "runs": int(x.runs), "density tie, engine": f"{x.density_tie:.4f}",
                            "equal length at rejoin": f"{x.equal_length:.4f}",
                            "growth per occupied slot: a, b, A1": f"{x.growth_small:.3f}, {x.growth_other:.3f}, {x.growth_a1:.3f}"}
                           for _, x in v[v.alpha == 0].iterrows()])))
    print()
    rows = []
    for (a, sd), g in v[v.alpha > 0].groupby(["alpha", "side"], sort=False):
        r = {"α": f"{a:.2f}", "side set": f"{sd:.2f}"}
        for where, copies, label in (("rest", 1, "with the rest, one copy"), ("side", 1, "beside the side, one copy"),
                                     ("rest", 2, "with the rest, two copies"), ("side", 2, "beside the side, two copies")):
            x = g[(g["adversary_side"] == where) & (g.copies == copies)].iloc[0]
            r[label] = f"{x.beaten:.3f} ± {x.beaten_sem:.3f}"
        rows.append(r)
    print(md(pd.DataFrame(rows)))
    print()
    even = v[(v.alpha.round(2) == 0.30) & (v.side.round(2) == 0.35)]
    print(md(pd.DataFrame([{"coalition's nodes": {"rest": "with the rest", "side": "beside the side"}[x["adversary_side"]],
                            "copies": int(x.copies), "longer at rejoin: side, rest": f"{x.small_longer:.3f}, {x.other_longer:.3f}",
                            "equal length": f"{x.equal_length:.3f}"} for _, x in even.iterrows()])))
    print()
    rows = []
    for a, g in t[t.alpha > 0].groupby("alpha", sort=False):
        rows.append({"α": f"{a:.2f}", "threshold over 36 h": f"{int(g.detector_threshold.iloc[0]):,}",
                     "sides held": ", ".join(f"{s:.2f}" for s in sorted(set(g.share_small.round(2)) | set(g.share_other.round(2)))),
                     "runs below it, engine": f"{min(g.detector_small.min(), g.detector_other.min()):.3f}",
                     "closed form, least": f"{min(g.detector_small_closed.min(), g.detector_other_closed.min()):.6f}"})
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


def j1() -> None:
    t = pd.read_csv(RUNS / "j1" / "circuit.csv")
    print(md(pd.DataFrame({
        "proof of leadership": t.variant,
        "constraints": t.constraints.map(lambda v: f"{v:,}"),
        "added": t.added.map(lambda v: f"{v:,}"),
        "share of today's": t.share.map(lambda v: f"{100 * v:.1f} %"),
        "public values": t.public,
        "domain": t.domain.map(lambda v: f"2^{int(v).bit_length() - 1}")})))


def j3() -> None:
    t = pd.read_csv(RUNS / "j3" / "regions.csv")
    t = t[t.f == t.f.min()]
    print(md(pd.DataFrame({
        "Δ": t.delay_s.map(lambda v: f"{v} s"),
        "convergence opportunities": t.convergence.map(lambda v: f"{v:.3f}"),
        "GHOST, ties steered": t.ghost_adversarial_ties.map(lambda v: f"{v:.3f}"),
        "GHOST, ties fixed": t.ghost_fixed_ties.map(lambda v: f"{v:.3f}"),
        "longest chain": t.chain.map(lambda v: f"{v:.3f}")})))
    print()
    print(md(pd.DataFrame({
        "Δ": t.delay_s.map(lambda v: f"{v} s"),
        "convergence opportunities, two events a win": t.convergence_two_events.map(
            lambda v: f"{v:.3f}"),
        "balance, ties steered": t.ghost_adversarial_ties_retraction.map(lambda v: f"{v:.3f}"),
        "balance, a fixed rule": t.ghost_fixed_ties_retraction.map(lambda v: f"{v:.3f}")})))


def j3bound() -> None:
    t = pd.read_csv(RUNS / "j3" / "bound.csv")

    def cell(r):
        if r.drift >= 0:
            return "none: the walk drifts up"
        if pd.isna(r.depth_slots):
            return "beyond 72 h"
        return f"{int(r.depth_slots):,} / {r.hours:.1f}"

    rows = []
    for (alpha, delay), g in t.groupby(["alpha", "delay_s"], sort=False):
        g = g.set_index("events")
        rows.append({"α": "a third" if abs(alpha - 1 / 3) < 1e-9 else f"{100 * alpha:g} %",
                     "Δ": f"{delay} s",
                     "two events a win (J.1): slots / hours": cell(g.loc[2]),
                     "one event a win: slots / hours": cell(g.loc[1])})
    print(md(pd.DataFrame(rows)))


def j2() -> None:
    t = pd.read_csv(RUNS / "j2" / "attack.csv")
    t["a"] = t.alpha.map(lambda v: "a third" if abs(v - 1 / 3) < 1e-9 else f"{100 * v:.0f} %")

    def hours(r, digits=1):
        if r.forever:
            return "none"
        return "> 72" if pd.isna(r.hours) else f"{r.hours:.{digits}f}"

    def pick(g, attack, ties):
        return g[(g.attack == attack) & (g.ties == ties)].iloc[0]

    tail = pd.read_csv(RUNS / "j2" / "tail.csv")
    rows = []
    for (a, d), g in tail.groupby(["alpha", "delay_s"], sort=False):
        row = {"α": "a third" if abs(a - 1 / 3) < 1e-9 else f"{100 * a:.0f} %", "Δ": f"{d} s"}
        for ties, name in (("steered", "ties steered"), ("fixed", "a fixed rule")):
            r = g[g.ties == ties].iloc[0]
            if r.forever:
                row[f"{name}: 1 h / 6 h / 24 h"] = "held for ever with positive chance"
                row[f"{name}: hours to 1e-9"] = "none"
            else:
                row[f"{name}: 1 h / 6 h / 24 h"] = " / ".join(
                    f"{r[f'hold_{h}h']:.1e}" if r[f"hold_{h}h"] > 0 else "< 1e-30"
                    for h in (1, 6, 24))
                row[f"{name}: hours to 1e-9"] = hours(r)
        rows.append(row)
    print(md(pd.DataFrame(rows)))
    print()
    rows = []
    for (a, d), g in t.groupby(["alpha", "delay_s"], sort=False):
        c = g.iloc[0]
        rows.append({"α": c.a, "Δ": f"{d} s",
                     "fixed rule": hours(pick(g, "combined", "fixed")),
                     "tie exploit": hours(pick(g, "combined, tie exploit", "fixed")),
                     "ties steered": hours(pick(g, "combined", "steered")),
                     "balance alone, fixed rule": hours(pick(g, "balance", "fixed")),
                     "private race": hours(pick(g, "private race", "fixed")),
                     "chain: attack": f"{c.chain_lower_hours:.1f}",
                     "chain: bound": f"{c.chain_upper_hours:.1f}"})
    print(md(pd.DataFrame(rows)))
    print()
    b2 = pd.read_csv(RUNS / "b2" / "depths.csv")
    b2 = b2[b2.eps == 1e-9]
    rows = []
    for (a, d), g in t[(t.alpha >= 0.3) & t.delay_s.isin([1, 10])].groupby(["alpha", "delay_s"],
                                                                              sort=False):
        r = pick(g, "combined", "fixed")
        star = b2[(b2.adv.round(4) == round(a, 4)) & (b2.delay_s == d)].iloc[0].lb_extrapolated
        lower = f"{math.floor(r.chain_lower_blocks + 1e-9)}{'*' if star else ''}"
        rows.append({"α": r.a, "Δ": f"{d} s", "slots": f"{r.depth_slots:,.0f}",
                     "hours": f"{r.hours:.2f}", "honest blocks": f"{r.honest_blocks:,.0f}",
                     "chain's attack: blocks / hours":
                         f"{lower} / {r.chain_lower_hours:.2f}",
                     "chain's bound: blocks / hours":
                         f"{r.chain_upper_blocks:,.0f} / {r.chain_upper_hours:.2f}"})
    print(md(pd.DataFrame(rows)))
    print()
    h = pd.read_csv(RUNS / "j2" / "h14.csv")
    print(md(pd.DataFrame({
        "attack, a fixed rule": h.attack.map({"combined": "combined",
                                              "combined, tie exploit": "with the tie exploit"}),
        "hours at 1 s": h.hours_1s.map(lambda v: f"{v:.2f}"),
        "hours at 10 s": h.hours_10s.map(lambda v: f"{v:.2f}"),
        "10 s over 1 s": h.ratio.map(lambda v: f"{v:.2f}"),
        "first part, below 1.25": h.part1_holds.map({True: "holds", False: "fails"}),
        "chain's attack at 10 s (hours)": h.chain_10s_hours.map(lambda v: f"{v:.2f}"),
        "second part, below it": h.part2_holds.map({True: "holds", False: "fails"})})))
    print()
    w = pd.read_csv(RUNS / "j2" / "window.csv")
    w = w[(w.alpha >= 0.3) & w.delay_s.isin([1, 10, 20])]
    print(md(pd.DataFrame({
        "α": w.alpha.map(lambda v: "a third" if abs(v - 1 / 3) < 1e-9 else f"{100 * v:.0f} %"),
        "Δ": w.delay_s.map(lambda v: f"{v} s"),
        "phases opening after a quiet stretch": w.stale_phases.map(lambda v: f"{100 * v:.2f} %"),
        "private wins after a gap": w.late_wins.map(lambda v: f"{100 * v:.1f} %")})))
    # retraction: two moves a win
    print()
    e = pd.read_csv(RUNS / "j2" / "edges.csv")
    rows = []
    for f, g in e.groupby("f", sort=False):
        row = {"f_A": f"{f:.4f}".rstrip("0") if f < 0.1 else f"{f:g}"}
        for _, x in g.iterrows():
            row[f"Δ = {int(x.delay_s)} s"] = (f"{x.retraction_steered:.3f} / "
                                              f"{x.retraction_fixed:.3f}")
        rows.append(row)
    print(md(pd.DataFrame(rows)))
    print()
    r = pd.read_csv(RUNS / "j2" / "retract.csv")
    r["a"] = r.alpha.map(lambda v: "a third" if abs(v - 1 / 3) < 1e-9 else f"{100 * v:.0f} %")

    def rh(g, attack, ties, count):
        x = g[(g.attack == attack) & (g.ties == ties) & (g["count"] == count)].iloc[0]
        if x.forever:
            return "none"
        return "> 72" if pd.isna(x.hours) else f"{x.hours:.1f}"

    def fixed_range(g, attack):
        best, relaxed = rh(g, attack, "fixed", "best switches"), rh(g, attack, "fixed", "relaxed")
        return best if best == relaxed else f"{best} – {relaxed}"

    rows = []
    for (a, dl), g in r.groupby(["alpha", "delay_s"], sort=False):
        one = t[(t.alpha == a) & (t.delay_s == dl)]
        rows.append({"α": g.iloc[0].a, "Δ": f"{dl} s",
                     "balance, ties steered": rh(g, "balance", "steered", "two moves"),
                     "balance, a fixed rule": fixed_range(g, "balance"),
                     "combined, ties steered": rh(g, "combined", "steered", "two moves"),
                     "combined, a fixed rule": fixed_range(g, "combined"),
                     "tie exploit": fixed_range(g, "combined, tie exploit"),
                     "one move, a fixed rule": hours(pick(one, "combined", "fixed")),
                     "chain: attack": f"{g.iloc[0].chain_lower_hours:.1f}"})
    print(md(pd.DataFrame(rows)))
    print()
    h = pd.read_csv(RUNS / "j2" / "h14_retract.csv")

    def hh(v):
        return "none" if pd.isna(v) else f"{v:.2f}"
    print(md(pd.DataFrame({
        "attack": h.attack.map({"combined": "combined",
                                "combined, tie exploit": "with the tie exploit"}),
        "ties, count": [f"{'ties steered' if ti == 'steered' else 'a fixed rule'}, {c}"
                        for ti, c in zip(h.ties, h["count"])],
        "hours at 1 s": h.hours_1s.map(hh), "hours at 10 s": h.hours_10s.map(hh),
        "first part": h.part1_holds.map({True: "holds", False: "fails"}),
        "chain's attack at 10 s (hours)": h.chain_10s_hours.map(lambda v: f"{v:.2f}"),
        "below it": h.part2_holds.map({True: "yes", False: "no"})})))


def _phase_k(name: str):
    """Phase K's tables live in tables_k1.py, tables_k3.py, tables_k5.py, tables_k7.py,
    tables_k8.py and tables_k9.py, one per part."""
    import importlib
    for mod in ("tables_k1", "tables_k3", "tables_k5", "tables_k7", "tables_k8", "tables_k9"):
        try:
            m = importlib.import_module(mod)
        except ModuleNotFoundError:
            continue
        if hasattr(m, name):
            return getattr(m, name)
    raise KeyError(name)


if __name__ == "__main__":
    if sys.argv[1].startswith("k"):
        _phase_k(sys.argv[1])()
        raise SystemExit
    {"j1": j1, "j2": j2, "j3": j3, "j3bound": j3bound,"a1": a1, "c1": c1, "c1settle": c1settle, "c3": c3, "c4": c4, "b3": b3, "b3delay": b3delay, "b2": b2, "b4": b4, "b5": b5,
     "b5rec": b5rec, "b5sweep": b5sweep, "b5part": b5part, "b6": b6, "b7": b7, "d0": d0, "d1b": d1b, "d3": d3, "d5": d5, "d6": d6,
     "e2": e2, "e5": e5, "e5balance": e5balance, "g1": g1, "g3": g3, "g4": g4, "g6": g6,
     "g7": g7, "h1": h1, "h2": h2, "h3": h3, "b5eng": b5eng, "i2": i2, "a1release": a1release, "a1conv": a1conv}[sys.argv[1]]()
