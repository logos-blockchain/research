"""Self-test: the closed forms of the report against the simulation, and the config
against the specification's own invariants. Exits non-zero on any failure.

Run with:  python -m empowering.verify --config configs/specified.toml
"""
from __future__ import annotations

import argparse
import sys

from . import core
from .params import P_FIELD, load


def run(config: str) -> int:
    p = load(config)
    failures = []

    def check(name: str, ok: bool, note: str = ""):
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f": {note}" if note else ""))
        if not ok:
            failures.append(name)

    print(f"verify against {p.name}\n")

    # 1. The pool trajectory tracks the closed form sigma_e = s* + (s0 - s*)(1-rho)^e.
    rows = core.simulate_pool(p)
    s_star = core.epoch_refill(p) / (p.T * p.N_b)
    s0 = core.sigma(p.R0, p)
    worst = max(abs(r["sigma"] - (s_star + (s0 - s_star) * (1 - p.rho) ** r["epoch"]))
                / max(s_star, 1e-12) for r in rows)
    check("trajectory tracks closed form", worst < 1e-9, f"worst rel err {worst:.1e}")

    # 2. The target rate is the difficulty controller's fixed point.
    d = 10 ** 30
    check("target is controller fixed point", core.next_reward_difficulty(d, p.T, p) == d)

    # 3. A block with no claims loosens by P/F, bounded.
    d2 = core.next_reward_difficulty(d, 0, p)
    check("zero-claims step is P/F", abs(d2 / d - p.P_ema / p.F_ema) < 1e-9)

    # 4. Pool never negative and settles at the fixed point.
    check("pool never negative", min(r["pool"] for r in rows) > 0)
    # The gap to R* closes at exactly (1-rho)^e; assert the simulated gap matches that,
    # which is the honest form of "settles at the fixed point" at any horizon.
    gap0 = p.R0 - core.r_star(p)
    gapE = rows[-1]["pool"] - core.r_star(p)
    expected = gap0 * (1 - p.rho) ** (len(rows) - 1)
    ok = abs(gapE - expected) <= abs(gap0) * 1e-9 + 1e-6
    check("converges to R* at rate (1-rho)^e", ok,
          f"remaining gap {gapE:.3e}, closed {1 - gapE / gap0:.1%} of {gap0:.3e}")

    # 5. Self-funding with headroom at the reference traffic.
    r = core.sigma_over_phi(p)
    check("sigma*/phi >= 2 at reference traffic", r >= 2.0, f"{r:.2f}")

    # 6. The specified endowment covers a 5-year adoption ramp.
    need = core.min_endowment_for_ramp(p, 5.0)
    check("R0 covers the 5-year ramp", p.R0 >= need,
          f"R0 {p.R0:.3e} vs needed {need:.3e}")

    # 7. Emission-vs-burn: the deflationary phase must be reachable through price
    #    discovery -- the required price sits between the resting level and MAX_PRICE.
    p_needed = (p.r_max * p.base_units_per_lgo) / (p.max_block_txs
                * (p.transfer_tx_bytes + p.transfer_tx_gas))
    check("deflationary phase reachable via price discovery",
          p.price_resting < p_needed < p.max_price,
          f"needs {p_needed:,.0f} lepta/gas vs MAX_PRICE {p.max_price:.2e}")

    # 8. Draining the pool inside one epoch must require exceeding the target rate by
    #    a large factor (1/rho), so the difficulty controller has room to react.
    check("within-epoch drain needs >= 50x the target rate",
          p.rho_den / p.rho_num >= 50,
          f"needs {p.T * p.rho_den / p.rho_num:,.0f} claims/block vs cap {p.max_block_txs}")

    # 9. Blend threshold arithmetic: exponent within the field.
    check("blend threshold inside the field", 0 < p.blend_base_exp < 254)
    check("reward genesis harder than blend base",
          p.reward_difficulty_exp > p.blend_base_exp)

    # 10. uint64 holds the supply in base units.
    check("supply fits TokenValue", p.S_tge * p.base_units_per_lgo < 2 ** 64 - 1)

    print(f"\n{len(failures)} failure(s)" if failures else "\nall pass")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="empowering.verify")
    ap.add_argument("--config", required=True)
    return run(ap.parse_args().config)


if __name__ == "__main__":
    sys.exit(main())
