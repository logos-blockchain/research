"""Phase J, J.2: every attack within Δ, at today's block rate (PLAN.md J.2).

    python scripts/j2_attacks.py      # writes runs/j2/{tail,attack,h14,window}.csv and
                                      # runs/j2/{retract,h14_retract,edges}.csv

On a fork choice that weighs every honest block, one weight per win (both variants of phase J),
at f = 1/30, exactly (src/finality_sim/delayfc.py):

- tail.csv: J.2.1, the balance begun with an empty reserve when the target's phase opens; the
  chance it still stands 1, 6 and 24 hours later, and the hours until that chance is 1e-9;
- attack.csv: J.2.2 and J.2.3, the depth at 1e-9 of each attack in slots, hours and honest
  blocks: the balance alone, the combined attack with and without a premined reserve, and the
  private race of E2 and E5 under the worst case of Δ; ties steered by the adversary, a fixed
  rule that favours the target's side, and a fixed rule that favours the adversary's (the tie
  exploit); beside them, J.2.4, the chain's B2 depths at its worst-case clock;
- h14.csv: H14's two parts against a third;
- window.csv: what the DAG's window changes, at E2's window of 7.5/f slots: the share of phases
  that open after a quiet stretch longer than the window less Δ, whose first block references no
  block inside it and weighs nothing, and the share of a private side's wins that follow the
  side's previous block by more than the window, which weigh nothing;
- retract.csv: the same depths when a placed win can be retracted by a second copy on the other
  side (two moves a win): ties steered, exactly; a fixed rule with the direction free (relaxed,
  the most retraction can buy) and with the direction kept and the passes between states chosen
  best (an attack, without a premined reserve); none at or above the edge of two moves a win;
- h14_retract.csv: H14's two parts on the retraction model, and whether any variant beats the
  chain's attack at 10 s against a third, the stop condition of PLAN.md J.2;
- edges.csv: E5's edges, one move a win, beside the edges of two moves a win, on E5's grid.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from finality_sim.balance import threshold
from finality_sim.delayfc import curve, depth, edge, rates

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "j2"
F = 1 / 30
EPS = 1e-9
ALPHAS = (0.25, 0.30, 1 / 3)
DELAYS = (1, 2, 5, 10, 20)
HORIZON = 72 * 3600                          # slots; a depth beyond it is reported as none
TAIL_HOURS = (1, 6, 24)
# (name, mode, ties, s_win, premined)
ATTACKS = (
    ("balance", "balance", "steered", None, False),
    ("balance", "balance", "fixed", None, False),
    ("combined", "attack", "steered", 0, True),
    ("combined", "attack", "fixed", 1, True),
    ("combined, tie exploit", "attack", "fixed", 0, True),
    ("combined, no premine", "attack", "steered", 0, False),
    ("combined, no premine", "attack", "fixed", 1, False),
    ("private race", "private", "fixed", 1, True),
    ("private race, tie exploit", "private", "fixed", 0, True),
)


REALISED = dict(s_lo=-40, s_hi=60, r_max=24)
# (name, mode, ties, s_win, premined, count, model)
RETRACT = (
    ("balance", "balance", "fixed", None, False, "best switches",
     dict(moves=2, policy="best", **REALISED)),
    ("combined", "attack", "fixed", 1, False, "best switches",
     dict(moves=2, policy="best", **REALISED)),
    ("combined, tie exploit", "attack", "fixed", 0, False, "best switches",
     dict(moves=2, policy="best", **REALISED)),
    ("balance", "balance", "steered", None, False, "two moves", dict(moves=2)),
    ("balance", "balance", "fixed", None, False, "relaxed", dict(moves=2, relaxed=True)),
    ("combined", "attack", "steered", 0, True, "two moves", dict(moves=2)),
    ("combined", "attack", "fixed", 1, True, "relaxed", dict(moves=2, relaxed=True)),
    ("combined, tie exploit", "attack", "fixed", 0, True, "relaxed",
     dict(moves=2, relaxed=True)),
)


def chain_clock(alpha: float, delta: float) -> float:
    """Seconds per canonical block under the worst case of Δ (SETTLEMENT.md B2)."""
    p_h = 1.0 - (1.0 - F) ** (1.0 - alpha)
    return delta + 1.0 / p_h


def one(alpha: float, delta: int, name: str, mode: str, ties: str, s_win, premined: bool) -> dict:
    lam_h, _ = rates(F, alpha)
    row = dict(alpha=alpha, delay_s=delta, attack=name, ties=ties, mode=mode,
               s_win=s_win, premined=premined)
    # above the edge of E5 the balance holds forever with positive probability: no depth
    edge = threshold(F, delta, "adversarial" if ties == "steered" else "deterministic")
    row["forever"] = mode != "private" and alpha >= edge
    if row["forever"]:
        row.update(depth_slots=None, hours=None, honest_blocks=None, at_depth_slots=None)
        if mode == "balance":
            row.update({f"hold_{h}h": None for h in TAIL_HOURS})
        return row
    c = curve(F, alpha, delta, ties, mode, HORIZON, s_win=s_win, premined=premined,
              stop=1e-30 if mode == "balance" else EPS / 100)
    key = "hold" if mode == "balance" else "ever"
    k = depth(c[key], EPS)
    row.update(depth_slots=k, hours=None if k is None else k / 3600,
               honest_blocks=None if k is None else k * lam_h,
               at_depth_slots=depth(c["at"], EPS))
    if mode == "balance":
        for h in TAIL_HOURS:
            t = h * 3600
            row[f"hold_{h}h"] = float(c["hold"][t]) if t < c["hold"].size else 0.0
    return row


def one_retract(alpha: float, delta: int, name: str, mode: str, ties: str, s_win,
                premined: bool, count: str, kw: dict) -> dict:
    lam_h, _ = rates(F, alpha)
    row = dict(alpha=alpha, delay_s=delta, attack=name, ties=ties, count=count,
               premined=premined)
    # at or above the edge of two moves a win the balance lasts for ever with positive chance
    row["forever"] = alpha >= edge(F, delta, ties, 2)
    if row["forever"]:
        row.update(depth_slots=None, hours=None, honest_blocks=None)
        if mode == "balance":
            row.update({f"hold_{h}h": None for h in TAIL_HOURS})
        return row
    c = curve(F, alpha, delta, ties, mode, HORIZON, s_win=s_win, premined=premined,
              stop=1e-30 if mode == "balance" else EPS / 100, **kw)
    key = "hold" if mode == "balance" else "ever"
    k = depth(c[key], EPS)
    row.update(depth_slots=k, hours=None if k is None else k / 3600,
               honest_blocks=None if k is None else k * lam_h)
    if mode == "balance":
        for h in TAIL_HOURS:
            t = h * 3600
            row[f"hold_{h}h"] = float(c["hold"][t]) if t < c["hold"].size else 0.0
    return row


def retraction(chain: pd.DataFrame) -> None:
    jobs = [(a, d, *x) for x in RETRACT for a in ALPHAS for d in DELAYS]
    r = pd.DataFrame(Parallel(n_jobs=4)(delayed(one_retract)(*j) for j in jobs))
    r = r.merge(chain, on=["alpha", "delay_s"])
    r.to_csv(OUT / "retract.csv", index=False)
    third = r[(r.alpha.round(4) == round(1 / 3, 4)) & (r.attack != "balance")]
    rows = []
    for (name, count, ties), g in third.groupby(["attack", "count", "ties"], sort=False):
        g = g.set_index("delay_s")
        h1, h10, chain10 = g.loc[1, "hours"], g.loc[10, "hours"], g.loc[10, "chain_lower_hours"]
        finite = pd.notna(h1) and pd.notna(h10)
        rows.append(dict(attack=name, count=count, ties=ties, hours_1s=h1, hours_10s=h10,
                         ratio=h10 / h1 if finite else None,
                         part1_holds=bool(finite and h10 / h1 < 1.25),
                         chain_10s_hours=chain10,
                         part2_holds=bool(pd.notna(h10) and h10 < chain10)))
    pd.DataFrame(rows).to_csv(OUT / "h14_retract.csv", index=False)
    e5 = pd.read_csv(HERE / "runs" / "e5" / "balance.csv")
    e5["retraction_steered"] = [edge(f, d, "steered", 2) for f, d in zip(e5.f, e5.delay_s)]
    e5["retraction_fixed"] = [edge(f, d, "fixed", 2) for f, d in zip(e5.f, e5.delay_s)]
    e5.to_csv(OUT / "edges.csv", index=False)
    with pd.option_context("display.width", 200, "display.max_columns", 30):
        print(r[["alpha", "delay_s", "attack", "ties", "count", "forever", "depth_slots",
                 "hours"]].round(3).to_string(index=False))
        print(pd.DataFrame(rows).round(3).to_string(index=False))
        print(e5.round(4).to_string(index=False))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    w = round(7.5 / F)                       # E2's window, 225 slots
    win = []
    for a in ALPHAS:
        lam_h, lam_a = rates(F, a)
        for d in DELAYS:
            win.append(dict(alpha=a, delay_s=d, window=w,
                            stale_phases=math.exp(-lam_h * (w - d)),
                            late_wins=math.exp(-lam_a * w)))
    pd.DataFrame(win).to_csv(OUT / "window.csv", index=False)
    jobs = [(a, d, *x) for a in ALPHAS for d in DELAYS for x in ATTACKS]
    rows = Parallel(n_jobs=4)(delayed(one)(*j) for j in jobs)
    t = pd.DataFrame(rows)
    t[t["mode"] == "balance"].drop(columns=["at_depth_slots"]).to_csv(OUT / "tail.csv",
                                                                      index=False)
    b2 = pd.read_csv(HERE / "runs" / "b2" / "depths.csv")
    b2 = b2[b2.eps == EPS]
    chain = []
    for a in ALPHAS:
        for d in DELAYS:
            r = b2[(b2.adv.round(4) == round(a, 4)) & (b2.delay_s == d)].iloc[0]
            clock = chain_clock(a, d)
            chain.append(dict(alpha=a, delay_s=d, chain_lower_blocks=float(r.lb_depth),
                              chain_lower_hours=float(r.lb_depth) * clock / 3600,
                              chain_upper_blocks=int(r.ub_depth),
                              chain_upper_hours=int(r.ub_depth) * clock / 3600,
                              chain_clock_s=clock))
    chain = pd.DataFrame(chain)
    t = t.merge(chain, on=["alpha", "delay_s"])
    t.to_csv(OUT / "attack.csv", index=False)
    retraction(chain)

    # H14 against a third: the strongest attack with a fixed tie rule, at 1 and 10 s
    third = t[(t.alpha.round(4) == round(1 / 3, 4)) & (t.ties == "fixed")]
    h14 = []
    for name in ("combined", "combined, tie exploit"):
        g = third[third.attack == name].set_index("delay_s")
        h1, h10 = g.loc[1, "hours"], g.loc[10, "hours"]
        chain10 = g.loc[10, "chain_lower_hours"]
        h14.append(dict(attack=name, hours_1s=h1, hours_10s=h10, ratio=h10 / h1,
                        part1_holds=bool(h10 / h1 < 1.25), chain_10s_hours=chain10,
                        part2_holds=bool(h10 < chain10)))
    pd.DataFrame(h14).to_csv(OUT / "h14.csv", index=False)
    with pd.option_context("display.width", 200, "display.max_columns", 30):
        print(t[["alpha", "delay_s", "attack", "ties", "depth_slots", "hours",
                 "chain_lower_hours", "chain_upper_hours"]].round(3).to_string(index=False))
        print(pd.DataFrame(h14).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
