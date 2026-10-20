"""Phase H.3: the time-reading rule under a worst case of Delta (PLAN.md, H.3).

    python scripts/h3_time_rule.py      # needs runs/a1 and runs/b2; writes runs/h3/*.csv (about 10 minutes on 4 cores)

Every rule reads t, the client's clock when it evaluates less the target's parent's slot.

counting.csv: the counting bound (finality_sim.further.counting_logp) at Delta = 10 s: its catch-up
ratio, and the depth at 1e-9 when the client holds the n-th block n / rate slots after the parent,
at the full rate g lambda, the rate of a chain the coalition withholds from, (1 - alpha) g lambda,
and the worst-case honest rate h_w = 1 / (Delta + 1/p_h), with the hours on each clock; and the mean
of 2A + H over 2n at the withheld and the worst-case rates.

precheck.csv: B3's delay-scheduling attack (finality_sim.grr_attack, Gaži, Ren and Russell §4.7 on
the slot lottery) against time-reading rules, at Delta = 10 s. Each rule accepts the k-th block of
the client's chain when it arrives within deadline[k] slots of the target's symbol:
- "depth": the depth rule at B2's lower-bound depth for 1e-3, as a reference for the attack's
  success at confirmation (B3);
- "b4 at worst rates": B4's elapsed-time rule (finality_sim.elapsed.deadlines) at eps = 1e-3, the
  coalition winning at its slot occupancy and the canonical chain growing at h_w, the premined
  lead folded in;
- "b4 at worst rates, adjusted": the same with the coalition's rate divided by 1 - alpha and the
  canonical rate h_w / (1 - alpha), the rates after a total-stake adjustment (G4);
- "counting": the counting bound's deadlines at eps = 1e-3.
Columns: the attack's success at acceptance and ever after, per accepted target; the share of
targets accepted within the attack's horizon; the mean depth at acceptance.

precheck_observed.csv: the same attack against the observed counting rule at eps = 1e-3
(finality_sim.grr_attack.attack_observed), the forks counted three ways: every honest block since
the target that is not on the client's chain, at least what the client counts; only those on the
attack's competing chain, at most what it counts; none. Per target and per accepted target.

played.csv: the counting rule at eps = 1e-3, Delta = 10 s, played on 32 independent-slot timelines
of 200,000 slots whose canonical chain runs at the full rate g lambda while the coalition's wins
come at its slot occupancy, the client holding each block Delta slots after its slot, scored by the
premined private race (finality_sim.race.race_depths): the share of targets accepted, the mean
depth and minutes at acceptance, the share of accepted targets the race beats, and the wins B5's
closed form expects over the accepted targets at the timelines' share q of the wins.

observed.csv: the observed counting rule (finality_sim.further.counting_observed_logp), which also
counts the forks the client has received, the distinct slots of the blocks with a slot after the
target's parent's that do not descend from the target. Per share: B2's depth at 1e-9 under the
worst case at 10 s, with its hours on the clock of a chain the coalition withholds from, B5's closed
form at the random-delay growth, and the rule's depth at 1e-9 with no forks at the full rate, at the
withheld rate (also at 5e-10, and with ties to the coalition), and at the worst-case rate, with two
and four forks at the withheld rate, against a coalition that balances the honest chain at the
worst-case rate with the honest forks alone (h - h_w a slot) and with its own blocks too
(h - h_w + p_a), and against one that publishes every win as a fork at the withheld rate (p_a).

copies.csv: a coalition that publishes every win as a fork and signs each on `copies` blocks, at
the withheld rate: the rule's depth at 1e-9 when the client counts fork blocks and when it counts
their distinct slots.

walk.csv: the bound's geometric law for the lead and the catch-up against the worst-case renewal
walk (finality_sim.adaptive): the mean ratio, the factor per block of each law's tail, P(L >= 100),
and the rule's depth at 1e-9 with no forks at the withheld rate under each, with the client's tie
rule and with ties to the coalition, the walk with and without a second honest leader's block.

adaptive.csv: the chance per target that the observed rule accepts and the target falls, as a
multiple of eps, at eps = 1e-3 and 1e-9, against a coalition that plays adaptively
(finality_sim.adaptive), under the bound's law and under the worst-case walk: every win private
until the honest part alone forces acceptance, the rule's own case; the induction over private or
signed wins; free timing between the full-rate and the worst-case paths; the upper bound.

views.csv: a realizable play that breaks the bound per view (finality_sim.adaptive.view_risk): the
likeliest accepted view whose chance of failure exceeds eps, the rule's bound there and the view's
chance; the view of chance at least 1e-12 that fails most often; the chance of all views above
eps; and the play's chance per target.

forks.csv: the forks the client counts, measured on the engine's timelines of G6 (the
specification's Blend, honest relays, the coalition withholding, 64 runs a share): the share of
targets with none and with two or more, the mean, the 90th and 99th percentiles and the most; how
late a fork reaches the client (99th percentile and most, in slots after its slot); and the
accepted targets of played_observed.csv with a counted fork not yet at the client at acceptance.

played_observed.csv: the observed rule at eps = 1e-3 played on those timelines with each target's
measured forks and the client's arrival times, and on the independent-slot timelines of played.csv
with none, scored by the premined private race: the share of targets accepted, the mean depth and
minutes at acceptance, the share of accepted targets the race beats, and the wins B5's closed form
expects.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from b2_settlement import F
from b3_race import BASE, CONFIGS
from finality_sim.adaptive import (catch_up, cycle_pmf, decay, free_timing, induction, law_depth,
                                   second_leader, upper_bound, view_risk, walk_lead)
from finality_sim.elapsed import deadlines
from finality_sim.forks import fork_counts, fork_points
from finality_sim.further import (counting_deadlines, counting_depth, counting_observed_deadlines,
                                  counting_observed_depth, counting_ratio, observed_settle)
from finality_sim.grr_attack import attack_observed, attack_rule, occupancy
from finality_sim.private_race import log_strict, strict_depth
from finality_sim.race import race_depths, withhold_tree
from tsi_sim.config import SimConfig

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "h3"
ALPHAS = (0.25, 0.30, 1 / 3)
DELTA = 10
EPS = 1e-3
RUNS = 8
SLOTS = 20_000_000
K_MAX = 400
JOBS = 4
MODES = {0: "every honest block off the client's chain", 1: "those on the competing chain", 2: "none"}


def growth() -> float:
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    s = s[(s.family == "rounds") & (s.link_latency_mean == 0.1)]
    return float(s[(s.blend_hops == 3) & (s.blend_delay_max == 3)].growth_per_f.iloc[0])


def rules(alpha: float, lb_depth: int) -> dict[str, np.ndarray]:
    a, h = occupancy(F, alpha), occupancy(F, 1 - alpha)
    h_w = 1.0 / (DELTA + 1.0 / h)
    depth = np.full(K_MAX + 1, -1.0)
    depth[lb_depth + 1:] = np.inf                          # accept once k exceeds the depth
    return {"depth": depth,
            "b4 at worst rates": deadlines(a, h_w, EPS, K_MAX),
            "b4 at worst rates, adjusted": deadlines(a / (1 - alpha), h_w / (1 - alpha), EPS, K_MAX),
            "counting": counting_deadlines(alpha, DELTA, EPS, K_MAX, F)}


def timeline(alpha: float, rep: int) -> dict:
    cfg = SimConfig(**BASE, **CONFIGS["spec"], adversary_frac=alpha, replicate=rep)
    tree, arrival, mask, public, canonical = withhold_tree(cfg)
    adv_blocks = mask[tree.leader.clip(min=0)] & (tree.slot >= 0)
    client = int(np.nonzero(~mask)[0][0])                  # an honest node
    cids = np.nonzero(canonical)[0]
    cids = cids[np.argsort(tree.slot[cids], kind="stable")]
    xs = np.nonzero(public & ~canonical)[0]
    fp = fork_points(tree.parent, canonical)
    return dict(alpha=round(alpha, 4), replicate=rep,
                canon=tree.slot[cids].astype(np.int64),
                clock=np.maximum(arrival[client, cids], tree.slot[cids]),
                adv=np.unique(tree.slot[adv_blocks]).astype(np.int64),
                forks=fork_counts(tree, public, canonical),
                x_slot=tree.slot[xs].astype(np.int64), x_fork_height=tree.height[fp[xs]],
                x_late=arrival[client, xs] - tree.slot[xs],
                c_height=tree.height[cids], c_parent_slot=tree.slot[tree.parent[cids]].astype(np.int64))


def expected(q: float, ks: np.ndarray) -> float:
    """The wins B5's closed form expects over targets accepted at confirmations ``ks``."""
    vals, counts = np.unique(ks, return_counts=True)
    return float(sum(c * math.exp(log_strict(q, int(k) + 1)) for k, c in zip(vals, counts)))


def one(alpha: float, name: str, deadline: np.ndarray, seed: int) -> dict:
    at_conf, ever, targets, accepted, mean_depth = attack_rule(alpha, F, DELTA, SLOTS, deadline, seed)
    return dict(alpha=round(alpha, 4), rule=name, seed=seed, at_conf=at_conf, ever=ever,
                targets=targets, accepted=accepted, depth_sum=mean_depth * accepted)


def one_observed(alpha: float, t0: np.ndarray, mode: int, seed: int) -> dict:
    at_conf, ever, targets, accepted, depth_sum, fork_sum = attack_observed(alpha, F, DELTA, SLOTS, t0,
                                                                            seed, mode)
    return dict(alpha=round(alpha, 4), forks=MODES[mode], seed=seed, at_conf=at_conf, ever=ever,
                targets=targets, accepted=accepted, depth_sum=depth_sum, fork_sum=fork_sum)


def counting(g: float, lam: float) -> None:
    rows = []
    for a in (0.10, 0.25, 0.30, 1 / 3):
        h, pa = occupancy(F, 1 - a), occupancy(F, a)
        rates = {"full": g * lam, "withheld": (1 - a) * g * lam, "worst": 1.0 / (DELTA + 1.0 / h)}
        rho = counting_ratio(a, DELTA, F)
        row = dict(alpha=round(a, 4), delta_s=DELTA, ratio=rho)
        for name, rate in rates.items():
            d = counting_depth(a, DELTA, 1e-9, rate, F)
            row[f"depth_{name}"] = d
            row[f"hours_{name}"] = d / rate / 3600 if d > 0 else math.nan
        for name in ("withheld", "worst"):
            row[f"mean_{name}"] = (2 * pa + h) / rates[name] / 2
        rows.append(row)
    c = pd.DataFrame(rows)
    c.to_csv(OUT / "counting.csv", index=False)
    print(c.to_string(index=False, float_format=lambda v: f"{v:.3f}"))


def precheck() -> None:
    depths = pd.read_csv(HERE / "runs" / "b2" / "depths.csv")
    lb = {round(a, 4): int(depths[(depths.adv.round(4) == round(a, 4)) & (depths.delay_s == DELTA)
                                  & (depths.eps == EPS)].lb_depth.iloc[0]) for a in ALPHAS}
    jobs = [(a, name, dl, s) for a in ALPHAS for name, dl in rules(a, lb[round(a, 4)]).items()
            for s in range(RUNS)]
    got = Parallel(n_jobs=JOBS)(delayed(one)(*j) for j in jobs)
    out = []
    for (alpha, name), grp in pd.DataFrame(got).groupby(["alpha", "rule"], sort=False):
        acc = int(grp.accepted.sum())
        out.append(dict(alpha=alpha, rule=name, lb_depth=lb[alpha], targets=int(grp.targets.sum()),
                        accepted_share=acc / grp.targets.sum(),
                        fail_at_acceptance=grp.at_conf.sum() / max(acc, 1),
                        fail_ever=grp.ever.sum() / max(acc, 1), mean_depth=grp.depth_sum.sum() / max(acc, 1)))
    t = pd.DataFrame(out)
    t.to_csv(OUT / "precheck.csv", index=False)
    print()
    with pd.option_context("display.width", 200):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))

    jobs = [(a, counting_observed_deadlines(a, DELTA, EPS, K_MAX, (0,), F)[:, 0], m, s)
            for a in ALPHAS for m in MODES for s in range(RUNS)]
    got = Parallel(n_jobs=JOBS)(delayed(one_observed)(*j) for j in jobs)
    out = []
    for (alpha, forks), grp in pd.DataFrame(got).groupby(["alpha", "forks"], sort=False):
        acc, tg = int(grp.accepted.sum()), int(grp.targets.sum())
        out.append(dict(alpha=alpha, forks=forks, targets=tg, accepted=acc,
                        fail_per_target=grp.at_conf.sum() / tg, fail_ever_per_target=grp.ever.sum() / tg,
                        fail_per_acceptance=grp.at_conf.sum() / acc if acc else math.nan,
                        mean_depth=grp.depth_sum.sum() / acc if acc else math.nan,
                        mean_forks=grp.fork_sum.sum() / acc if acc else math.nan))
    t = pd.DataFrame(out)
    t.to_csv(OUT / "precheck_observed.csv", index=False)
    print()
    with pd.option_context("display.width", 200):
        print(t.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


def played(g: float, lam: float) -> None:
    rows = []
    for a in ALPHAS:
        dl = counting_deadlines(a, DELTA, EPS, K_MAX, F)[:, None]
        pa = occupancy(F, a)
        rng = np.random.default_rng(int(a * 1000))
        ks, ts, beaten = [], [], []
        for _ in range(32):
            canon = np.nonzero(rng.random(200_000) < g * lam)[0].astype(np.int64)
            adv = np.nonzero(rng.random(200_000) < pa)[0].astype(np.int64)
            k, tt = observed_settle(canon, dl, np.zeros(canon.size, np.int64), (0,), canon + DELTA)
            deepest = race_depths(canon, adv, K_MAX, premine=True, win_at=1)
            ok = (k >= 1) & (deepest >= 0)
            ks.append(k[ok]), ts.append(tt[ok]), beaten.append(deepest[ok] >= k[ok])
        ks, ts, beaten = (np.concatenate(x) for x in (ks, ts, beaten))
        rows.append(dict(alpha=round(a, 4), accepted=int(ks.size), mean_depth=float(ks.mean()),
                         mean_minutes=float(ts.mean() / 60), race_beats=float(beaten.mean()),
                         expected=expected(pa / (pa + g * lam), ks)))
    pl = pd.DataFrame(rows)
    pl.to_csv(OUT / "played.csv", index=False)
    print()
    print(pl.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


def observed(g: float, lam: float) -> None:
    depths = pd.read_csv(HERE / "runs" / "b2" / "depths.csv")
    b2 = depths[(depths.delay_s == DELTA) & (depths.eps == 1e-9)]
    rows = []
    for a in (0.10, 0.25, 0.30, 1 / 3):
        h, pa = occupancy(F, 1 - a), occupancy(F, a)
        h_w = 1.0 / (DELTA + 1.0 / h)
        full, withheld = g * lam, (1 - a) * g * lam
        q = a / (a + (1 - a) * g)
        d_w = counting_observed_depth(a, DELTA, 1e-9, withheld, 0, 0.0, F)
        d_hw = counting_observed_depth(a, DELTA, 1e-9, h_w, 0, 0.0, F)
        b2_depth = int(b2[b2.adv.round(4) == round(a, 4)].ub_depth.iloc[0])
        rows.append(dict(
            alpha=round(a, 4), delta_s=DELTA, b2_depth=b2_depth, b2_hours_withheld=b2_depth / withheld / 3600,
            closed_depth=strict_depth(q, math.log(1e-9)),
            full_0=counting_observed_depth(a, DELTA, 1e-9, full, 0, 0.0, F),
            withheld_0=d_w, hours_withheld_0=d_w / withheld / 3600 if d_w > 0 else math.nan,
            withheld_0_half=counting_observed_depth(a, DELTA, 5e-10, withheld, 0, 0.0, F),
            withheld_0_ties=counting_observed_depth(a, DELTA, 1e-9, withheld, 0, 0.0, F, ties_to_coalition=True),
            worst_0=d_hw, hours_worst_0=d_hw / h_w / 3600 if d_hw > 0 else math.nan,
            withheld_2=counting_observed_depth(a, DELTA, 1e-9, withheld, 2, 0.0, F),
            withheld_4=counting_observed_depth(a, DELTA, 1e-9, withheld, 4, 0.0, F),
            balancing=counting_observed_depth(a, DELTA, 1e-9, h_w, 0, h - h_w, F),
            balancing_own=counting_observed_depth(a, DELTA, 1e-9, h_w, 0, h - h_w + pa, F),
            publishing=counting_observed_depth(a, DELTA, 1e-9, withheld, 0, pa, F)))
    ob = pd.DataFrame(rows)
    ob.to_csv(OUT / "observed.csv", index=False)
    print()
    print(ob.to_string(index=False, float_format=lambda v: f"{v:.3f}"))

    rows = []
    for a in (0.10, 0.25):
        pa, withheld = occupancy(F, a), (1 - a) * g * lam
        for copies in (1, 2, 3, 5, 10):
            rows.append(dict(alpha=round(a, 4), copies=copies,
                             blocks=counting_observed_depth(a, DELTA, 1e-9, withheld, 0, copies * pa, F),
                             slots=counting_observed_depth(a, DELTA, 1e-9, withheld, 0, pa, F)))
    cp = pd.DataFrame(rows)
    cp.to_csv(OUT / "copies.csv", index=False)
    print()
    print(cp.to_string(index=False))


def walk(g: float, lam: float) -> None:
    rows = []
    for a in ALPHAS:
        pa, h = occupancy(F, a), occupancy(F, 1 - a)
        withheld = (1 - a) * g * lam
        rho = counting_ratio(a, DELTA, F)
        geo = (1 - rho) * rho ** np.arange(1500), rho ** np.arange(1500)
        row = dict(alpha=round(a, 4), ratio=rho, second=second_leader(a, F),
                   rule=law_depth(a, DELTA, 1e-9, withheld, *geo),
                   rule_ties=law_depth(a, DELTA, 1e-9, withheld, *geo, ties_to_coalition=True))
        for name, second in (("walk", 0.0), ("walk2", second_leader(a, F))):
            u = cycle_pmf(pa, h, DELTA, second=second)
            pmf, tail = walk_lead(u, 1500)
            c = catch_up(u, tail)
            row[f"{name}_mean"] = float((np.arange(u.size) * u).sum())
            row[f"{name}_decay"] = decay(u)
            row[f"{name}_lead100"] = float(tail[100])
            row[name] = law_depth(a, DELTA, 1e-9, withheld, pmf, c)
            row[f"{name}_ties"] = law_depth(a, DELTA, 1e-9, withheld, pmf, c, ties_to_coalition=True)
        row["rule_lead100"] = rho ** 100
        rows.append(row)
    wk = pd.DataFrame(rows)
    wk.to_csv(OUT / "walk.csv", index=False)
    print()
    with pd.option_context("display.width", 250):
        print(wk.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


def adaptive() -> None:
    cells = [(a, eps, n_max) for a in ALPHAS for eps, n_max in ((1e-3, 500), (1e-9, 900))]

    def cell(a, eps, n_max, model):
        ind = induction(a, DELTA, eps, model, n_max, F)
        return dict(alpha=round(a, 4), eps=eps, law=model, t_end=ind["t_end"], n_end=ind["n_end"],
                    own=ind["own"] / eps, induction=ind["value"] / eps,
                    free_timing=free_timing(a, DELTA, eps, model, n_max, F)["value"] / eps,
                    upper_bound=upper_bound(a, DELTA, eps, model, n_max, F)["value"] / eps)
    got = Parallel(n_jobs=JOBS)(delayed(cell)(a, eps, n, m) for a, eps, n in cells for m in ("bound", "renewal"))
    ad = pd.DataFrame(got)
    ad.to_csv(OUT / "adaptive.csv", index=False)
    print()
    with pd.option_context("display.width", 200):
        print(ad.to_string(index=False, float_format=lambda v: f"{v:.4g}"))

    views()


def views() -> None:
    rows = []
    for a, eps, n_max in ((a, eps, n_max) for a in ALPHAS for eps, n_max in ((1e-3, 500), (1e-9, 900))):
        r = view_risk(a, DELTA, eps, n_max, F)
        v, w = r["likeliest"], r["worst"] or {}
        rows.append(dict(alpha=round(a, 4), eps=eps, n=v["n"], t=v["t"], honest=v["honest"],
                         coalition=v["coalition"], risk=v["risk"], bound=v["bound"], chance=v["chance"],
                         worst_n=w.get("n", -1), worst_t=w.get("t", -1), worst_coalition=w.get("coalition", -1),
                         worst_risk=w.get("risk", math.nan), worst_bound=w.get("bound", math.nan),
                         worst_chance=w.get("chance", math.nan),
                         above=r["above"], worst_honest=r["worst_honest"], per_target=r["per_target"]))
    vw = pd.DataFrame(rows)
    vw.to_csv(OUT / "views.csv", index=False)
    print()
    with pd.option_context("display.width", 200):
        print(vw.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


def engine(g: float, lam: float) -> None:
    lines = Parallel(n_jobs=JOBS, backend="loky")(delayed(timeline)(a, r) for a in ALPHAS for r in range(64))
    frows, prows = [], []
    for a in ALPHAS:
        mine = [x for x in lines if x["alpha"] == round(a, 4)]
        forks = np.concatenate([x["forks"][1:] for x in mine])            # targets with a parent
        late = np.concatenate([x["x_late"] for x in mine])
        grid = tuple(int(v) for v in np.unique(forks))
        dl = counting_observed_deadlines(a, DELTA, EPS, K_MAX, grid, F)
        ks, ts, beaten, total, in_flight, wins, made = [], [], [], 0, 0, 0, 0
        for x in mine:
            wins, made = wins + x["adv"].size, made + x["adv"].size + x["canon"].size
            k, tt = observed_settle(x["canon"], dl, x["forks"], grid, x["clock"])
            deepest = race_depths(x["canon"], x["adv"], K_MAX, premine=True, win_at=1)
            scored = deepest >= 0
            ok = (k >= 1) & scored
            total += int(scored[1:].sum())
            ks.append(k[ok]), ts.append(tt[ok]), beaten.append(deepest[ok] >= k[ok])
            for i in np.nonzero(ok & (x["forks"] > 0))[0]:
                hit = (x["x_slot"] > x["c_parent_slot"][i]) & (x["x_fork_height"] < x["c_height"][i])
                seen_by = x["clock"][i + k[i]]
                in_flight += bool(np.any(x["x_slot"][hit] + x["x_late"][hit] > seen_by))
        ks, ts, beaten = (np.concatenate(v) for v in (ks, ts, beaten))
        frows.append(dict(alpha=round(a, 4), targets=int(forks.size), none=float(np.mean(forks == 0)),
                          two_or_more=float(np.mean(forks >= 2)), mean=float(forks.mean()),
                          p90=float(np.percentile(forks, 90)), p99=float(np.percentile(forks, 99)),
                          most=int(forks.max()), late_p99=float(np.percentile(late, 99)),
                          late_most=float(late.max()), in_flight=in_flight))
        prows.append(dict(alpha=round(a, 4), timelines="engine", targets=total, accepted=int(ks.size),
                          mean_depth=float(ks.mean()), mean_minutes=float(ts.mean() / 60),
                          race_beats=float(beaten.mean()), expected=expected(wins / made, ks)))
        dl0 = counting_observed_deadlines(a, DELTA, EPS, K_MAX, (0,), F)
        pa = occupancy(F, a)
        rng = np.random.default_rng(int(a * 1000))
        ks, ts, beaten, total = [], [], [], 0
        for _ in range(32):
            canon = np.nonzero(rng.random(200_000) < g * lam)[0].astype(np.int64)
            adv = np.nonzero(rng.random(200_000) < pa)[0].astype(np.int64)
            k, tt = observed_settle(canon, dl0, np.zeros(canon.size, np.int64), (0,), canon + DELTA)
            deepest = race_depths(canon, adv, K_MAX, premine=True, win_at=1)
            scored = deepest >= 0
            ok = (k >= 1) & scored
            total += int(scored[1:].sum())
            ks.append(k[ok]), ts.append(tt[ok]), beaten.append(deepest[ok] >= k[ok])
        ks, ts, beaten = (np.concatenate(v) for v in (ks, ts, beaten))
        prows.append(dict(alpha=round(a, 4), timelines="full rate, no forks", targets=total,
                          accepted=int(ks.size), mean_depth=float(ks.mean()),
                          mean_minutes=float(ts.mean() / 60), race_beats=float(beaten.mean()),
                          expected=expected(pa / (pa + g * lam), ks)))
    fk = pd.DataFrame(frows)
    fk.to_csv(OUT / "forks.csv", index=False)
    po = pd.DataFrame(prows)
    po.to_csv(OUT / "played_observed.csv", index=False)
    print()
    print(fk.to_string(index=False, float_format=lambda v: f"{v:.4g}"))
    print()
    print(po.to_string(index=False, float_format=lambda v: f"{v:.4g}"))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    g, lam = growth(), -math.log(1 - F)
    counting(g, lam)
    observed(g, lam)
    walk(g, lam)
    played(g, lam)
    adaptive()
    engine(g, lam)
    precheck()


if __name__ == "__main__":
    main()
