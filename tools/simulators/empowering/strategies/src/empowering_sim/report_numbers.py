"""Gate: every headline the strategies report quotes, against the runs that produce it.

    PYTHONPATH=src python3 -m empowering_sim.report_numbers

`validate` pins these same values as literals in its own source, which proves the model has
not moved but says nothing about the document. This asserts the other half: that the tables a
reader actually sees carry the numbers the simulator produces.

The runs here are the published configurations, so they cost about what `validate` costs --
sections 3 and 6 are quick, section 7's two 600-epoch arrival sweeps are the slow part.
"""
from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

import numpy as np

from . import arrivals as ar
from . import economics, elevation as el, strategies as st
from .config import Config, load
from .report_check import NUM, Claim, run

DEFAULT_REPORT = Path("../../../../reports/empowering/strategies/strategies-report.md")

# Sections of the *specification*, not of this report.
ELSEWHERE: set[str] = set()


def _cell(label: str, col: int) -> str:
    """Capture the `col`-th value cell of the table row beginning with `label`."""
    skip = r"\|[^|\n]*" * (col - 1)
    return rf"^\| *{re.escape(label)} *{skip}\| *\**({NUM})"


def build(cfg: Config) -> list[Claim]:
    claims: list[Claim] = []

    # --- section 3: the medians table, at the published configuration -------------------
    pop, _ = st.run(cfg, st.StrategyConfig())
    tot = pop.reward_pow + pop.reward_leader + pop.reward_service
    med = {s: float(np.median(tot[pop.strategy == s.value])) / cfg.base_units_per_lgo
           for s in st.Strategy}
    base = med[st.Strategy.STAKER]
    for label, strat in (("miner", st.Strategy.MINER),
                         ("miner and staker", st.Strategy.MINER_STAKER),
                         ("stakeholder", st.Strategy.STAKER),
                         ("miner, staker and service provider", st.Strategy.MINER_STAKER_SERVICE),
                         ("stakeholder and service provider", st.Strategy.STAKER_SERVICE)):
        claims.append(Claim("3", _cell(label, 1), round(med[strat]), rel=1e-9,
                            note=f"median {label}"))
        claims.append(Claim("3", _cell(label, 2), round(med[strat] / base, 2), rel=6e-3,
                            note=f"ratio {label}"))

    # --- section 6: the elevation regimes, and the pool's clock -------------------------
    persist = el.run(cfg, el.ElevationConfig(miners_per_epoch=100, epochs=400,
                                             retire_on_bond=False))
    retire = el.run(cfg, el.ElevationConfig(miners_per_epoch=100, epochs=400,
                                            retire_on_bond=True))
    ceiling = cfg.genesis_pool / cfg.min_stake
    claims += [
        Claim("6", _cell("keep mining", 1), persist.elevated, rel=1e-9,
              note="elevated, bonded miners keep mining"),
        Claim("6", _cell("keep mining", 2), round(100 * persist.elevated / ceiling, 1),
              rel=6e-3, note="as a share of the 50,000 ceiling"),
        Claim("6", _cell("retire", 1), retire.elevated, rel=1e-9,
              note="elevated, bonded miners retire"),
        Claim("6", _cell("retire", 2), round(100 * retire.elevated / ceiling, 1),
              rel=6e-3, note="as a share of the ceiling"),
        Claim("6", rf"min_stake` is \*\*({NUM})\*\*", ceiling, rel=1e-9,
              note="elevation ceiling"),
    ]
    half = math.log(0.5) / math.log(1 - cfg.distribution_rate)
    ninety = math.log(0.1) / math.log(1 - cfg.distribution_rate)
    claims += [
        Claim("6", rf"half-life is \*\*({NUM}) epochs", round(half), rel=1e-9,
              note="pool half-life"),
        Claim("6", rf"90% depleted after \*\*({NUM}) epochs", round(ninety), rel=1e-9,
              note="90% depletion"),
    ]

    # --- section 7: arrivals as a process ----------------------------------------------
    fast = ar.run_dynamic(cfg, ar.Arrivals(amplitude=50), epochs=600)
    slow = ar.run_dynamic(cfg, ar.Arrivals(amplitude=5), epochs=600)
    # Section 7 carries three tables that all have a "50" row, so each pattern is anchored on
    # the absorption table's own shape: it is the only one whose rows reach a "door closes"
    # cell. Matching on the rate alone would silently assert against the wrong table.
    claims += [
        Claim("7", rf"^\| 50 \| *({NUM}) \|(?:[^|\n]*\|){{2}} *epoch", fast.absorption.seated,
              rel=1e-9, note="seated at fifty arrivals an epoch"),
        Claim("7", rf"^\| 50 \|[^|\n]*\| *({NUM}) \|[^|\n]*\| *epoch",
              fast.absorption.elevated, rel=1e-9, note="elevated at fifty an epoch"),
        Claim("7", rf"^\| 50 \|(?:[^|\n]*\|){{3}} *epoch ({NUM})", fast.absorption.door_epoch,
              rel=1e-9, note="the door closes"),
        Claim("7", rf"^\| 50 \|(?:[^|\n]*\|){{4}} *({NUM}) \|",
              fast.absorption.no_return_epoch, rel=1e-9, note="the point of no return"),
        Claim("7", rf"^\| 5 \|[^|\n]*\| *({NUM}) \|[^|\n]*\| *epoch",
              slow.absorption.elevated, rel=1e-9, note="elevated at five an epoch"),
    ]

    # --- section 11: what one claim is worth -------------------------------------------
    opening = economics.reward_per_claim(cfg.genesis_pool, cfg)
    claims.append(Claim("11", rf"factor of \*\*({NUM})\*\*", opening / cfg.claim_fee,
                        rel=6e-3, note="opening reward over a claim's own fee"))
    return claims


def main() -> int:
    ap = argparse.ArgumentParser(prog="empowering_sim.report-numbers")
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    a = ap.parse_args()
    cfg = load()
    print(f"config: {cfg.label}")
    return run(a.report, build(cfg), elsewhere=ELSEWHERE)


if __name__ == "__main__":
    raise SystemExit(main())
