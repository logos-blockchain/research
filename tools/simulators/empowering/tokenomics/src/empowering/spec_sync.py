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
    # "of the supply at network launch" until 2026-09; "of the maximum supply" after PR 400
    # restated the basis as S_cap. Same 10^10, so one config value serves both forms.
    check("POW_REWARD_POOL_GENESIS",
          grab(genesis,
               r"= (\d+)/1000 of the (?:supply at network launch|maximum supply)", "seed"),
          int(p.genesis_pool_fraction * 1000))

    rewards = "block-rewards.md"
    # Two accepted forms: the pre-PR-375 parametrization row anchored the supply as S_tge
    # ("Token supply at TGE"); PR 375 (merged 2026-08-26) removed S_tge and anchors
    # everything to the hard cap ("Maximum token supply (hard cap)"). Numerically identical
    # at the stated 10^10, so one config value serves both forms; PR 400 has since merged
    # master, so current trees all carry the S_cap form and the alternation only serves
    # historical snapshots.
    check("S_tge / S_cap",
          grab(rewards,
               r"(?:Token supply at TGE|Maximum token supply \(hard cap\)) \| (\d+) billion LGO",
               "supply"),
          int(p.S_tge / 1e9))
    rewards_text = read(rewards)
    if rewards_text and "Lifetime of the rewards reserve" in rewards_text:
        # The PR-375 tree only: the reserve-lifetime parameter its Pool Accounting section
        # introduces. Y = 10 sizes the reserve at I_max * S_cap * Y = 10^9 LGO, which is the
        # RESERVE_GENESIS the strategy simulator's emission stocks carry.
        # Accepts both $10$ (the PR head this gate was written against) and $`10`$ (the
        # form the 2026-08-25 pre-merge cleanup switched the whole document to).
        check("Y (reserve lifetime, PR 375)",
              grab(rewards, r"Lifetime of the rewards reserve[^|]*\| \$`?(\d+)`?\$ years", "Y"),
              10)

    blendp = "blend-protocol.md"
    n_b = grab(blendp, r"which translates to \$`([\d,]+)`\$ blocks", "N_b")
    check("blocks per epoch (blend)", n_b, p.N_b)
    crypt = "cryptarchia-v1-protocol.md"
    raw_nb = grab(crypt, r"= 10k = ([0-9{},]+)`\$ blocks", "10k")
    check("blocks per epoch defined in Cryptarchia",
          raw_nb and raw_nb.replace("{", "").replace("}", ""), p.N_b)
    check("blend_ops_per_message",
          grab(blendp, r"beta_\{max\} = (\d+)", "blend ops per message"),
          p.blend_ops_per_message)

    # The reference implementation's constants are all functions of the supply; guard
    # them so a supply revision cannot leave the code behind again.
    import math
    # `int(3e9)` before the merge, `int64(3_000_000_000)` after -- the 2026-08-26 merge of
    # PR 375 rewrote the reference block around numpy int64. Both forms are captured and the
    # comparison is NUMERIC, because the old string comparison ("3e9") broke on a formatting
    # change that moved no value -- which is drift this gate should survive, not report.
    _stake_raw = grab(rewards, r"STAKE_TARGET = int(?:64)?\(([\d_.e+]+)\)", "stake target")
    check("STAKE_TARGET (reference code)",
          _stake_raw and float(_stake_raw.replace("_", "")), 0.3 * p.S_tge)
    infl_num = int(p.I_max * p.S_tge)
    g = math.gcd(infl_num, p.blocks_per_year)
    check("INFLATION_NUMERATOR (reference code)",
          grab(rewards, r"INFLATION_NUMERATOR = (?:int64\()?([\d_]+)\)?", "inflation num"),
          str(infl_num // g))
    check("INFLATION_DENOMINATOR (reference code)",
          grab(rewards, r"INFLATION_DENOMINATOR = (?:int64\()?([\d_]+)\)?", "inflation den"),
          str(p.blocks_per_year // g))
    check("A_SCALE (reference code)",
          grab(rewards, r"A_SCALE = (?:int64\()?([\d_]+)\)?", "a scale"),
          str(int(0.3 * p.S_tge * p.I_max * 4)))

    # --- derived margins ----------------------------------------------------------
    # Until 2026-09-03 these were phrase-plus-value checks against the Mantle text, which
    # stated each margin in prose. PR 400 then moved the design rationale out of the
    # specification into the PR description (`b2f0f941`), so there is no spec sentence left
    # to anchor to and these are now pure value checks: each margin is recomputed from the
    # config and asserted against the range that makes the corresponding claim in our own
    # reports true. Where the range itself moved, the cause is the 2026-09-04 claim change
    # (ZkSignature proof, gas 56 -> 590: the claim fee went from 6,664 to 11,298 lepta) --
    # and the PR description still carries the OLD figures ("6,664 lepta", "about four
    # fifths", "five times the fee at six hundred"), stale against the PR's own change;
    # flagged upstream rather than silently re-anchored here.
    import math

    def derived(label: str, value: float, lo: float, hi: float):
        nonlocal checks
        checks += 1
        if not (lo <= value <= hi):
            failures.append(f"derived margin {label}: recomputed {value:.4g}, "
                            f"outside [{lo:.3g}, {hi:.3g}] — a report claim is stale")

    phi_over_S = p.phi / p.S_tge
    sigma0 = p.rho * p.R0 / (p.T * p.N_b)
    ceiling = (sigma0 / 2) / p.S_tge
    derived("price-discovery headroom, orders of magnitude above the fee floor",
            math.log10(ceiling / phi_over_S), 4.5, 6.0)
    derived("claim fee at the resting prices, lepta (was 6,664 before the ZkSignature)",
            p.phi * p.base_units_per_lgo, 11_297, 11_299)
    R_min = p.phi * p.T * p.N_b / p.rho
    no_traffic_years = math.log(p.R0 / R_min) / -math.log(1 - p.rho) / p.epochs_per_year
    derived("no-traffic seed lifetime stays 'decades'", no_traffic_years, 15, 80)
    derived("u64 headroom over the supply in lepta",
            (2 ** 64 - 1) / (p.S_tge * p.base_units_per_lgo), 1.80, 1.89)

    reaches = 1 - p.T / (p.psi * p.beta * p.n_tx_ref)
    derived("share of the distribution reaching claimants at the reference load "
            "(two thirds since the claim signature; four fifths before)",
            reaches, 0.60, 0.70)
    derived("reward over the claim fee at six hundred transactions "
            "(three times since the claim signature; five before)",
            p.psi * p.beta * 600 / p.T, 2.7, 3.2)
    derived("within-epoch drain requirement, thousands of claims per block",
            p.T * p.rho_den / p.rho_num / 1000, 1.99, 2.01)
    # excess of a 100x-too-permissive genesis target, as a fraction of the pool
    from .core import next_reward_difficulty, sigma as _sigma
    d_eq = P_FIELD >> p.reward_difficulty_exp
    d, excess = int(d_eq * 100), 0
    for _ in range(400):
        c = min(max(0, round(p.T * d / d_eq)), p.max_block_txs)
        excess += max(0, c - p.T)
        d = next_reward_difficulty(d, c, p)
    derived("genesis over-payment, thousandths of one percent of the pool",
            excess * _sigma(p.R0, p) / p.R0 * 1e5, 2.2, 3.8)

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
    require_phrase(mantle, "canonical integer representative")
    poq = "proof-of-quota.md"
    require_phrase(poq, "BLEND_POW_V1")
    require_phrase(poq, "pow_nonce")
    require_phrase(mantle, "one LGO is $`10^{9}`$ lepta")
    require_phrase(mantle, "hi = min(previous * BLEND_MAX_STEP, p - 1)")
    # The unfenced `return min(new_target, p - 1)` until 2026-09; PR 400 then floored the
    # retarget at REWARD_TARGET_FLOOR = ceil(F/(P-F)) = 9 -- the fence our UPSTREAM-PENDING
    # section 4 asked for, with a stronger floor than the max(1, .) we suggested (floors
    # 1..8 form an absorbing band under floor division).
    require_phrase(mantle, "return min(max(new_target, REWARD_TARGET_FLOOR), p - 1)")
    check("REWARD_TARGET_FLOOR",
          grab(mantle, r"REWARD_TARGET_FLOOR: uint64 = (\d+)", "floor"),
          -(-p.F_ema // (p.P_ema - p.F_ema)))
    require_phrase(mantle, "specified over **arbitrary-precision integers**")

    # What the 2026-09 revision of the RFC newly pins, so it cannot quietly un-pin:
    # the carve-out is stated where the fees are routed, the PoW pool joins the conserved
    # total, a claim may straddle one epoch boundary, and the claim is signed.
    require_phrase(rewards, "net of the share diverted to the")
    require_phrase(rewards, "S_t + P_t + B_t + W_t")
    require_phrase(mantle, "found against the current or the previous epoch")
    require_phrase(mantle, "The claim must be signed by the key the reward is paid to")

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
