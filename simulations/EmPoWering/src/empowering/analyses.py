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
    """The admission threshold, on the measured target hardware (one-core basis)."""
    print("=== Blend admission threshold (measured on the target) ===\n")
    d = P_FIELD >> p.blend_base_exp
    attempts = P_FIELD / d
    s1 = attempts * p.sec_per_candidate
    print(f"  threshold p/2^{p.blend_base_exp}: {attempts:,.0f} expected candidates")
    print(f"  one target core     {s1:>8.1f} s/solution   {86400 / s1:>8,.0f} msgs/day")
    print(f"  whole board ({p.pi5_cores})     {s1 / p.pi5_cores:>8.1f} s/solution"
          f"   {86400 * p.pi5_cores / s1:>8,.0f} msgs/day")
    print(f"  optimising miner    {attempts * p.sec_per_candidate_opt:>8.1f} s"
          f"   (algorithmic edge {p.sec_per_candidate / p.sec_per_candidate_opt:.2f}x)")
    print("\n  Basis: one core of a Raspberry Pi 5, measured; a desktop core is ~6x faster")
    print("  and deliberately not the calibration basis.")
    return dict(target_seconds=s1)


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
                # one definition, shared with the section 6 sweeps and the panel's golden
                # grid (core.peak_adversary_share), so the three cannot drift apart
                peak = core.peak_adversary_share(p, h, sf, D0f, rows)
                row += f"{peak:>11.1%}" + ("!" if peak >= 1 / 3 else " ")
                out[(h, sf, D0f)] = peak
            print(row)
    print("\n  ! exceeds one third. The asymptote h/(h+(1-h)s) does not depend on the")
    print("  share or the supply; the horizon figures above do (see report, section 4.1).")
    return dict(peak=out[(p.adversary_h, 1.0, 0.30)])


def volume(p: Params) -> dict:
    """What share of a block's transactions are claims, and what beta ties it to.

    Assumption A10 reads the claim load against block *capacity* -- T/MAX_BLOCK_TXS, about
    one percent, "comfortable with room to spare". That is the right check for whether claims
    fit. It is not the check for whether they pay, because the reward per claim is set by the
    fees the *actual* traffic collects, not by the capacity it could have collected.

    Against actual traffic the two quantities are one identity. With v = T/n_tx the claim
    share of transactions and sigma*/phi = psi*beta*n_tx/T the steady-state reward over the
    fee,

        v * (sigma*/phi) = psi * beta

    so at the point where a claim exactly pays its own fee the claim share is psi*beta, and
    that is the *ceiling* on how much of a block's traffic claims may be while mining still
    funds itself from fees. It depends on beta and on nothing else -- not on T, which cancels,
    and not on the traffic level.
    """
    print("=== PoW claim share of transaction volume (A10, against traffic) ===\n")
    v_cap = p.T / p.max_block_txs
    v_ref = p.T / p.n_tx_ref
    v_be = p.psi * p.beta
    n_min = p.T / v_be
    print(f"  A10, against capacity      T/MAX_BLOCK_TXS = {v_cap:.2%}")
    print(f"  against reference traffic  T/n_tx          = {v_ref:.2%}  (n_tx = {p.n_tx_ref})")
    print(f"  identity                   v * sigma*/phi  = psi*beta = {v_be:.4%}")
    print(f"  break-even claim share     psi*beta        = {v_be:.2%}")
    print(f"  break-even traffic         T/(psi*beta)    = {n_min:,.0f} tx/block")
    print(f"  margin at reference        {p.n_tx_ref / n_min:.2f}x the break-even traffic\n")
    print(f"  {'beta':>7} {'break-even n_tx':>16} {'ceiling on v':>13}"
          f" {'sigma*/phi @' + str(p.n_tx_ref):>15} {'v @' + str(p.n_tx_ref):>10}")
    print("  " + "-" * 66)
    out = {}
    for num in (2, 5, 10, 20, 33):
        q = replace(p, beta_num=num)
        vb = q.psi * q.beta
        r = core.sigma_over_phi(q)
        star = " <-" if num == p.beta_num else ""
        print(f"  {q.beta:>6.0%} {q.T / vb:>16,.0f} {vb:>12.2%} {r:>15.2f}"
              f" {v_ref:>10.2%}{star}")
        out[num] = dict(break_even_n=q.T / vb, ceiling=vb, sigma_over_phi=r)
    print("\n  Raising beta does not change how many claims a block carries -- the difficulty")
    print("  controller holds that at T regardless. What it moves is the traffic floor: below")
    print("  T/(psi*beta) transactions per block a claim earns less than it pays, and the")
    print("  shortfall comes out of the endowment rather than out of fees.")

    # The refill treats every transaction as an ordinary transfer, but T of them are claims,
    # which pay more. Small, one-signed, and worth stating rather than leaving implicit.
    understated = p.T * (1 / p.psi - 1) / p.n_tx_ref
    print(f"\n  Refill approximation: the model prices all {p.n_tx_ref} transactions as transfers,")
    print(f"  but {p.T} of them are claims paying 1/psi = {1 / p.psi:.3f}x more. The refill is")
    print(f"  understated by {understated:.2%} -- one-signed, and conservative.")
    return dict(v_cap=v_cap, v_ref=v_ref, v_break_even=v_be, n_min=n_min,
                refill_understated=understated, by_beta=out)


def fees(p: Params) -> dict:
    """The working fee range, on the model's one real axis.

    Traffic count and price level are not separately identified: what the refill takes is a
    share of a block's fee *revenue*, and what decides whether mining pays is that revenue
    against the claim's own fee, which moves with the price too. The two scalings cancel, so
    the whole (n_tx, price) plane collapses to

        Phi_hat = Phi_b / phi   (a block's revenue counted in claim fees)

    with `sigma*/phi = beta * Phi_hat / T`. Every verdict below is therefore price-free.
    """
    print("=== Working fee range (revenue per block, in claim fees) ===\n")
    u, be = p.base_units_per_lgo, core.min_fee_load(p)
    print(f"  the axis    Phi_hat = Phi_b/phi = psi*n_tx     sigma*/phi = beta*Phi_hat/T")
    print(f"  break-even  Phi_hat = T/beta                 = {be:,.0f} claim fees per block")
    print(f"  at the resting price that is {be * p.phi * u:,.0f} lepta/block, but the")
    print("  threshold itself does not depend on the price level -- both sides scale.\n")
    print(f"  {'Phi_hat':>10} {'sigma*/phi':>11} {'verdict':<22}"
          f" {'lepta/blk @rest':>16} {'~n_tx @any price':>17}")
    print("  " + "-" * 82)
    out = {}
    rows = [(25, ""), (50, ""), (100, "break-even"), (200, "2x margin"),
            (round(core.fee_load(p)), "SPECIFIED"), (857, "full block"), (2000, "")]
    for load, tag in sorted(set(rows), key=lambda r: r[0]):
        r = core.sigma_over_phi_from_load(p, load)
        verdict = ("under water" if r < 1 else "thin" if r < 2
                   else "works" if r < 10 else "ample")
        if tag:
            verdict = f"{verdict} <- {tag}"
        print(f"  {load:>10,} {r:>11.2f} {verdict:<22}"
              f" {load * p.phi * u:>16,.0f} {load / p.psi:>17,.0f}")
        out[load] = r
    print(f"\n  The specified set collects {core.fee_load(p):,.1f} claim fees per block against a")
    print(f"  break-even of {be:,.0f} -- a {core.sigma_over_phi(p):.2f}x margin. Read as a traffic count that is")
    print(f"  {p.n_tx_ref} ordinary transfers; read as a price level it is anything at all, which is")
    print("  the point: the margin is set by how much revenue a block collects relative to")
    print("  what a claim costs, and both move together when the market reprices.")
    print(f"\n  This axis is also exact where the count form is not: pricing all {p.n_tx_ref}")
    print(f"  transactions as transfers understates the refill by {p.T * (1 / p.psi - 1) / p.n_tx_ref:.2%},")
    print("  because T of them are claims paying more. Revenue per block makes no assumption")
    print("  about composition, so that correction disappears.")
    # --- what mixes produce a given load. Illustrative, not exhaustive. ---
    shapes = [("ordinary transfer", p.transfer_tx_bytes, p.transfer_tx_gas, "KNOWN"),
              ("PoW claim (+transfer)", p.claim_tx_bytes, p.claim_tx_gas, "KNOWN"),
              ("SDP declare", p.sdp_declare_bytes, p.sdp_declare_gas, "gas KNOWN"),
              ("channel inscribe", p.inscribe_bytes, p.inscribe_gas, "gas KNOWN")]
    print("\n  --- which transaction mixes produce a load ---\n")
    print(f"  {'shape':<24} {'bytes':>7} {'gas':>6} {'claim fees each':>16}"
          f" {'to break even':>14} {'fills a block to':>17}")
    print("  " + "-" * 90)
    for name, nb, g, tag in shapes:
        each = p.shape_load(nb, g)
        print(f"  {name:<24} {nb:>7} {g:>6} {each:>16.4f} {be / each:>14,.0f}"
              f" {each * p.max_block_txs:>17,.0f}")
    print(f"\n  (byte counts for the last two are ASSUMED and illustrative; their gas is the"
          f"\n   specification's. The first two are the shapes the model already carries.)\n")
    mixes = [("600 transfers - the reference", [(p.n_tx_ref, p.transfer_tx_bytes, p.transfer_tx_gas)]),
             (f"{p.T} claims + {p.n_tx_ref - p.T} transfers - the realistic block",
              [(p.T, p.claim_tx_bytes, p.claim_tx_gas),
               (p.n_tx_ref - p.T, p.transfer_tx_bytes, p.transfer_tx_gas)]),
             ("a full block of transfers", [(p.max_block_txs, p.transfer_tx_bytes, p.transfer_tx_gas)]),
             ("a full block of the cheapest shape",
              [(p.max_block_txs, p.inscribe_bytes, p.inscribe_gas)]),
             ("half a block, half inscribes",
              [(256, p.transfer_tx_bytes, p.transfer_tx_gas), (256, p.inscribe_bytes, p.inscribe_gas)])]
    print(f"  {'mix':<44} {'load':>8} {'sigma*/phi':>11} {'verdict':<12}")
    print("  " + "-" * 80)
    for name, parts in mixes:
        load = sum(k * p.shape_load(nb, g) for k, nb, g in parts)
        r = core.sigma_over_phi_from_load(p, load)
        print(f"  {name:<44} {load:>8,.0f} {r:>11.2f}"
              f" {'under water' if r < 1 else 'thin' if r < 2 else 'works':<12}")
        out[name] = load
    floor_bytes = be / p.max_block_txs * (p.claim_tx_bytes + p.claim_tx_gas) - p.inscribe_gas
    print(f"\n  A full block clears break-even on almost any mix: with {p.max_block_txs} slots it needs")
    print(f"  only {be / p.max_block_txs:.3f} claim fees per transaction, which at the cheapest Operation's")
    print(f"  {p.inscribe_gas} gas means about {floor_bytes:.0f} encoded bytes each. A signed transaction cannot be")
    print("  that small -- the claim's signature alone is 128 B -- so what decides the margin is")
    print("  how FULL blocks are, not what is in them.")
    return dict(break_even_load=be, specified_load=core.fee_load(p),
                margin=core.sigma_over_phi(p), by_load=out,
                min_bytes_for_break_even=floor_bytes)


def ratio(p: Params) -> dict:
    """T and beta are not separately identified by the economics -- only T/beta is.

    Every quantity that decides whether mining pays contains the two only as a ratio, so the
    parameter set has a one-dimensional degeneracy the sweeps in 4.4.1/4.4.2 and 4.10 do not
    show, because each holds the other fixed. What breaks the tie is the constraints that
    bind T and beta *separately*, and they pull in opposite directions along the ray.
    """
    from dataclasses import replace
    print("=== T and beta: the ratio is what the economics sees ===\n")
    print("  sigma*/phi = psi*beta*n_tx/T = Phi_hat/(T/beta). Along T/beta = const nothing")
    print("  the economics cares about changes at all:\n")
    print(f"  {'T':>5} {'beta':>7} {'T/beta':>8} {'sigma*/phi':>11} {'edge':>9}"
          f" {'break-even load':>16}")
    print("  " + "-" * 62)
    def on_ray(T: int):
        """The (T, beta) on the current ray T/beta, as a config."""
        return replace(p, T=T, beta_num=int(round(p.beta_den * T * p.beta / p.T)))

    for T in (5, 10, 11, 20, 50):
        q = on_ray(T)
        print(f"  {T:>5} {q.beta:>7.0%} {T / q.beta:>8.0f} {core.sigma_over_phi(q):>11.4f}"
              f" {core.builder_edge(q):>8.4f}x {core.min_fee_load(q):>16,.0f}")

    lo, hi = core.iso_margin_window(p)
    cap = core.subordination_beta_cap(p)
    print("\n  What breaks the degeneracy -- constraints on T and beta one at a time:\n")
    print(f"  {'T':>5} {'beta':>7} {'drain T/rho':>12} {'vs cap':>14} {'subordination':>14}"
          f" {'noise':>7} {'overshoot':>10}")
    print("  " + "-" * 76)
    for T in (10, 11, 12, 20, 50):
        q = on_ray(T)
        d = T * q.rho_den / q.rho_num
        sub = q.beta / (q.leader_fee_share * (1 - q.beta))
        over = (q.P_ema - q.F_ema) / (2 * q.P_ema * T)
        flag = "reachable" if d <= q.max_block_txs else "out of reach"
        print(f"  {T:>5} {q.beta:>7.0%} {d:>12,.0f} {flag:>14} {sub:>13.1%}"
              f"{'!' if sub > 1 / 3 else ' '} {1 / T ** 0.5:>6.1%} {over:>10.2%}")

    print(f"\n  Raising T along the ray puts the drain out of reach at T > {lo:.2f};")
    print(f"  subordination caps beta at {cap:.2%}, which on this ray is T <= {hi:.2f}.")
    ints = [t for t in range(int(lo) + 1, int(hi) + 1)]
    print(f"  The window is therefore T in ({lo:.2f}, {hi:.2f}] -- integer choices: {ints}.")
    if ints:
        t = ints[0]
        q = on_ray(t)
        print(f"\n  At T = {t}, beta = {q.beta:.0%} the economics is identical -- sigma*/phi"
              f" {core.sigma_over_phi(q):.4f},")
        print(f"  builder edge {core.builder_edge(q):.4f}x, break-even load"
              f" {core.min_fee_load(q):,.0f} -- while the drain needs")
        print(f"  {t * q.rho_den // q.rho_num:,} claims per block against a cap of"
              f" {q.max_block_txs}, so it is impossible by")
        print("  construction rather than prevented by the controller. The price is a"
              f" {q.beta / p.beta - 1:.0%} larger")
        print(f"  reserve ({core.r_star(p):,.0f} -> {core.r_star(q):,.0f} LGO) and floor"
              f" ({core.r_min(p):,.0f} -> {core.r_min(q):,.0f} LGO), both negligible")
        print("  in absolute terms, and arrival noise and the retarget overshoot both improve.")
    return dict(window=(lo, hi), integers=ints, beta_cap=cap,
                drain_safe_T=core.drain_safe_T(p))


def sweeps_full(p: Params) -> dict:
    """Section 6's sweep programme: every axis, every per-cell metric it asks for."""
    from .sweeps import report as _report
    return _report(p)


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
        pow_vs_leader = beta / (p.leader_fee_share * (1 - beta))
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


def sampled(p: Params) -> dict:
    """Section 4.8: A2's Poisson arrivals, run rather than replaced by their mean."""
    from .sampled import report as _report
    return _report(p)


ALL = {"fee": fee, "emission": emission, "rewards": rewards,
       "blend": blend, "exhaustion": exhaustion, "security": security, "volume": volume, "sampled": sampled, "fees": fees,
       "ratio": ratio, "sweeps-full": sweeps_full, "sweep-target": sweep_target, "sweep-share": sweep_share, "sweep-rho": sweep_rho}
