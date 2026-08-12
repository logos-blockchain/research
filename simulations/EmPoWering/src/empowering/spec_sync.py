"""Drift gate: the config file against the logos-lips specification tree.

The config quotes constants that live in the specifications. This reads them back out
of the specs and fails loudly on any mismatch, so "in sync with the RFC" is a checked
claim rather than a promise. Run after every specification change:

    make check LIPS=/path/to/logos-lips
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from .params import P_FIELD, load


def run(config: str, lips: str) -> int:
    p = load(config)
    raw = Path(lips) / "docs" / "blockchain" / "raw"
    if not raw.is_dir():
        print(f"specification tree not found at {raw}")
        return 2
    failures, checks = [], 0

    def read(fname: str) -> str | None:
        try:
            return (raw / fname).read_text()
        except OSError:
            failures.append(f"specification file missing or unreadable: {fname}")
            return None

    def grab(fname: str, pattern: str, label: str):
        text = read(fname)
        if text is None:
            return None
        m = re.search(pattern, text)
        if not m:
            failures.append(f"could not find {label} in {fname}")
            return None
        return m.group(1)

    def check(label: str, got, want):
        nonlocal checks
        checks += 1
        if got is not None and str(got).replace(",", "").replace("_", "") != str(want):
            failures.append(f"{label}: spec says {got!r}, config has {want!r}")

    mantle = "bedrock-v1.1-mantle-specification.md"
    check("TARGET_CLAIMS_PER_BLOCK",
          grab(mantle, r"TARGET_CLAIMS_PER_BLOCK: uint64 = (\d+)", "T"), p.T)
    check("POW_SHARE", grab(mantle, r"POW_SHARE: uint64 = (\d+)", "share"), p.beta_num)
    check("SHARE_DEN", grab(mantle, r"SHARE_DEN: uint64 = (\d+)", "den"), p.beta_den)
    check("RATE_NUM",
          grab(mantle, r"EPOCH_POW_DISTRIBUTION_RATE_NUM: uint64 = (\d+)", "rho num"),
          p.rho_num)
    check("RATE_DEN",
          grab(mantle, r"EPOCH_POW_DISTRIBUTION_RATE_DEN: uint64 = (\d+)", "rho den"),
          p.rho_den)
    check("EMA_SMOOTHING_FACTOR",
          grab(mantle, r"EMA_SMOOTHING_FACTOR: uint64 = (\d+)", "F"), p.F_ema)
    check("EMA_SMOOTHING_PRECISION",
          grab(mantle, r"EMA_SMOOTHING_PRECISION: uint64 = (\d+)", "P"), p.P_ema)
    check("BLEND_DIFFICULTY_BASE exponent",
          grab(mantle, r"BLEND_DIFFICULTY_BASE: PowTarget = p // 2\*\*(\d+)", "base"),
          p.blend_base_exp)
    check("TARGET_TXS_PER_BLOCK",
          grab(mantle, r"TARGET_TXS_PER_BLOCK: uint64 = (\d+)", "blend target"),
          p.blend_target_txs)
    check("BLEND_DAMPING_NUM",
          grab(mantle, r"BLEND_DAMPING_NUM: uint64 = (\d+)", "a"), p.blend_damping_num)
    check("BLEND_DAMPING_DEN",
          grab(mantle, r"BLEND_DAMPING_DEN: uint64 = (\d+)", "b"), p.blend_damping_den)
    check("BLEND_MAX_STEP",
          grab(mantle, r"BLEND_MAX_STEP: uint64 = (\d+)", "step"), p.blend_max_step)
    check("reward genesis exponent",
          grab(mantle, r"scalar field modulus divided by \$`2\^\{(\d+)\}`\$", "genesis d"),
          p.reward_difficulty_exp)

    gas = "analysis-gas-cost-determination.md"
    check("CLAIM_POW_REWARD_GAS + TRANSFER_GAS",
          grab(gas, r"CLAIM_POW_REWARD_GAS\s+= (\d+)", "claim gas"),
          p.claim_tx_gas - p.transfer_tx_gas)
    check("TRANSFER_GAS",
          grab(gas, r"\bTRANSFER_GAS\s+= (\d+)", "transfer gas"), p.transfer_tx_gas)

    genesis = "bedrock-genesis-block.md"
    check("POW_REWARD_POOL_GENESIS",
          grab(genesis, r"= (\d+)/1000 of the supply at network launch", "seed"),
          int(p.genesis_pool_fraction * 1000))

    rewards = "block-rewards.md"
    check("S_tge",
          grab(rewards, r"Token supply at TGE \| (\d+) billion LGO", "supply"),
          int(p.S_tge / 1e9))

    blendp = "blend-protocol.md"
    n_b = grab(blendp, r"which translates to \$`([\d,]+)`\$ blocks", "N_b")
    check("blocks per epoch", n_b, p.N_b)
    check("beta_max", grab(blendp, r"beta_\{max\} = (\d+)", "beta_max"), p.beta_max)

    # The reference implementation's constants are all functions of the supply; guard
    # them so a supply revision cannot leave the code behind again.
    import math
    check("STAKE_TARGET (reference code)",
          grab(rewards, r"STAKE_TARGET = int\((\S+)\)", "stake target"),
          f"{0.3 * p.S_tge:.0e}".replace("e+", "e").replace("e0", "e"))
    infl_num = int(p.I_max * p.S_tge)
    g = math.gcd(infl_num, p.blocks_per_year)
    check("INFLATION_NUMERATOR (reference code)",
          grab(rewards, r"INFLATION_NUMERATOR = ([\d_]+)", "inflation num"),
          str(infl_num // g))
    check("INFLATION_DENOMINATOR (reference code)",
          grab(rewards, r"INFLATION_DENOMINATOR = ([\d_]+)", "inflation den"),
          str(p.blocks_per_year // g))
    check("A_SCALE (reference code)",
          grab(rewards, r"A_SCALE = ([\d_]+)", "a scale"),
          str(int(0.3 * p.S_tge * p.I_max * 4)))

    # --- derived margins the specifications state in prose ------------------------
    # These are the sentences no constant-level gate covers: each is recomputed from
    # the config and asserted against the exact wording, so a parameter change that
    # invalidates a margin fails here instead of leaving stale prose behind.
    import math

    def margin(fname: str, phrase: str, value: float, lo: float, hi: float):
        nonlocal checks
        checks += 1
        text = read(fname)
        if text is None:
            return
        if phrase not in text:
            failures.append(f"margin phrase missing from {fname}: {phrase!r}")
        elif not (lo <= value <= hi):
            failures.append(f"margin {phrase!r}: recomputed {value:.3g}, "
                            f"outside [{lo:.3g}, {hi:.3g}] — prose is stale")

    phi_over_S = p.phi / p.S_tge
    sigma0 = p.rho * p.R0 / (p.T * p.N_b)
    ceiling = (sigma0 / 2) / p.S_tge                       # the stated 1.157e-10 form
    import math as _m
    margin(mantle, "five orders of magnitude above the floor",
           _m.log10(ceiling / phi_over_S), 4.5, 6.0)
    margin(mantle, "6,664 lepta", p.phi * p.base_units_per_lgo, 6663, 6665)
    R_min = p.phi * p.T * p.N_b / p.rho
    no_traffic_years = math.log(p.R0 / R_min) / -math.log(1 - p.rho) / p.epochs_per_year
    margin(mantle, "for decades", no_traffic_years, 15, 40)
    margin(mantle, "a factor of only $`1.84`$",
           (2 ** 64 - 1) / (p.S_tge * p.base_units_per_lgo), 1.80, 1.89)

    reaches = 1 - p.T / (p.psi * p.beta * p.n_tx_ref)
    margin(mantle, "about four fifths of the distribution reaching claimants",
           reaches, 0.75, 0.85)
    margin(mantle, "five times the fee at six hundred",
           p.psi * p.beta * 600 / p.T, 4.5, 5.5)
    margin(mantle, "a thousand claims in every block",
           p.T * p.rho_den / p.rho_num / 1000, 0.99, 1.01)
    # excess of a 100x-too-permissive genesis target, as a fraction of the pool
    from .core import next_reward_difficulty, sigma as _sigma
    d_eq = P_FIELD >> p.reward_difficulty_exp
    d, excess = int(d_eq * 100), 0
    for _ in range(400):
        c = min(max(0, round(p.T * d / d_eq)), p.max_block_txs)
        excess += max(0, c - p.T)
        d = next_reward_difficulty(d, c, p)
    margin(mantle, "six thousandths of one percent of the genesis pool",
           excess * _sigma(p.R0, p) / p.R0 * 1e5, 4.5, 7.5)

    def require_phrase(fname: str, phrase: str):
        nonlocal checks
        checks += 1
        text = read(fname)
        if text is not None and phrase not in text:
            failures.append(f"guarantee phrase missing from {fname}: {phrase!r}")

    # robustness guarantees the specification must keep stating
    require_phrase(mantle, "losing less than one lepton per block")
    require_phrase(mantle, "conservation bounds every such aggregate")
    require_phrase(mantle, "validated against the target produced by the previous block")
    require_phrase(mantle, "one LGO is $`10^{9}`$ lepta")
    require_phrase(mantle, "hi = min(previous * BLEND_MAX_STEP, p - 1)")
    require_phrase(mantle, "return min(new_target, p - 1)")
    require_phrase(mantle, "are specified over unbounded integers")

    print(f"{checks} checks against {raw}")
    if failures:
        for f in failures:
            print(f"  DRIFT  {f}")
        return 1
    print("  all in sync")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="empowering.spec_sync")
    ap.add_argument("--config", required=True)
    ap.add_argument("--lips", required=True, help="path to the logos-lips checkout")
    a = ap.parse_args()
    return run(a.config, a.lips)


if __name__ == "__main__":
    sys.exit(main())
