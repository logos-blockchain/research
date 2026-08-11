"""The report's result sections, one function per section, all config-driven.

Each function prints the tables backing the corresponding section of
reports/EmPoWering/tokenomics/ and returns the headline numbers so `verify` can
assert on them.
"""
from __future__ import annotations

from dataclasses import replace
from math import sqrt

from . import core
from .params import P_FIELD, Params


def fee(p: Params) -> dict:
    """The claim transaction's fee, built from the wire format and gas table."""
    print("=== The claim transaction, derived ===\n")
    print(f"  encoded signed tx     {p.claim_tx_bytes:>7} bytes, {p.claim_tx_gas} gas")
    print(f"  fee at the floor      {p.claim_fee(p.price_floor):>10,.0f} LGO")
    print(f"  fee at rest           {p.phi:>10,.0f} LGO"
          f"   ({p.phi / p.S_tge:.2e} of supply)")
    print(f"  ordinary transfer     {p.transfer_fee():>10,.0f} LGO")
    print(f"  psi = avg/claim       {p.psi:>10.3f}")
    return dict(phi=p.phi, psi=p.psi)


def emission(p: Params) -> dict:
    """The supply against the fee schedule: where the deflationary phase begins."""
    print("=== Supply vs the fee schedule ===\n")
    burn_at_target = p.blend_target_txs * p.transfer_fee()
    print(f"  max minted per block  {p.r_max:>14,.1f} LGO")
    print(f"  burn at target load   {burn_at_target:>14,.1f} LGO"
          f"   ({p.blend_target_txs} tx at rest)")
    transition = p.r_max / p.transfer_fee()
    print(f"  deflation begins at   {transition:>14,.0f} tx/block"
          f"   (target {p.blend_target_txs}, cap {p.max_block_txs})")
    ok = 0 < transition <= p.max_block_txs
    print(f"  all three phases reachable: {'YES' if ok else 'NO'}")
    return dict(transition_tx=transition, reachable=ok)


def rewards(p: Params) -> dict:
    """Steady state, headroom, builder edge, floors — the section 4.3/4.4 numbers."""
    print("=== Reward economics at the specified set ===\n")
    r = core.sigma_over_phi(p)
    print(f"  sigma*/phi at {p.n_tx_ref} tx/block   {r:>8.2f}")
    print(f"  builder edge                 {core.builder_edge(p):>8.3f}x")
    print(f"  R_min                        {core.r_min(p) / p.S_tge:>8.3%} of supply")
    print(f"  R*  (fixed point)            {core.r_star(p) / p.S_tge:>8.3%} of supply")
    print(f"  R0  (specified)              {p.genesis_pool_fraction:>8.3%} of supply")
    s0 = core.sigma(p.R0, p)
    print(f"  opening reward sigma_0       {s0:>8,.0f} LGO = {s0 / p.phi:.1f}x the fee")
    print("\n  Endowment needed to hold sigma >= phi across an adoption ramp:")
    ramp = {}
    for years in (1, 2, 5, 10):
        R0 = core.min_endowment_for_ramp(p, float(years))
        ramp[years] = R0 / p.S_tge
        print(f"    {years:>2}-year ramp   {R0 / p.S_tge:>8.3%} of supply")
    return dict(sigma_over_phi=r, edge=core.builder_edge(p),
                sigma0_over_phi=s0 / p.phi, ramp=ramp)


def blend(p: Params) -> dict:
    """The admission threshold: message cost on the bench machine and the target one."""
    print("=== Blend admission threshold ===\n")
    d = P_FIELD >> p.blend_base_exp
    attempts = P_FIELD / d
    s_m4 = attempts * p.sec_per_candidate
    print(f"  threshold p/2^{p.blend_base_exp}: {attempts:,.0f} expected candidates")
    print(f"  one M4 Pro core     {s_m4:>8.1f} s/solution   {86400 / s_m4:>8,.0f} msgs/day")
    for r, label in ((p.pi5_slowdown_low, "Pi 5 @ low"),
                     (p.pi5_slowdown, "Pi 5 @ mid"),
                     (p.pi5_slowdown_high, "Pi 5 @ high")):
        s = s_m4 * r
        print(f"  {label:<18}  {s / 60:>8.1f} min       {86400 / s:>8,.0f} msgs/day"
              f"   ({86400 * p.pi5_cores / s:,.0f} on all {p.pi5_cores} cores)")
    print("\n  The Pi 5 rows are ESTIMATED from the M4 Pro measurement; re-derive the")
    print("  threshold once bench-poseidon2 has been run on the target hardware.")
    return dict(m4_seconds=s_m4, pi5_mid_seconds=s_m4 * p.pi5_slowdown)


def exhaustion(p: Params) -> dict:
    """Section 3.8: what stops claiming, and the margins."""
    print("=== Stopping conditions ===\n")
    per_block = p.T * p.rho_den / p.rho_num
    print(f"  within-epoch drain needs   {per_block:,.0f} claims/block"
          f"   (cap {p.max_block_txs})")
    print(f"  cliff: refill below        {p.T * p.N_b:,} base units/epoch")
    print(f"  reward genesis p/2^{p.reward_difficulty_exp}: "
          f"{2 ** p.reward_difficulty_exp * p.sec_per_candidate / 60:,.1f} core-min per solution")
    cores = (p.T * 2 ** p.reward_difficulty_exp * p.sec_per_candidate) / p.block_seconds
    print(f"  honest cores at target     {cores:,.0f}")
    return dict(drain_claims_per_block=per_block, genesis_cores=cores)


def security(p: Params) -> dict:
    """Section 4.1: adversarial stake accumulation, mined coins aging one epoch."""
    print("=== Bootstrap security ===\n")
    rows = core.simulate_pool(p)
    distributed = sum(p.T * p.N_b * r["sigma"] for r in rows if r["enabled"])
    yrs = rows[-1]["years"]
    print(f"  distributed over {yrs:.1f} years: {distributed / p.S_tge:.2%} of supply")
    print(f"  (perpetual refill: this grows with the horizon, it is not a lifetime figure)\n")
    print(f"  {'h':>6} {'honest stakes':>14}" +
          "".join(f"{'D0=' + f'{d:.1%}':>12}" for d in (0.005, 0.05, 0.30)))
    print("  " + "-" * 60)
    out = {}
    for h in (0.10, p.adversary_h, 0.50):
        for sf in (1.0, 0.5):
            row = f"  {h:>6.2f} {sf:>13.0%}"
            for D0f in (0.005, 0.05, 0.30):
                adv = pend_a = honest = pend_h = 0.0
                peak = 0.0
                for r in rows:
                    adv += pend_a
                    honest += pend_h
                    d = p.T * p.N_b * r["sigma"] if r["enabled"] else 0.0
                    pend_a, pend_h = d * h, d * (1 - h) * sf
                    tot = D0f * p.S_tge + adv + honest
                    peak = max(peak, adv / tot if tot else 0.0)
                row += f"{peak:>11.1%}" + ("!" if peak >= 1 / 3 else " ")
                out[(h, sf, D0f)] = peak
            print(row)
    print("\n  ! exceeds one third. The asymptote h/(h+(1-h)s) does not depend on the")
    print("  share or the supply; the horizon figures above do (see report, section 4.1).")
    return dict(peak=out[(p.adversary_h, 1.0, 0.30)])


def sweep_target(p: Params) -> dict:
    """Report 4.4.1: the claim target is overhead, not throughput."""
    print("=== Sweep: TARGET_CLAIMS_PER_BLOCK (report 4.4.1) ===\n")
    print(f"  at beta = {p.beta:.0%}, {p.n_tx_ref} tx/block. The epoch's distribution is")
    print("  fixed by the refill; T divides it and each claim pays a fee out of its share.\n")
    print(f"  {'T':>5} {'sigma*/phi':>11} {'fee eaten':>10} {'to miners':>10}"
          f" {'edge':>8} {'noise':>7} {'R0 5y ramp':>12}")
    print("  " + "-" * 68)
    out = {}
    for T in (1, 5, 10, 25, 50, 100):
        q = replace(p, T=T)
        r = core.sigma_over_phi(q)
        R0 = core.min_endowment_for_ramp(q, 5.0)
        R0s = "never" if R0 == float("inf") else f"{R0 / p.S_tge:.3%}"
        e = core.builder_edge(q)
        es = "n/a" if e == float("inf") else f"{e:.2f}x"
        star = " <-" if T == p.T else ""
        print(f"  {T:>5} {r:>11.2f} {min(1, 1 / r):>9.0%} {max(0, 1 - 1 / r):>10.0%}"
              f" {es:>8} {1 / sqrt(T):>6.0%} {R0s:>12}{star}")
        out[T] = r
    print("\n  T enters the delivered amount with a minus sign; lower is better until")
    print("  variance (1/sqrt(T)) dominates. The specified value is arrowed.")
    return out


def sweep_share(p: Params) -> dict:
    """Report 4.4.2: the share against self-funding below and subordination above."""
    print("=== Sweep: POW_SHARE (report 4.4.2) ===\n")
    print(f"  at T = {p.T}, {p.n_tx_ref} tx/block. Bounded below by headroom over the")
    print("  fee, above by mining staying subordinate to the leader path (A_t = 0).\n")
    print(f"  {'beta':>7} {'sigma*/phi':>11} {'edge':>8} {'reaches claimants':>18}"
          f" {'PoW/leader':>12}")
    print("  " + "-" * 62)
    out = {}
    for num in (2, 5, 10, 20, 33):
        q = replace(p, beta_num=num)
        r = core.sigma_over_phi(q)
        e = core.builder_edge(q)
        es = "n/a" if e == float("inf") else f"{e:.3f}x"
        beta = num / p.beta_den
        pow_vs_leader = beta / (0.4 * (1 - beta))
        star = " <-" if num == p.beta_num else ""
        print(f"  {beta:>6.0%} {r:>11.2f} {es:>8} {max(0, 1 - 1 / r):>17.0%}"
              f" {pow_vs_leader:>11.0%}{star}")
        out[num] = r
    print("\n  Subordination read as PoW <= a third of the leader share caps beta near")
    print("  12%; the specified tenth sits under it with 5x fee headroom.")
    return out


def sweep_rho(p: Params) -> dict:
    """Report 4.4.3: rho sets the standing reserve, never the reward."""
    print("=== Sweep: EPOCH_POW_DISTRIBUTION_RATE (report 4.4.3) ===\n")
    print(f"  {'rho':>7} {'reserve R*':>12} {'R_min':>9} {'lag (yr)':>9}"
          f" {'drain claims/blk':>17}")
    print("  " + "-" * 60)
    out = {}
    for den in (500, 200, 100, 50, 20):
        q = replace(p, rho_den=den)
        rs = core.r_star(q) / p.S_tge
        rm = core.r_min(q) / p.S_tge
        drain = p.T * den / p.rho_num
        flag = "unreachable" if drain > p.max_block_txs else "reachable"
        star = " <-" if den == p.rho_den else ""
        print(f"  {1 / den:>6.1%} {rs:>11.2%} {rm:>8.3%} {den / p.epochs_per_year:>8.1f}"
              f" {drain:>12,.0f} {flag}{star}")
        out[den] = rs
    print("\n  Three pressures push rho up (reserve, floor, lag, all 1/rho); the drain")
    print("  margin pushes it down. The specified hundredth is where they meet.")
    return out


ALL = {"fee": fee, "emission": emission, "rewards": rewards,
       "blend": blend, "exhaustion": exhaustion, "security": security,
       "sweep-target": sweep_target, "sweep-share": sweep_share, "sweep-rho": sweep_rho}
