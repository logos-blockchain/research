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

    # 13. The claim-volume identity: v * (sigma*/phi) = psi*beta, with v = T/n_tx the claim
    # share of a block's transactions. Checked across traffic AND beta, since it is the
    # relation A10 needs and the one the report's section 4.8 quotes.
    worst_id = 0.0
    from dataclasses import replace as _replace
    for num in (2, 5, 10, 20, 33):
        q = _replace(p, beta_num=num)
        for n in (50, 119, 300, 600, 1024):
            v = q.T / n
            worst_id = max(worst_id, abs(v * core.sigma_over_phi(q, n) - q.psi * q.beta))
    check("claim share identity v*(sigma*/phi) = psi*beta", worst_id < 1e-12,
          f"worst abs err {worst_id:.1e}")

    # 14. Break-even traffic is exactly where the reward equals the fee, so the ceiling on
    # the claim share of traffic is psi*beta and nothing else.
    n_be = p.T / (p.psi * p.beta)
    check("break-even traffic is where sigma* = phi",
          abs(core.sigma_over_phi(p, n_be) - 1.0) < 1e-12,
          f"{n_be:,.0f} tx/block, claim share {p.T / n_be:.2%} = psi*beta")

    # 15. The specified point sits below that ceiling -- mining funds itself from fees at
    # the reference traffic rather than out of the endowment.
    check("claims pay for themselves at reference traffic",
          p.T / p.n_tx_ref < p.psi * p.beta,
          f"share {p.T / p.n_tx_ref:.2%} vs ceiling {p.psi * p.beta:.2%}")

    # 16. The refill prices every transaction as a transfer, but T of them are claims paying
    # more, so the model understates the refill. Assert the error is one-signed and small.
    under = p.T * (1 / p.psi - 1) / p.n_tx_ref
    check("refill approximation is conservative and under 1%", 0 < under < 0.01,
          f"understated by {under:.2%}")

    # 17-20. Sampled arrivals (section 4.8): the assumption A2 replaces with its mean.
    from . import sampled as _s
    a = _s.summary(p, seeds=2, epochs=2)

    check("sampled per-block spread matches the AR(1) closed form",
          abs(a["rel_sd"] - _s.predicted_relative_sd(p)) < 0.01,
          f"measured {a['rel_sd']:.1%} vs predicted {_s.predicted_relative_sd(p):.1%}")

    # The retarget overshoots T by (P-F)/(2P) under Poisson arrivals -- Jensen on a convex
    # map, one-signed, and invisible to the mean-field model.
    check("retarget overshoots T by (P-F)/(2P)",
          abs((a["mean_per_block"] - p.T) - _s.predicted_rate_bias(p)) < 0.02,
          f"measured +{a['mean_per_block'] - p.T:.4f} vs predicted +{_s.predicted_rate_bias(p):.4f}")

    # The epoch total is far tighter than an uncorrelated Poisson sum, because the
    # controller corrects rather than accumulates. This is what justifies section 3.1.
    naive = 1 / (p.T * p.N_b) ** 0.5
    check("epoch total is much tighter than uncorrelated Poisson",
          a["epoch_rel_sd"] < naive / 10,
          f"{a['epoch_rel_sd']:.4%} vs naive {naive:.4%}")

    # Poisson bursts come nowhere near the within-epoch drain: it is a controller
    # guarantee, not a probabilistic one.
    check("Poisson arrivals never approach the drain requirement",
          a["peak_sd_from_drain"] > 50 and a["guard_blocks"] == 0,
          f"busiest block {a['peak_block']}, drain needs {p.T * p.rho_den // p.rho_num},"
          f" {a['peak_sd_from_drain']:,.0f} sd away")

    # 21-23. The fee-load formulation (section 4.9): one axis in place of (n_tx, price).
    worst_eq = max(abs(core.sigma_over_phi(p, n)
                       - core.sigma_over_phi_from_load(p, core.fee_load(p, n)))
                   for n in (25, 50, 119, 300, 600, 1024))
    check("fee load reproduces the count form exactly", worst_eq < 1e-12,
          f"worst abs err {worst_eq:.1e}")

    # The verdict must not move with the price level: both the refill and the claim's own
    # fee scale with it, so sigma*/phi is invariant. This is what makes the axis the right one.
    from dataclasses import replace as _rep
    ratios = [core.sigma_over_phi(_rep(p, price_resting=p.price_resting * m), p.n_tx_ref)
              for m in (1, 10, 1_000, 100_000)]
    check("fee-load verdict is price-invariant",
          max(ratios) - min(ratios) < 1e-9,
          f"sigma*/phi = {ratios[0]:.4f} across 5 decades of price")

    # Break-even is T/beta claim fees per block -- no traffic estimate, no price level.
    check("break-even load is T/beta",
          abs(core.min_fee_load(p) - p.T / p.beta) < 1e-12
          and abs(core.sigma_over_phi_from_load(p, core.min_fee_load(p)) - 1.0) < 1e-12,
          f"{core.min_fee_load(p):,.0f} claim fees per block")

    # 24. Composition barely matters: a full block clears break-even on any realistic shape,
    # because the per-transaction requirement is smaller than a signed transaction can be.
    need_each = core.min_fee_load(p) / p.max_block_txs
    bytes_each = need_each * (p.claim_tx_bytes + p.claim_tx_gas) - p.inscribe_gas
    check("a full block breaks even on any realistic shape", bytes_each < 128,
          f"needs {need_each:.3f} claim fees each = ~{bytes_each:.0f} bytes,"
          " under a signature alone (128 B)")

    # 25-26. T and beta enter the economics only as T/beta, and the window that keeps the
    # margin while closing the drain is bounded by subordination above and the cap below.
    from dataclasses import replace as _r
    ray = [core.sigma_over_phi(_r(p, T=t, beta_num=int(round(p.beta_den * t * p.beta / p.T))))
           for t in (5, 10, 11, 20, 50)]
    check("T and beta enter only as T/beta", max(ray) - min(ray) < 1e-12,
          f"sigma*/phi = {ray[0]:.4f} at every point on the ray")

    lo, hi = core.iso_margin_window(p)
    ints = [t for t in range(int(lo) + 1, int(hi) + 1)]
    ok = lo < hi and bool(ints)
    if ok:
        q = _r(p, T=ints[0], beta_num=int(round(p.beta_den * ints[0] * p.beta / p.T)))
        ok = (abs(core.sigma_over_phi(q) - core.sigma_over_phi(p)) < 1e-12
              and q.T * q.rho_den / q.rho_num > q.max_block_txs
              and q.beta <= core.subordination_beta_cap() + 1e-12)
    check("a window exists that holds the margin and closes the drain", bool(ok),
          f"T in ({lo:.2f}, {hi:.2f}], integers {ints}")

    print(f"\n{len(failures)} failure(s)" if failures else "\nall pass")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="empowering.verify")
    ap.add_argument("--config", required=True)
    return run(ap.parse_args().config)


if __name__ == "__main__":
    sys.exit(main())
