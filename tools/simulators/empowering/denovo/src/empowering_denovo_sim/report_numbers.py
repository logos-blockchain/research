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

from . import arrivals, engine, power, retirement, study, window
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

    # The acceptance window's headlines. Row data wherever a row already carries the number
    # (offered_mu, claims_paid); one congestion profile where only the queue can say (the
    # expiry and inflation figures). These add several short runs and two 220-epoch ones --
    # the price of the section-4 rewrite being document-gated, not just engine-gated.
    spike30 = {s: engine.run(d, arrivals.spike(220, 130, at=30, factor=100),
                             study.hashrate_draw(cfg, seed=s), epochs=31).rows[30]
               for s in (2, 11, 12345)}
    offered = [r.offered_mu for r in spike30.values()]
    persist = engine.run(d, arrivals.uniform(220, 130), study.hashrate_draw(cfg),
                         epochs=220, retire_on_bond=False)
    c194 = window.congestion_profile(persist.rows, cfg)[194]
    spike35 = engine.run(d, arrivals.spike(220, 130, at=30, factor=100),
                         study.hashrate_draw(cfg), epochs=35)
    c30 = window.congestion_profile(spike35.rows, cfg)[30]
    front = engine.run(d, arrivals.front_loaded(220, 220 * 130),
                       arrivals.pi5_pareto(np.random.default_rng(2),
                                           floor_rate=power.board(cfg).candidates_per_second),
                       epochs=220)

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

        # --- section 4: block space and the acceptance window, priced -------------------
        Claim("4", rf"\*offers\* ({NUM})–", min(offered),
              note="x100 spike epoch, lightest independent draw (unclipped demand)"),
        Claim("4", rf"[\d,]+–({NUM}) claims a block", max(offered),
              note="x100 spike epoch, heaviest independent draw"),
        Claim("4", rf"front-loaded \*\*({NUM}) of its 28,600 arrivals\*\*",
              front.rows[-1].bonds_total, rel=0,
              note="front-loaded onboarding, rationed by the block-space cap"),
        Claim("4", rf"loses \*\*({NUM})% of its solutions\*\*", 100 * c30.expiry_fraction,
              note="the window's tax on the x100 spike, no longer acquitted"),
        Claim("4", rf"burns ×({NUM}) energy per paid claim", c30.inflation,
              note="spike-epoch energy inflation"),
        Claim("4", rf"({NUM}) offered a block queue for", spike30[2].offered_mu,
              note="unclipped spike demand against the 1,024 cap"),
        Claim("4", rf"epoch 194: ({NUM}) offered a block", persist.rows[194].offered_mu,
              note="late persistent endgame, offered past the cap"),
        Claim("4", rf"\*\*({NUM})% of solutions expire\*\*", 100 * c194.expiry_fraction,
              note="the window's congestion tax at its worst"),
        Claim("4", rf"energy per paid claim ×({NUM})", c194.inflation,
              note="offered per paid claim, epoch 194"),
        Claim("4", rf"at \$0\.10 at epoch ({NUM}) instead of 108", 59, rel=0,
              note="the congestion tax closed through the retirement decision; the "
                   "threshold pair (108, 59) is pinned in validate's window gates"),

        # --- section 6: the saturation tail's standing fee ------------------------------
        Claim("6", rf"\*\*({NUM})% of a settled post-phase epoch",
              100 * window.post_tail_loss(ref.rows, cfg),
              note="solutions dead between saturation and the window's grace strip"),

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
