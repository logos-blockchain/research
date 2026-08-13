"""Gate: every number the report quotes, checked against the model that produces it.

`check` ties the config to the specification tree and `verify` ties the model to its closed
forms. Between the model and the *document* there was nothing, which is how sections 3.7,
4.1 and 4.2 came to state conclusions that were arithmetically correct for the parameter
set they were run against and then went stale in place when section 0.1 moved the
denomination. This closes that gap.

Each claim below names a phrase that appears in the report, a pattern locating the number
inside it, and the model expression that must produce it. A drifted number fails here
rather than surviving until a reader notices.

**Superseded numbers are checked too, in the other direction.** The body deliberately keeps
sections 3.7, 4.1 and 4.2 as written and flags them from section 0.3, so their old figures
must NOT be asserted against the model. What is asserted instead is that section 0.3 states
the corrected values, and that each superseded section still carries its banner -- removing
a banner without removing the stale numbers under it is itself a failure.

    python -m empowering.report_numbers --config configs/specified.toml
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from . import core
from .params import Params, load

DEFAULT_REPORT = Path("../../reports/EmPoWering/tokenomics/tokenomics-model.md")
NUM = r"[-+]?[\d,]+(?:\.\d+)?"


@dataclass(frozen=True)
class Claim:
    """One quoted number: where it appears, and what the model says it should be."""
    section: str
    pattern: str            # regex with exactly one capture group around the number
    expected: float
    rel: float = 5e-3       # the report rounds, so compare relatively by default
    note: str = ""


def _parse(raw: str) -> float:
    return float(raw.replace(",", "").replace("\u2212", "-").strip())


def split_sections(text: str) -> dict[str, str]:
    """Map each section number to its own text, so a claim is checked where it is stated.

    Without this, a pattern like ``| 0 | 0.00 | ... |`` matches both §0.3's corrected table
    and the superseded one in §3.7 -- exactly the confusion this gate exists to prevent.
    """
    heads = list(re.finditer(r"^#{2,4} +(\d+(?:\.\d+)*)[. ]", text, re.M))
    out: dict[str, str] = {}
    for i, m in enumerate(heads):
        end = heads[i + 1].start() if i + 1 < len(heads) else len(text)
        out[m.group(1)] = text[m.start():end]
    return out


def build(p: Params) -> list[Claim]:
    """The claims, derived from `p` so a config change moves the expectations too."""
    rows = core.simulate_pool(p, epochs=int(40 * p.epochs_per_year))
    s0_over_phi = rows[0]["sigma_over_phi"]
    edge_launch = 1 + 0.5 / (s0_over_phi - 1)
    r_star, r_min = core.r_star(p), core.r_min(p)
    ratio = p.R0 / r_star
    import math
    yrs_to_2x = (math.log(ratio - 1) / -math.log(1 - p.rho)) / p.epochs_per_year
    half_life = math.log(2) / -math.log(1 - p.rho)
    annual = 1 - (1 - p.rho) ** p.epochs_per_year
    blend_attempts = 2.0 ** p.blend_base_exp
    blend_secs = blend_attempts * p.sec_per_candidate
    deflation = (p.r_max * p.base_units_per_lgo) / (p.max_block_txs
                                                    * (p.transfer_tx_bytes + p.transfer_tx_gas))
    ramp5 = core.min_endowment_for_ramp(p, 5.0)

    return [
        # --- the claim transaction and its ratios (section 4.3) ---
        Claim("4.3", r"encoded `SignedMantleTx`\*\* \| \*\*(" + NUM + r") B\*\*",
              p.claim_tx_bytes, 0),
        Claim("4.3", r"\*\*encoded `SignedMantleTx`\*\* \| \*\*\d+ B\*\* \| \*\*(" + NUM + r")\*\*",
              p.claim_tx_gas, 0),
        Claim("4.3", r"`306 · 7 \+ 646 · 7 = (" + NUM + r")` price units",
              p.phi * p.base_units_per_lgo, 0),
        Claim("4.3", r"or (" + NUM + r") at the bare floor",
              p.claim_fee(p.price_floor) * p.base_units_per_lgo, 0),
        Claim("4.3", r"comes to 207 B and 590 gas, or (" + NUM + r") units at rest",
              p.transfer_fee() * p.base_units_per_lgo, 0),
        Claim("4.3", r"\\psi \\;=\\; \\frac\{\\bar\\varphi\}\{\\varphi_\\text\{claim\}\} "
                     r"\\;\\approx\\; (" + NUM + r")", p.psi, 2e-3),

        # --- pool dynamics (section 3) ---
        Claim("3.1", r"half-life \*\*(" + NUM + r") epochs", half_life, 5e-3),
        Claim("3.1", r"half-life \*\*\d+ epochs ≈ (" + NUM + r") years",
              half_life / p.epochs_per_year, 5e-3),
        Claim("3.1", r"annual decay \*\*−(" + NUM + r") ?%", annual * 100, 5e-3),
        Claim("3.2", r"— (" + NUM + r") base units at `T = 10`", p.T * p.N_b, 0),
        Claim("4.4.3", r"(" + NUM + r") claims per block against a capacity",
              p.T * p.rho_den / p.rho_num, 0),
        Claim("3.8", r"that is `T/ρ = (" + NUM + r")` claims", p.T * p.rho_den / p.rho_num, 0,
              note="optional: 3.8 phrasing"),
        # the hard edge is on rho itself: drain is reachable once rho >= T/MAX_BLOCK_TXS
        Claim("4.4.3", r"`ρ < T/MAX_BLOCK_TXS = (" + NUM + r") ?%`",
              100 * p.T / p.max_block_txs, 5e-3),

        # --- emission (section 3.4 / 0.1) ---
        Claim("0.1", r"emission cap at ~(" + NUM + r") lepta/gas", deflation, 5e-3),
        Claim("0.1", r"lepta/gas, (" + NUM + r")× the resting level",
              deflation / p.price_resting, 5e-3),
        Claim("0.1", r"`φ` at the resting floor is (" + NUM + r") lepta",
              p.phi * p.base_units_per_lgo, 0),

        # --- section 0.3: the corrected figures for the superseded sections ---
        Claim("0.3", r"`R₀/R\* = (" + NUM + r")` at the resting price", ratio, 5e-3),
        Claim("0.3", r"\| 0 \| 0\.00 \| (" + NUM + r") \|",
              core.sigma(p.R0, p) * p.base_units_per_lgo, 5e-3),
        Claim("0.3", r"\| 0 \| 0\.00 \| [\d,]+ \| (" + NUM + r")× \|", s0_over_phi, 5e-3),
        Claim("0.3", r"\| ∞ \| — \| (" + NUM + r") \|",
              core.sigma_over_phi(p) * p.phi * p.base_units_per_lgo, 5e-3),
        Claim("0.3", r"\| launch \| [\d,]+× \| \*\*(" + NUM + r")×\*\*", edge_launch, 1e-4),
        Claim("0.3", r"\| steady state \| [\d.]+× \| \*\*(" + NUM + r")×\*\*",
              core.builder_edge(p), 1e-4),
        Claim("0.3", r"pool distributes \*\*(" + NUM + r") ?%\*\* of supply over",
              _distributed_pct(p), 2e-2),

        # --- section 4.7: the figures added with the validation plots ---
        Claim("4.7.1", r"\| 7 \(resting\) \| 1× \| (" + NUM + r") \|", r_star, 5e-3),
        Claim("4.7.1", r"\| 7 \(resting\) \| 1× \| [\d,]+ \| [\d,]+ \| \*\*(" + NUM + r")\*\*",
              yrs_to_2x, 1e-2),
        Claim("4.7.2", r"`ψβ = (" + NUM + r") ?%` of transactions", 100 * p.psi * p.beta, 5e-3),
        Claim("4.7.2", r"the break-even traffic is (" + NUM + r") tx/block",
              p.T / (p.psi * p.beta), 5e-3),
        Claim("4.7.2", r"the network operates at `v = (" + NUM + r") ?%`",
              100 * p.T / p.n_tx_ref, 5e-3),
        Claim("4.7.2", r"a \*\*(" + NUM + r")× margin\*\* below the ceiling",
              core.sigma_over_phi(p), 5e-3),
        Claim("4.7.3", r"break-even traffic is 597 tx/block against a reference of (" + NUM + r")",
              p.n_tx_ref, 0),
        Claim("4.7.4", r"\*\*(" + NUM + r")× the 5-year minimum\*\*", p.R0 / ramp5, 1e-2),
        Claim("4.7.6", r"admissible band is \*\*`β ∈ \[(" + NUM + r") ?%",
              100 * 2 * p.T / (p.psi * p.n_tx_ref), 1e-2),
        Claim("4.7.6", r"needs `T/ρ` claims in every block for a whole epoch: (" + NUM + r")",
              p.T * p.rho_den / p.rho_num, 0),

        Claim("0.3", r"model now gives \*\*(" + NUM + r")×10⁻⁶ ?%\*\*",
              100 * r_star / p.S_tge * 1e6, 5e-3),
        Claim("0.3", r"and \*\*(" + NUM + r")×10⁻⁶ ?%\*\*: the reserve",
              100 * r_min / p.S_tge * 1e6, 5e-3),
        Claim("0.3", r"the reserve is (" + NUM + r") LGO", r_star, 5e-3),
        Claim("0.3", r"and the floor (" + NUM + r") LGO", r_min, 5e-3),

        # --- blend admission (section 0.0 / 4.5) ---
        Claim("0.0", r"~50 s and ~(" + NUM + r") messages/day per core",
              86400 / blend_secs, 2e-2),
        Claim("0.0", r"optimiser's edge (" + NUM + r")×",
              p.sec_per_candidate / p.sec_per_candidate_opt, 5e-3),
        Claim("4.5", r"threshold `p/2\^\{?19\}?`?: ?(" + NUM + r") expected candidates",
              blend_attempts, 5e-3, note="optional: phrasing varies"),

        # --- the pieces section 4.7.1 quotes about the floor ---
        Claim("4.7.1", r"`R\*` \((" + NUM + r")\) sits above `R_min`", r_star, 5e-3),
        Claim("4.7.1", r"sits above `R_min` \((" + NUM + r")\)", r_min, 5e-3),
    ]


def _distributed_pct(p: Params) -> float:
    rows = core.simulate_pool(p)
    return 100 * sum(p.T * p.N_b * r["sigma"] for r in rows if r["enabled"]) / p.S_tge


# Sections the body deliberately keeps as written, each flagged from 0.3. The banner must
# stay: dropping it without dropping the stale numbers beneath it is the failure mode.
SUPERSEDED = {
    "3.7": "Superseded in its conclusion by §0.3",
    "4.1": "Figures superseded by §0.3",
    "4.2": "Part (c) superseded by §0.3",
}


def run(config: str, report: Path) -> int:
    p = load(config)
    try:
        text = report.read_text()
    except OSError as e:
        print(f"cannot read report: {e}", file=sys.stderr)
        return 2

    failures, missing, checked = [], [], 0
    sections = split_sections(text)
    print(f"report numbers: {report}\nagainst config: {p.name}\n")

    for c in build(p):
        scope = sections.get(c.section)
        if scope is None:
            missing.append((c, 0))
            print(f"  MISS  §{c.section:<6} no such section in the report")
            continue
        found = re.findall(c.pattern, scope)
        if len(found) != 1:
            if "optional" in c.note:
                continue
            missing.append((c, len(found)))
            print(f"  MISS  §{c.section:<6} pattern matched {len(found)}x (want 1): {c.pattern[:58]}")
            continue
        checked += 1
        got = _parse(found[0])
        ok = (got == c.expected if c.rel == 0
              else abs(got - c.expected) <= c.rel * max(abs(c.expected), 1e-12))
        if not ok:
            failures.append((c, got))
        flag = "PASS" if ok else "FAIL"
        detail = f"report {got:,.6g} vs model {c.expected:,.6g}"
        print(f"  {flag}  §{c.section:<6} {detail}")

    print()
    for sec, banner in SUPERSEDED.items():
        ok = banner in text
        print(f"  {'PASS' if ok else 'FAIL'}  §{sec:<6} supersession banner present")
        if not ok:
            failures.append((Claim(sec, banner, 0), 0))

    print()
    if missing:
        print(f"{len(missing)} pattern(s) did not match exactly once — the report's wording moved,")
        print("so the gate can no longer find the number. Re-anchor the pattern or fix the text.")
    if failures:
        print(f"{len(failures)} number(s) drifted from the model.")
    if not missing and not failures:
        print(f"all {checked} quoted numbers match the model")
    return 1 if (failures or missing) else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="empowering.report-numbers")
    ap.add_argument("--config", default="configs/specified.toml")
    ap.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    a = ap.parse_args()
    return run(a.config, a.report)


if __name__ == "__main__":
    raise SystemExit(main())
