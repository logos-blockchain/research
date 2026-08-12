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
    u = p.base_units_per_lgo
    print("=== The claim transaction, derived ===\n")
    print(f"  encoded signed tx     {p.claim_tx_bytes:>10} bytes, {p.claim_tx_gas} gas")
    print(f"  fee at the floor      {p.claim_fee(p.price_floor) * u:>10,.0f} lepta")
    print(f"  fee at rest           {p.phi * u:>10,.0f} lepta  = {p.phi:.3e} LGO"
          f"  ({p.phi / p.S_tge:.2e} of supply)")
    print(f"  ordinary transfer     {p.transfer_fee() * u:>10,.0f} lepta")
    print(f"  psi = avg/claim       {p.psi:>10.3f}")
    return dict(phi=p.phi, psi=p.psi)


def emission(p: Params) -> dict:
    """The supply against the fee schedule: how the deflationary phase is reached.

    With the lepton floor far below discovered prices, the phase is not reachable at
    the floor; what matters is the price at which a full block's burn matches the
    emission cap, and that it lies inside the representable price range.
    """
    print("=== Supply vs the fee schedule ===\n")
    r_max_lepta = p.r_max * p.base_units_per_lgo
    per_block_gas = p.max_block_txs * (p.transfer_tx_bytes + p.transfer_tx_gas)
    p_needed = r_max_lepta / per_block_gas
    print(f"  max minted per block   {r_max_lepta:>16,.0f} lepta  ({p.r_max:,.2f} LGO)")
    print(f"  full-block burn @rest  {per_block_gas * p.price_resting:>16,.0f} lepta")
    print(f"  deflation at price     {p_needed:>16,.0f} lepta/gas"
          f"  = {p_needed / p.price_resting:,.0f}x the resting level")
    ok = p.price_resting < p_needed < p.max_price
    print(f"  inside (resting, MAX_PRICE={p.max_price:.2e}): {'YES' if ok else 'NO'}")
    print("\n  The phase is reached through price discovery, not at the floor; the floor")
    print("  exists to keep zero from being absorbing, not to carry the emission model.")
    return dict(price_needed=p_needed, reachable=ok)


def rewards(p: Params) -> dict:
    """Steady state, headroom, builder edge, floors — the section 4.3/4.4 numbers."""
    print("=== Reward economics at the specified set ===\n")
    r = core.sigma_over_phi(p)
    print(f"  sigma*/phi at {p.n_tx_ref} tx/block   {r:>8.2f}")
    print(f"  builder edge                 {core.builder_edge(p):>8.3f}x")
    print(f"  R_min                        {core.r_min(p) / p.S_tge:>10.2e} of supply")
    print(f"  R*  (fixed point, at rest)   {core.r_star(p) / p.S_tge:>10.2e} of supply")
    print(f"  R0  (specified)              {p.genesis_pool_fraction:>10.2e} of supply")
    s0 = core.sigma(p.R0, p)
    print(f"  opening reward sigma_0       {s0 * p.base_units_per_lgo:>12,.0f} lepta"
          f" = {s0:.3f} LGO = {s0 / p.phi:,.0f}x the resting fee")
    print("\n  Endowment needed to hold sigma >= phi across an adoption ramp, at the")
    print("  RESTING price level (higher discovered prices scale these in proportion):")
    ramp = {}
    for years in (1, 2, 5, 10):
        R0 = core.min_endowment_for_ramp(p, float(years))
        ramp[years] = R0 / p.S_tge
        print(f"    {years:>2}-year ramp   {R0 / p.S_tge:>10.2e} of supply")
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
    print(f"  cliff: refill below        {p.T * p.N_b:,} lepta/epoch")
    print(f"  reward genesis p/2^{p.reward_difficulty_exp}: "
          f"{2 ** p.reward_difficulty_exp * p.sec_per_candidate_reward / 60:,.1f} core-min per solution"
          " (reward candidate keeps its key derivation)")
    cores = (p.T * 2 ** p.reward_difficulty_exp * p.sec_per_candidate_reward) / p.block_seconds
    print(f"  honest cores at target     {cores:,.0f}")

    # Report 4.6: the asymmetry of a mis-set genesis target. Arrivals modelled as
    # proportional to the target; excess claims priced at the opening reward.
    print("\n  Genesis target mis-set (report 4.6): excess claims before convergence")
    sigma0 = core.sigma(p.R0, p)
    d_eq = P_FIELD >> p.reward_difficulty_exp
    print(f"\n  {'genesis vs correct':>22} {'blocks to ±10%':>15} {'excess claims':>14}"
          f" {'cost (LGO)':>12} {'of pool':>10}")
    print("  " + "-" * 70)
    table = {}
    for mult, label in ((100, "100x too permissive"), (10, "10x too permissive"),
                        (0.1, "10x too hard"), (0.01, "100x too hard")):
        d = int(d_eq * mult)
        excess, conv = 0, None
        for n in range(400):
            c = min(max(0, round(p.T * d / d_eq)), p.max_block_txs)
            excess += max(0, c - p.T)
            if conv is None and abs(c - p.T) <= 0.1 * p.T:
                conv = n
            d = core.next_reward_difficulty(d, c, p)
        print(f"  {label:>22} {str(conv):>15} {excess:>14,} {excess * sigma0:>12,.0f}"
              f" {excess * sigma0 / p.R0:>10.2e}")
        table[label] = excess
    print(f"\n  Too permissive over-pays, bounded; too hard costs only time. The pool is")
    print(f"  {p.R0:,.0f} LGO, so even the worst row is a rounding error against it.")
    return dict(drain_claims_per_block=per_block, genesis_cores=cores,
                genesis_error=table)


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
        R0s = "never" if R0 == float("inf") else f"{R0 / p.S_tge:.2e}"
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
        print(f"  {1 / den:>6.1%} {rs:>11.2e} {rm:>8.2e} {den / p.epochs_per_year:>8.1f}"
              f" {drain:>12,.0f} {flag}{star}")
        out[den] = rs
    print("\n  Three pressures push rho up (reserve, floor, lag, all 1/rho); the drain")
    print("  margin pushes it down. The specified hundredth is where they meet.")
    return out


ALL = {"fee": fee, "emission": emission, "rewards": rewards,
       "blend": blend, "exhaustion": exhaustion, "security": security,
       "sweep-target": sweep_target, "sweep-share": sweep_share, "sweep-rho": sweep_rho}
