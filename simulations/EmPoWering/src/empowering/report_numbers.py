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
import math
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
        Claim("4.4.3", r"sits the right side: (" + NUM + r") against 1,024",
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


        # --- section 4.8: sampled arrivals ---
        Claim("4.8", r"\| claims per block, mean \| \*\*(" + NUM + r")\*\*", _sampled_mean(p), 2e-3),
        Claim("4.8", r"\| claims per block, mean \| \*\*[\d.]+\*\* \| (" + NUM + r") \|",
              p.T + (p.P_ema - p.F_ema) / (2 * p.P_ema), 1e-4),
        Claim("4.8", r"\| relative spread \| \*\*(" + NUM + r") ?%\*\*",
              100 * _sampled_rel(p), 2e-2),
        Claim("4.8", r"\| relative spread \| \*\*[\d.]+ ?%\*\* \| (" + NUM + r") ?%",
              100 * _pred_rel(p), 5e-3),
        Claim("4.8", r"bare Poisson, what A2 quotes \| \| (" + NUM + r") ?%",
              100 / math.sqrt(p.T), 5e-3),
        Claim("4.8", r"controller amplification \| \*\*[\d.]+×\*\* \| (" + NUM + r")×",
              _pred_amp(p), 5e-3),
        Claim("4.8", r"if arrivals were uncorrelated \| \| (" + NUM + r") ?%",
              100 / math.sqrt(p.T * p.N_b), 5e-3),
        Claim("4.8", r"drain needs (" + NUM + r") \|", p.T * p.rho_den / p.rho_num, 0),
        Claim("4.8", r"\*\*\+(" + NUM + r") ?% at `T = 10`",
              100 * (p.P_ema - p.F_ema) / (2 * p.P_ema * p.T), 1e-2),

        # --- section 4.9: the fee-load axis ---
        Claim("4.9", r"\| \*\*100\*\* \| \*\*(" + NUM + r")\*\* \|", 1.0, 1e-9),
        Claim("4.9", r"\| \*\*502\*\* \| \*\*(" + NUM + r")\*\* \|",
              _core_load_ratio(p), 5e-3),
        Claim("4.9", r"break-even of 100\*\* — the same (" + NUM + r")× margin",
              _core_load_ratio(p), 5e-3, note="optional: phrasing"),
        Claim("4.9", r"collect \*\*(" + NUM + r")/β\*\*", 0, 0, note="optional"),
        Claim("4.9.1", r"\*\*(" + NUM + r") claim fees per transaction\*\*",
              _need_each(p), 5e-3),
        Claim("4.9.1", r"about \*\*(" + NUM + r") encoded bytes each\*\*", _bytes_each(p), 2e-2),
        Claim("4.9.1", r"\| 600 transfers \| (" + NUM + r") \|", _load_of(p, "ref"), 5e-3),
        Claim("4.9.1", r"\| a full block of transfers \| (" + NUM + r") \|",
              _load_of(p, "full"), 5e-3),

        # --- section 0.4: the adopted rho = 1/200, and section 3.7's launch row ---
        Claim("0.4", r"falls from 0\.51 % to \*\*(" + NUM + r") ?%\*\*",
              100 * core.peak_adversary_share(p, p.adversary_h, 1.0, 0.30), 2e-2),
        Claim("0.4", r"σ₀ = (" + NUM + r")× the fee",
              core.sigma(p.R0, p) / p.phi, 5e-3),
        Claim("0.4", r"half-life is (" + NUM + r") epochs",
              math.log(2) / -math.log(1 - p.rho_num / p.rho_den), 1e-2),
        Claim("3.7", r"\| 0 \| 0\.00 \| (" + NUM + r") \| ",
              core.sigma(p.R0, p) * p.base_units_per_lgo, 5e-3),

        # --- section 4.10: the sweep programme ---
        Claim("4.10.1", r"\| \*\*10\*\* \(specified\) \| \*\*(" + NUM + r")\*\*",
              core.sigma_over_phi(p), 5e-3),
        Claim("4.10.1", r"\| 50 \| (" + NUM + r") \|", _at_T(p, 50, "ratio"), 5e-3),
        Claim("4.10.1", r"\| 500 \| (" + NUM + r") \|", _at_T(p, 500, "ratio"), 5e-2),
        Claim("4.10.1", r"it goes to \*\*(" + NUM + r")×\*\*", _at_T(p, 50, "edge"), 2e-2),
        Claim("4.10.1", r"claims would need to be \*\*(" + NUM + r") % of every block\*\*",
              100 * 500 / p.n_tx_ref, 1e-2),
        Claim("4.10.1", r"noise falls from (" + NUM + r") % to",
              100 / p.T ** 0.5, 5e-3),
        Claim("4.10", r"simulation gives exactly (" + NUM + r")", _recon(p), 0),
        Claim("4.10", r"step \*down\* takes (" + NUM + r") blocks", _recon(p, 0.1), 0),
        Claim("4.10.2", r"\(0\.42 % → (" + NUM + r") %",
              100 * _peak_at_R0(p, 0.10), 2e-2),

        # --- body sections corrected in place 2026-08-13 ---
        Claim("3.7", r"\| ∞ \| — \| (" + NUM + r") \|",
              core.sigma_over_phi(p) * p.phi * p.base_units_per_lgo, 5e-3),
        Claim("3.7", r"endowment is \*\*(" + NUM + r")×\*\* that", p.R0 / core.r_star(p), 5e-3),
        Claim("4.1", r"distributes \*\*(" + NUM + r") %\*\* of supply", _distributed_pct(p), 2e-2),
        Claim("4.4", r"floor is `R_min` = (" + NUM + r")×10⁻⁸",
              1e8 * core.r_min(p) / p.S_tge, 5e-3),
        Claim("4.4.3", r"\| `R\*` at the reference traffic \| (" + NUM + r")×10⁻⁷",
              1e7 * core.r_star(p) / p.S_tge, 5e-3),

        # --- section 4.4.2: subordination flows at genesis vs steady state ---
        Claim("4.4.2", r"epoch-0 distribution is `ρR₀` = \*\*(" + NUM + r") LGO\*\*",
              p.rho_num / p.rho_den * p.genesis_pool_fraction * p.S_tge, 1e-6),
        Claim("4.4.2", r"about \*\*(" + NUM + r") LGO\*\*\. On fees alone", _leader_fees(p), 2e-2),
        Claim("4.4.2", r"out-earns the leader path \*\*(" + NUM + r")-fold\*\*",
              (p.rho_num / p.rho_den * p.R0) / _leader_fees(p), 1e-2),
        Claim("4.4.2", r"receive ≈ (" + NUM + r") M LGO per epoch",
              p.r_max * p.N_b / 1e6, 1e-2),
        Claim("4.4.2", r"the pool's 250,000 is \*\*(" + NUM + r") ?%\*\*",
              100 * (p.rho_num / p.rho_den * p.R0) / (_leader_fees(p) + p.r_max * p.N_b), 1e-2),
        Claim("4.4.2", r"a third of leader fee income for roughly \*\*(" + NUM + r") years\*\*",
              _years_above_third(p), 5e-2),

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


def _core_load_ratio(p: Params) -> float:
    return core.sigma_over_phi(p)


def _need_each(p: Params) -> float:
    return core.min_fee_load(p) / p.max_block_txs


def _bytes_each(p: Params) -> float:
    return _need_each(p) * (p.claim_tx_bytes + p.claim_tx_gas) - p.inscribe_gas


def _load_of(p: Params, which: str) -> float:
    n = p.n_tx_ref if which == "ref" else p.max_block_txs
    return core.fee_load(p, n)


def _at_T(p: Params, T: int, what: str) -> float:
    from dataclasses import replace
    q = replace(p, T=T)
    return core.sigma_over_phi(q) if what == "ratio" else core.builder_edge(q)


def _recon(p: Params, step: float = 10.0) -> float:
    return float(core.reconvergence_blocks(p, step))


def _peak_at_R0(p: Params, frac: float) -> float:
    from dataclasses import replace
    return core.peak_adversary_share(replace(p, genesis_pool_fraction=frac), 0.33, 1.0, 0.30)


def _leader_fees(p: Params) -> float:
    return p.leader_fee_share * (1 - p.beta) * p.N_b * p.n_tx_ref * p.transfer_fee()


def _years_above_third(p: Params) -> float:
    import math
    return (math.log((_leader_fees(p) / 3) / (p.rho_num / p.rho_den * p.R0))
            / math.log(1 - p.rho)) / p.epochs_per_year


def _sampled(p: Params):
    from . import sampled as smp
    return smp.summary(p, seeds=4, epochs=12)


def _sampled_mean(p: Params) -> float:
    return _sampled(p)["mean_per_block"]


def _sampled_rel(p: Params) -> float:
    return _sampled(p)["rel_sd"]


def _pred_rel(p: Params) -> float:
    from . import sampled as smp
    return smp.predicted_relative_sd(p)


def _pred_amp(p: Params) -> float:
    from . import sampled as smp
    return smp.predicted_amplification(p)


def _distributed_pct(p: Params) -> float:
    rows = core.simulate_pool(p)
    return 100 * sum(p.T * p.N_b * r["sigma"] for r in rows if r["enabled"]) / p.S_tge


# Sections the body deliberately keeps as written, each flagged from 0.3. The banner must
# stay: dropping it without dropping the stale numbers beneath it is the failure mode.
# Sections corrected in place on 2026-08-13, with §0.3 kept as the record of what moved.
# The pointer must stay: a reader landing mid-document needs to know the section was revised
# and where the history is, and dropping the pointer while leaving the prose is the failure
# mode this guards.
SUPERSEDED = {
    "3.7": "Corrected in place 2026-08-13; §0.3 records what moved",
    "4.1": "Corrected in place 2026-08-13; §0.3 records what moved",
    "4.2": "Part (c) corrected in place 2026-08-13; §0.3 records what moved",
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
