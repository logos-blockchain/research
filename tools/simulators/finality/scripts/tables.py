"""Markdown tables for the study's notes, read straight from runs/ (no hand transcription).

    python scripts/tables.py a1 | c1 | c1settle | c3 | c4 | b3 | b3delay | b2 | b5 | b5rec | b5sweep |
                             d0 | d6 | e2 | e5 | e5balance
"""

from __future__ import annotations

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
    for a in (0.10, 0.25):
        p = t[(t.alpha == a) & (t.eps == 1e-9)].pivot_table(
            index=["hops", "delta_max"], columns="interval", values="minutes")
        p = p[sorted(p.columns, reverse=True)].round(0).astype(int).reset_index()
        p["hops"] = p["hops"].astype(int)
        p["delta_max"] = p["delta_max"].astype(int)
        p.columns = ["hops", "Δ_max"] + [f"{int(c)} s" for c in p.columns[2:]]
        print(f"α = {a}, ε = 1e-9\n")
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
        first = 20                                   # the first computed depth (B2 DEPTHS)

        def show(v, extra):
            if v <= first:
                return f"≤ {first}"
            return f"{v:.0f}{'*' if extra else ''}"

        t["cell"] = t.apply(lambda r: f"{show(r.lb_depth, r.lb_extrapolated)} – "
                                      f"{show(r.ub_depth, r.ub_extrapolated)}", axis=1)
        p = t.pivot(index="adv", columns="delay_s", values="cell").reset_index()
        p["adv"] = p["adv"].map(lambda v: f"{v:.2f}")
        p.columns = ["α"] + [f"{int(c)} s" for c in p.columns[1:]]
        print(f"ε = {eps:.0e}\n")
        print(md(p))
        print()


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

    def cell(v):
        try:
            return f"{float(v):.3f}"
        except ValueError:
            return str(v).replace(">=", "≥")
    for c in ks:
        t[c.replace("k=", "k = ") if c == ks[0] else c[2:]] = w[c].map(cell).values
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


def d0() -> None:
    m = pd.read_csv(RUNS / "d0" / "emission_map.csv")
    d = m[(m.awake == 1.0) & (m.eps == 1e-9)]
    t = pd.DataFrame({"α": d.alpha, "seats": d.seats.map(lambda v: f"{v:,.0f}"),
                      **{f"{r} s": d[f"x_R{r}"].map(lambda v: f"×{v:,.0f}")
                         for r in (90, 600, 3600)}})
    print(md(t))
    print()
    d = m[m.eps == 1e-9].pivot(index="alpha", columns="awake", values="seats")
    t = pd.DataFrame({"α": d.index.map(lambda v: f"{v:.2f}")})
    for awake, name in ((1.0, "all honest seats vote"), (0.9, "90 % vote"), (0.8, "80 % vote")):
        t[name] = [("none" if np.isnan(v) else f"{v:,.0f}") for v in d[awake]]
    print(md(t))


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
    for (f, d), g in t.groupby(["f", "delay_s"], sort=False):
        row = {"f": f"{f:.3g}", "Δ": f"{int(d)} s", "s per layer":
               f"{1 / g.layers_per_slot.mean():.1f}"}
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
    {"a1": a1, "c1": c1, "c1settle": c1settle, "c3": c3, "c4": c4, "b3": b3, "b3delay": b3delay, "b2": b2, "b5": b5,
     "b5rec": b5rec, "b5sweep": b5sweep, "d0": d0, "d6": d6,
     "e2": e2, "e5": e5, "e5balance": e5balance}[sys.argv[1]]()
