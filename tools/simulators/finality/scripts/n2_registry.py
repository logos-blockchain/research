"""Phase N.2: the registry and a lottery that divides by it (PLAN.md Phase N).

    python scripts/n2_registry.py    # writes runs/n2/{registry,lottery}.csv; about 30 minutes on 12 cores

src/finality_sim/units.py.

- registry.csv: the units the active stake at 30 % of the supply registers at today's minimum stake,
  the window in which they go on chain, the stake distribution snapshot phase once the snapshot is
  final (2⌊k/f⌋ slots), the registrations a second network-wide, a registration's bytes, the
  registry's bytes an epoch, and the registrations a holder of 1 %, 0.1 % and 0.01 % makes.
- lottery.csv: the slot rule's wait at 1e-9 under the worst case at 10 s without grinding (K.7's
  bound, src/finality_sim/waitbound.py) against 30 % and a third, with a share of the honest
  registered stake online and the coalition's online. Divided by the registered stake, the
  coalition's rate is its stake's and the honest rate falls with its uptime; divided by an
  inference that has corrected to the online stake, both rates are the full lottery's. The
  coalition's share of the online stake is the same in both.
"""

from __future__ import annotations

import pathlib

import pandas as pd
from joblib import Parallel, delayed

from finality_sim import units as un
from finality_sim.waitbound import wait_curve, wait_needed

OUT = pathlib.Path(__file__).resolve().parent.parent / "runs" / "n2"
EPS = 1e-9
F = 1 / 30
DELTA_S = 10
T_MAX = 1_500_000
COALITIONS = (0.30, 1 / 3)
UPTIMES = (1.0, 0.95, 0.9, 2 / 3)
SHARES = (0.01, 0.001, 0.0001)
JOBS = 12


def need(alpha: float, scale: float) -> int:
    """The least wait, in slots, whose bound is at most EPS; -1 past T_MAX."""
    return wait_needed(wait_curve(T_MAX, alpha, DELTA_S, F, floor=EPS / 10, scale=scale), EPS)


def main() -> None:
    units = un.registered_units()
    window = un.SNAPSHOT_PHASE - un.K_OVER_F
    registry = pd.DataFrame([dict(
        units=units, window_slots=window, window_h=window / 3600,
        per_s=un.registrations_per_s(units), bytes=un.registration_bytes(),
        epoch_mb=units * un.registration_bytes() / 1e6,
        **{f"holder_{s:g}": round(s * units) for s in SHARES})])

    jobs = []
    for a in COALITIONS:
        for u in UPTIMES:
            for mode, rates in (("registered", un.registered_rates), ("inferred", un.inferred_rates)):
                eff, scale = rates(a, u)
                jobs.append(dict(alpha=a, uptime=u, mode=mode, alpha_online=eff, scale=scale,
                                 interval_s=un.block_interval(scale)))
    waits = Parallel(n_jobs=JOBS)(delayed(need)(j["alpha_online"], j["scale"]) for j in jobs)
    lottery = pd.DataFrame([dict(j, wait=w, wait_h=w / 3600 if w > 0 else float("nan"))
                            for j, w in zip(jobs, waits)])

    OUT.mkdir(parents=True, exist_ok=True)
    for name, t in (("registry", registry), ("lottery", lottery)):
        t.to_csv(OUT / f"{name}.csv", index=False)
        print(t.to_string(index=False), end="\n\n")


if __name__ == "__main__":
    main()
