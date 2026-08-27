"""Gate: every headline the de-novo report quotes, against the runs that produce it.

    PYTHONPATH=src:../strategies/src python3 -m empowering_denovo_sim.report_numbers
    make report-numbers

`validate` pins these values as literals in its own source, which proves the engine has not
moved but says nothing about the document. This asserts the other half.

The engine is `empowering_sim.report_check`, shared with the strategies report so the two are
gated by one implementation rather than by two that drift apart.

**The two bonds figures come from different experiments, and that matters.** 24,707 is the
reference run with retirement imposed; 7,963 is the run where each bonded miner re-decides
every epoch against its own income and electricity, and chooses to keep mining. Anchoring the
second to `retire_on_bond=False` instead looks right and is not -- that is a third experiment,
and it lands near 5,600. Each run below draws from its own generator, so neither depends on
what ran before it.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from empowering_sim.report_check import NUM, Claim, run

from . import arrivals, engine, power, retirement, study
from .params import Triple

DEFAULT_REPORT = Path("../../../../reports/empowering/denovo/denovo-report.md")

# Section numbers belonging to the other documents this report cites: design-comparison's §0,
# MAPPING's §1.1, adversarial-analysis's §2.3/§3.3/§3.4/§4.2, and MODEL's §8.3/§8.5.
ELSEWHERE = {"0", "1.1", "2.3", "3.3", "3.4", "4.2", "8.3", "8.5"}


def build() -> list[Claim]:
    d = Triple().derived().check()
    cfg = d.cfg
    lgo = cfg.base_units_per_lgo

    # Retirement imposed: the regime the triple bets on.
    draw = arrivals.pi5_pareto(np.random.default_rng(2),
                               floor_rate=power.board(cfg).candidates_per_second)
    ref = engine.run(d, arrivals.uniform(220, 130), draw, epochs=220)
    retiring = ref.rows[-1].bonds_total

    # Retirement decided: each bonded miner re-decides each epoch, and mining wins.
    decided = engine.run(d, arrivals.uniform(220, 130), study.hashrate_draw(cfg),
                         epochs=240, retirement_policy=retirement.Rational())
    persistent = decided.rows[-1].bonds_total
    intent = d.triple.expected_nodes

    return [
        # --- section 3: the reference run -----------------------------------------------
        Claim("3", rf"epoch \*\*({NUM}) exactly\*\*", d.bootstrap_epochs, rel=1e-9,
              note="the endowment's schedule hits zero"),
        Claim("3", rf"reward opens at \*\*({NUM}) LGO\*\*",
              round(d.opening_reward() / lgo, 2), rel=1e-9, note="opening reward"),
        Claim("3", rf"opening sub-pool of ({NUM}) LGO", d.opening_sub_pool() // lgo,
              rel=1e-9, note="opening sub-pool"),
        Claim("3", rf"lands \*\*({NUM}) bonds", retiring, rel=1e-9,
              note="bonds delivered when bonded miners retire"),
        Claim("3", rf"against the ({NUM}) intent", intent, rel=1e-9,
              note="the triple's intent"),
        Claim("3", rf"same triple delivers ({NUM})", persistent, rel=1e-9,
              note="bonds delivered under persistence"),

        # --- section 4: the same two numbers, in the arrival-shape table ----------------
        # Cross-section, deliberately: section 3 and section 4 quote the same reference run,
        # and an edit that moves one without the other is exactly the drift worth catching.
        Claim("4", rf"^\| uniform \| *({NUM})", retiring, rel=1e-9,
              note="uniform arrivals, retiring"),
        Claim("4", rf"^\| uniform \|[^|\n]*\| *({NUM})", persistent, rel=1e-9,
              note="uniform arrivals, persistent"),

        # --- section 10: and again in the requirements table ----------------------------
        Claim("10", rf"R3 onboarding[^|\n]*\|[^|\n]*\| ({NUM}) bonds", retiring, rel=1e-9,
              note="R3, as validated"),
        Claim("10", rf"R3 onboarding[^|\n]*\|[^|\n]*\|[^|\n]*?against a ({NUM}) intent",
              intent, rel=1e-9, note="R3 intent, as validated"),
        Claim("10", rf"R2 two regimes[^|\n]*\|[^|\n]*\|[^|\n]*?epoch ({NUM}) exactly",
              d.bootstrap_epochs, rel=1e-9, note="R2 transition, as validated"),
    ]


def main() -> int:
    ap = argparse.ArgumentParser(prog="empowering_denovo_sim.report-numbers")
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    a = ap.parse_args()
    return run(a.report, build(), elsewhere=ELSEWHERE)


if __name__ == "__main__":
    raise SystemExit(main())
