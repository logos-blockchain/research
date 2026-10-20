"""Phase H.2: the delay function, the contribution's binding and the coalition's speed ratio (PLAN.md, H.2).

    python scripts/h2_delay.py [stage ...]   # needs runs/a1, runs/b2, runs/b7; writes runs/h2/*.csv

Stages, all by default and in this order: binding, gmin, formation (reads gmin.csv), margin, span.

A candidate nonce of the last sub-window can be formed from the sub-window's start, so the delay on
the coalition's hardware is T_a = W + margin, with W the sub-window (DESIGNS.md, H.2). Every table
is at 30 % and a third, for B6's two delay models.

binding.csv: per k, the distinct values the last sub-window's minimum can take at the cut-off with no
delay, over every feasible fork and subset of the coalition's wins (formation.binding_counts, 4,000
windows a cell): one contribution per win, per parent, per chain prefix; windows past 200,000 subsets
are left out of the means and counted.
gmin.csv: per model, share and k, the choices at the cut-off E[G_min]: B7's sampled mean; the mean
of the exact expectation given the slots (finality_sim.fork_bound.conditional_mean, 10,000 windows);
the bound from B6's walk alone (fork_bound.gmin_bound, the last sub-window's split and the previous
one's each chosen to make their terms smallest); E[D] and E[A] of the deepest feasible fork; and the
depth at 1e-9 with two nonces at the bound.
formation.csv: per k, at margins of 10 and 20 minutes, the values seen while reachable for each
binding of the contribution (formation.formation_counts, 100,000 windows a cell at k = 1620 and
1080, 50,000 at 2160): the chance a choice is open, the factor if every value were formed at the
sub-window's start, per win, bound to the parent's win tag (from below and above), and bound to the
parent's contribution, chained, with the share of windows in which a branch of two or more wins is
seen while it can still be published; the walk's bound on that share (formation.evaluator_bound);
the chance of a blind switch, sampled and bounded by the open chance after the margin averaged over
the sub-window (formation.open_curve, 100,000 windows; formation.blind_bound); the depth at 1e-9
with two nonces for the chained binding with one evaluator, sampled, and with the honest minima at
gmin.csv's bound and the blind switch at its bound; and the most delay evaluators the coalition can
run before that depth passes k, at the walk's bound on the branches.
margin.csv: at k = 2160, the chained binding's factor and depth at margins of 1 to 20 minutes.
span.csv: per k, the sub-windows m of B7, the sub-window W, T_a at margins of 10 and 20 minutes, the
honest computation R * T_a for speed ratios R of 3, 5, 10 and 15, the 4 floor(k/f) slots between the
cut-off and the first slot that uses the nonce, and the largest R whose squarings fit them.
"""

from __future__ import annotations

import math
import pathlib
import sys

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from b2_settlement import F
from b7_nonce import depth_reader, models
from finality_sim.fork_bound import conditional_mean, gmin_bound
from finality_sim.formation import (binding_counts, blind_bound, evaluator_bound, formation_counts,
                                    open_curve)
from finality_sim.nonce import _rates

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "h2"
ALPHAS = (0.30, 1 / 3)
KS = (2160, 1620, 1080)
MARGINS = (10, 20)
SWEEP = (1, 2, 5, 10, 20)
RATIOS = (3, 5, 10, 15)
FRACTIONS = (0.6, 0.65, 0.7, 0.75, 0.8, 0.85)
EPS = 1e-9
JOBS = 4


def largest_factor(at, k: int) -> float:
    """The largest factor per nonce, met twice, whose depth at 1e-9 stays within k blocks."""
    def depth(log_eps):
        try:
            return at(log_eps)
        except ValueError:                                             # past B2's computed depths
            return math.inf
    if depth(math.log(EPS)) > k:
        return 0.0
    lo, hi = 0.0, 40.0                                                 # log F
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if depth(math.log(EPS) - 2 * mid) <= k else (lo, mid)
    return math.exp(lo)


def binding(name: str, kw: dict, alpha: float, k: int, m: int, seed: int) -> dict:
    r = binding_counts(F, alpha, 6 * math.floor(k / F), m, 4_000, seed, **kw)
    row = dict(model=name, alpha=round(alpha, 4), k=k, crossed=r["crossed"], skipped=r["skipped"])
    for key in ("per_win", "per_parent", "per_prefix"):
        v = r[key]
        row[key], row[key + "_sem"], row[key + "_more"] = v.mean(), v.std() / math.sqrt(v.size), np.mean(v > 1)
    return row


def formation(name: str, kw: dict, alpha: float, k: int, m: int, seed: int) -> list[dict]:
    window = 6 * math.floor(k / F)
    n = 50_000 if k == 2160 else 100_000
    r = formation_counts(F, alpha, window, m, [60 * t for t in MARGINS], n, seed, **kw)
    rows = []
    for i, t in enumerate(MARGINS):
        b = evaluator_bound(F, alpha, window // m, 60 * t, **kw)
        row = dict(model=name, alpha=round(alpha, 4), k=k, margin=t, windows=n,
                   open=r["open"][:, i].mean(), crossing=r["cross"].mean())
        for key in ("open_factor", "per_win", "tag_lo", "tag", "chained", "blind_tag", "blind_chained"):
            row[key] = r[key][:, i].mean()
        row["multi"] = r["multi"][:, i].mean()
        row["multi_seen"] = int(r["multi"][:, i].sum())
        row |= dict(survive=b["survive"], inside=b["inside"], cross_law=b["cross"], multi_bound=b["bound"])
        rows.append(row)
    return rows


def sweep(name: str, kw: dict, alpha: float, m: int, seed: int) -> list[dict]:
    r = formation_counts(F, alpha, 6 * math.floor(2160 / F), m, [60 * t for t in SWEEP], 20_000, seed, level=1, **kw)
    return [dict(model=name, alpha=round(alpha, 4), margin=t, chained=r["chained"][:, i].mean(),
                 per_win=r["per_win"][:, i].mean(), open_factor=r["open_factor"][:, i].mean())
            for i, t in enumerate(SWEEP)]


def bound_cell(name: str, kw: dict, b7: pd.DataFrame, alpha: float, k: int) -> dict:
    m_k = int(b7[b7.k == k].sub_windows.iloc[0])
    window = 6 * math.floor(k / F)
    sub = window // m_k
    _, _, _, rate = _rates(F, alpha, kw.get("growth"), kw.get("delta"))
    bounds = [gmin_bound(F, alpha, sub, int(frac * sub * rate), **kw) for frac in FRACTIONS]
    stay = min(bounds, key=lambda b: b["bound"] - b["cross"])
    cross = min(bounds, key=lambda b: b["cross"])
    cond, _ = conditional_mean(F, alpha, window, 10_000, 211 + k + int(alpha * 1000), sub_windows=m_k, **kw)
    x = b7[(b7.model == name) & (b7.alpha == round(alpha, 4)) & (b7.k == k)].iloc[0]
    return dict(model=name, alpha=round(alpha, 4), k=k, sub_windows=m_k, sampled=float(x.mean_g),
                conditional=float(cond.mean()), conditional_sem=float(cond.std() / math.sqrt(cond.size)),
                bound=stay["bound"] - stay["cross"] + cross["cross"], main=stay["main"],
                tails=stay["tail_d"] + stay["tail_n"], cross=cross["cross"], e_d=stay["e_d"], e_a=stay["e_a"])


STAGES = ("binding", "gmin", "formation", "margin", "span")


def main(stages: tuple[str, ...] = STAGES) -> None:
    ms = {n: kw for n, (kw, _) in models().items() if n != "random, testnet"}
    b7 = pd.read_csv(HERE / "runs" / "b7" / "minimum.csv")
    m_of = {k: int(b7[b7.k == k].sub_windows.iloc[0]) for k in KS}
    ub = pd.read_parquet(HERE / "runs" / "b2" / "ub.parquet")
    log_ub = {(round(a, 4), int(d)): np.log(g.sort_values("depth").ub.to_numpy())
              for (a, d), g in ub.groupby(["adv", "delay_s"])}
    OUT.mkdir(parents=True, exist_ok=True)
    cells = [(n, a, k) for n in ms for a in ALPHAS for k in KS]

    if "binding" in stages:
        rows = Parallel(n_jobs=JOBS)(delayed(binding)(n, ms[n], a, k, m_of[k], 3 + k + int(a * 1000))
                                     for n, a, k in cells)
        bd = pd.DataFrame(rows)
        bd.to_csv(OUT / "binding.csv", index=False)
        with pd.option_context("display.width", 250, "display.max_columns", 30):
            print(bd.to_string(index=False, float_format=lambda v: f"{v:.4g}"))

    if "gmin" in stages:
        out = Parallel(n_jobs=JOBS)(delayed(bound_cell)(n, ms[n], b7, a, k) for n, a, k in cells)
        gm = pd.DataFrame(out)
        for i, r in gm.iterrows():
            at = depth_reader(ms[r.model], r.alpha, log_ub)
            gm.loc[i, "depth_two"] = at(math.log(EPS / r.bound ** 2))
            gm.loc[i, "depth_two_sampled"] = at(math.log(EPS / r.sampled ** 2))
        gm.to_csv(OUT / "gmin.csv", index=False)
        print()
        with pd.option_context("display.width", 220):
            print(gm.to_string(index=False, float_format=lambda v: f"{v:.4g}"))

    if "formation" in stages:
        gm = pd.read_csv(OUT / "gmin.csv")
        got = Parallel(n_jobs=JOBS)(delayed(formation)(n, ms[n], a, k, m_of[k], 17 + k + int(a * 1000))
                                    for n, a, k in cells)
        fm = pd.DataFrame([r for rows in got for r in rows])
        span = max(6 * math.floor(k / F) // m_of[k] for k in KS) + 60 * max(MARGINS)
        curves = dict(zip([(n, round(a, 4)) for n in ms for a in ALPHAS], Parallel(n_jobs=JOBS)(
            delayed(open_curve)(F, a, span, 100_000, 29 + int(a * 1000), **ms[n]) for n in ms for a in ALPHAS)))
        bound_of = {(r.model, round(r.alpha, 4), r.k): r.bound for r in gm.itertuples()}
        for i, r in fm.iterrows():
            at = depth_reader(ms[r.model], r.alpha, log_ub)
            bound = bound_of[(r.model, round(r.alpha, 4), r.k)]
            ts, shares = curves[(r.model, round(r.alpha, 4))]
            blind = blind_bound(ts, shares, 60 * int(r.margin), 6 * math.floor(r.k / F) // m_of[r.k])
            fm.loc[i, "depth_1e-09"] = at(math.log(EPS))
            fm.loc[i, "depth_chained"] = at(math.log(EPS / (r.chained + r.multi_bound) ** 2))
            fm.loc[i, "depth_per_win"] = at(math.log(EPS / r.per_win ** 2))
            fm.loc[i, "depth_tag"] = at(math.log(EPS / r.tag ** 2))
            fm.loc[i, "gmin_bound"] = bound
            fm.loc[i, "blind_bound"] = blind
            fm.loc[i, "depth_bound"] = at(math.log(EPS / (bound + blind + r.multi_bound) ** 2))
            top = largest_factor(at, int(r.k))
            fm.loc[i, "largest_factor"] = top
            fm.loc[i, "largest_evaluators"] = max(0.0, (top - r.chained) / r.multi_bound) if top else 0.0
            fm.loc[i, "largest_evaluators_bound"] = (max(0.0, (top - bound - blind) / r.multi_bound)
                                                     if top else 0.0)
        fm.to_csv(OUT / "formation.csv", index=False)
        print()
        with pd.option_context("display.width", 300, "display.max_columns", 40):
            print(fm.to_string(index=False, float_format=lambda v: f"{v:.4g}"))

    if "margin" in stages:
        got = Parallel(n_jobs=JOBS)(delayed(sweep)(n, ms[n], a, m_of[2160], 104729 + int(a * 1000))
                                    for n in ms for a in ALPHAS)
        sw = pd.DataFrame([r for rows in got for r in rows])
        for i, r in sw.iterrows():
            at = depth_reader(ms[r.model], r.alpha, log_ub)
            sw.loc[i, "depth_1e-09"] = at(math.log(EPS))
            sw.loc[i, "depth_chained"] = at(math.log(EPS / r.chained ** 2))
        sw.to_csv(OUT / "margin.csv", index=False)
        print()
        print(sw.to_string(index=False, float_format=lambda v: f"{v:.4g}"))

    if "span" in stages:
        rows = []
        for k in KS:
            m_k = m_of[k]
            w = math.floor(6 * math.floor(k / F) / m_k)
            phase = 4 * math.floor(k / F)
            for margin in MARGINS:
                t_a = w + 60 * margin
                row = dict(k=k, sub_windows=m_k, sub_window_slots=w, margin_min=margin, t_a_slots=t_a,
                           phase_slots=phase, largest_ratio=phase / t_a)
                for ratio in RATIOS:
                    row[f"honest_hours_r{ratio}"] = ratio * t_a / 3600
                rows.append(row)
        sp = pd.DataFrame(rows)
        sp.to_csv(OUT / "span.csv", index=False)
        print()
        print(sp.to_string(index=False, float_format=lambda v: f"{v:.3g}"))


if __name__ == "__main__":
    main(tuple(sys.argv[1:]) or STAGES)
