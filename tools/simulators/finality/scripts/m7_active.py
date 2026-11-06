"""Phase M.7: the active stake at 30 % of the supply (PLAN.md Phase M).

    python scripts/m7_active.py     # writes runs/m7/; about 15 minutes on 12 cores

The lottery weighs a note against the inferred total active stake, so every share in the study is
a share of the active stake; the block rewards' target puts the active stake at 30 % of the supply
(src/finality_sim/active.py).

- supply.csv: the most of the supply each coalition holds with the active stake at 30 %.
- seats.csv: D2's anonymous committees, sized for the inference's error up to 1.05, sized again
  once the coalition's stake enters from outside the active stake, `1/(1 − α)` as after a deflation,
  and the honest stake entering at which the committee sized for 1.05 loses safety.
- wait.csv: the slot rule's wait at 1e-9 under the worst case at 10 s without grinding (K.7's bound,
  src/finality_sim/waitbound.py), with the true active stake `x` times the inferred.
- edge.csv: the `x` at which that wait reaches `⌊k/f⌋` = 64,800 slots, 18 hours, against 30 % and
  a third, and the least inferred active stake, as a share of the supply, that keeps the true
  active stake, at most 30 % of the supply, within it.
- declared.csv: the most declarations the active stake makes at the minimum stake, and what
  verifying their votes costs, with rounds of 60 slots, as M.4 counts it (reports/pqc).
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd
from joblib import Parallel, delayed

from finality_sim import active as ac
from finality_sim import committee as cm
from finality_sim import netcert as nc
from finality_sim.waitbound import wait_curve, wait_needed

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "m7"
EPS = 1e-9
F = 1 / 30
K = math.floor(2160 / F)
DELTA_S = 10
T_MAX = 1_500_000
COALITIONS = (0.10, 0.25, 0.30, 1 / 3)
WAITED = (0.30, 1 / 3)
XS = (1.0, ac.entering(0.30), ac.entering(1 / 3), 1.9, 2.0, 2.5, 3.0)
BRACKETS = {0.30: (2.5, 3.0), 1 / 3: (1.9, 2.0)}
EDGE_TOL = 1e-3
ROUND = 60
JOBS = 12


def need(alpha: float, x: float) -> int:
    """The least wait, in slots, whose bound is at most EPS with the true stake ``x`` times the
    inferred; -1 past T_MAX."""
    return wait_needed(wait_curve(T_MAX, alpha, DELTA_S, F, floor=EPS / 10, scale=x), EPS)


def edge(alpha: float) -> dict:
    """Bisect the ``x`` at which the wait reaches K, inside the bracket the grid shows."""
    lo, hi = BRACKETS[alpha]
    w_lo, w_hi = need(alpha, lo), need(alpha, hi)
    if not 0 < w_lo <= K < w_hi:
        raise SystemExit(f"bracket {lo}..{hi} does not hold the edge against {alpha}")
    while hi - lo > EDGE_TOL:
        mid = (lo + hi) / 2
        w = need(alpha, mid)
        if 0 < w <= K:
            lo, w_lo = mid, w
        else:
            hi = mid
    return dict(alpha=alpha, edge=lo, wait=w_lo, wait_h=w_lo / 3600,
                least_inferred=ac.least_inferred(lo))


def main() -> None:
    supply = pd.DataFrame([dict(alpha=a, supply_share=ac.supply_share(a)) for a in COALITIONS])

    rows = []
    for a in COALITIONS:
        sized = cm.smallest_committee(a, EPS, inflation=1.05)
        entered = cm.smallest_committee(a, EPS, inflation=ac.entering(a))
        x = ac.honest_entry_break(a, EPS) if sized else math.nan
        rows.append(dict(alpha=a, sized_seats=sized[0] if sized else math.nan,
                         sized_quorum=sized[1] if sized else math.nan, entering=ac.entering(a),
                         entered_seats=entered[0] if entered else math.nan,
                         entered_quorum=entered[1] if entered else math.nan,
                         honest_break=x, break_active=x - 1,
                         break_supply=nc.STAKED_SHARE * (x - 1)))
    seats = pd.DataFrame(rows)

    jobs = [(a, x) for x in XS for a in WAITED]
    par = Parallel(n_jobs=JOBS)
    out = par([delayed(need)(a, x) for a, x in jobs] + [delayed(edge)(a) for a in WAITED])
    waits, edges = out[:len(jobs)], out[len(jobs):]
    wait = pd.DataFrame([dict(alpha=a, x=x, interval_s=1 / ac.lottery_chance(x), wait=w,
                              wait_h=w / 3600 if w > 0 else math.nan)
                         for (a, x), w in zip(jobs, waits)])
    edge_t = pd.DataFrame(edges)

    ns, size = nc.pi5_signature("Ed25519", "rustcrypto")
    cap = ac.declarations_cap()
    declared = pd.DataFrame([dict(active=nc.STAKED_SHARE, minimum=nc.MIN_STAKE_SHARE,
                                  declarations=cap, votes_per_s=cap / ROUND,
                                  core_share=nc.verify_core_share(cap, ROUND, ns),
                                  kb_per_s=cap / ROUND * nc.vote_bytes(size) / 1000)])

    OUT.mkdir(parents=True, exist_ok=True)
    for name, t in (("supply", supply), ("seats", seats), ("wait", wait), ("edge", edge_t),
                    ("declared", declared)):
        t.to_csv(OUT / f"{name}.csv", index=False)
        print(t.to_string(index=False), end="\n\n")
    print(f"no anonymous committee once the coalition's stake enters, from {ac.seats_edge():.4f}")


if __name__ == "__main__":
    main()
