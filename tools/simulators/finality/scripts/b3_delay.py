"""Phase B3: the delay-scheduling attacker against the B2 bounds (PLAN.md B3).

    python scripts/b3_delay.py        # writes runs/b3/delay.csv

At f = 1/30 with 1 s slots, for attacker shares 0.10, 0.25 and 1/3 and delays of 2, 5 and 10 s:

- the attack of B1's lower bound, played on the slot lottery (src/finality_sim/grr_attack.py),
  counted at confirmation as the code counts it, and at any later moment;
- the private-chain attack alone on the same draws, with premining and ties to the attacker
  (src/finality_sim/race.py, win_at = 0), on the chain of honest wins more than Delta apart;
- the ported lower and upper bounds at D = f Delta.

20 runs of 1e8 slots per point.
"""

from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from finality_sim.grr_attack import attack, timelines
from finality_sim.lcbounds import error_lb, error_ub, slot_pdf
from finality_sim.race import race

from b2_settlement import alphabet_for

F = 1 / 30
OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "b3"
ADV = (0.10, 0.25, 1 / 3)
DELAYS_S = (2, 5, 10)
K_MAX = 60
RUNS = 20
SLOTS = 100_000_000


def simulate(adv: float, delay: int, seed: int) -> dict:
    at_conf, ever, n = attack(adv, F, delay, SLOTS, K_MAX, seed)
    honest, adv_slots = timelines(adv, F, delay, SLOTS, seed)
    priv, n_priv = race(honest, adv_slots, K_MAX, give_up=60, premine=True, win_at=0)
    return dict(at_conf=at_conf, ever=ever, targets=n, private=priv, private_targets=n_priv)


def bounds(adv: float, delay: int, k: int) -> tuple[float, float]:
    d = F * delay
    a = alphabet_for(adv, d)
    states = max(30, a + 1)
    sp = slot_pdf(1 - adv, d, a)
    return error_lb(k, sp, a, states, min_prob=1e-16), error_ub(k, sp, a, states, 1e-16)


def main() -> None:
    pts = [(a, d) for a in ADV for d in DELAYS_S]
    sims = Parallel(n_jobs=-2)(delayed(simulate)(a, d, s) for a, d in pts for s in range(RUNS))
    bnds = Parallel(n_jobs=-2)(delayed(bounds)(a, d, k) for a, d in pts
                               for k in range(1, K_MAX + 1))
    rows = []
    for i, (a, d) in enumerate(pts):
        part = sims[i * RUNS:(i + 1) * RUNS]
        tot = {key: sum(p[key] for p in part) for key in part[0]}
        for k in range(1, K_MAX + 1):
            lb, ub = bnds[i * K_MAX + k - 1]
            rows.append(dict(adv=round(a, 4), delay_s=d, depth=k,
                             at_confirmation=tot["at_conf"][k - 1] / tot["targets"],
                             ever=tot["ever"][k - 1] / tot["targets"],
                             private=tot["private"][k - 1] / tot["private_targets"],
                             targets=tot["targets"], private_targets=tot["private_targets"],
                             lb=lb, ub=ub))
    t = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    t.to_csv(OUT / "delay.csv", index=False)
    with pd.option_context("display.width", 200, "display.max_rows", 600):
        print(t[t.depth % 10 == 0].to_string(index=False))


if __name__ == "__main__":
    main()
