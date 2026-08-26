"""Section 6's sweep programme, run.

Section 6 lists the axes worth sweeping and, more usefully, what to report in every cell:
the steady-state margin, whether the endowment covers an adoption ramp, the peak attacker
share and its asymptote, the builder's edge, how fast the difficulty controller recovers
from a tenfold hashrate step, and how much fee revenue is diverted from the burn. Until now
that was a plan rather than an output.

Each axis is swept by replacing one field of the config and re-deriving, so a cell is the
whole model at that setting rather than a formula copied out of it.
"""
from __future__ import annotations

from dataclasses import replace

from . import core
from .params import Params

# The claim target the specification sets, plus the larger values the proposal and earlier
# revisions carried. 500 is well past anything considered; it is here to show the wall.
T_VALUES = (10, 50, 100, 500)
BETA_NUM = (5, 10, 20, 33, 50)
RHO_DEN = (200, 100, 50)
R0_FRAC = (0.005, 0.01, 0.02, 0.05, 0.10)
RAMP_YEARS = (1, 2, 5, 10)
D0_FRAC = (0.005, 0.05, 0.30)


def cell(p: Params, ramp_years: float = 5.0, h: float = None,
         honest_stake: float = 1.0, d0: float = 0.30) -> dict:
    """Every quantity section 6 asks for, at one parameter setting."""
    h = p.adversary_h if h is None else h
    need = core.min_endowment_for_ramp(p, ramp_years)
    covered = p.R0 >= need
    return {
        "sigma_over_phi": core.sigma_over_phi(p),
        "ramp_need_frac": need / p.S_tge,
        "ramp_covered": covered,
        "ramp_margin": (p.R0 / need) if need > 0 and need != float("inf") else float("inf"),
        "peak_adversary": core.peak_adversary_share(p, h, honest_stake, d0),
        "asymptote": core.adversary_asymptote(h, honest_stake),
        "builder_edge": core.builder_edge(p),
        "reconverge_blocks": core.reconvergence_blocks(p),
        "burn_diverted": p.beta,
        "break_even_load": core.min_fee_load(p),
        "claim_share": p.T / p.n_tx_ref,
        "claim_share_ceiling": p.psi * p.beta,
        "drain_per_block": p.T * p.rho_den / p.rho_num,
        "drain_reachable": p.T * p.rho_den / p.rho_num <= p.max_block_txs,
    }


def _fmt(c: dict, p: Params) -> str:
    edge = "n/a" if c["builder_edge"] == float("inf") else f"{c['builder_edge']:.3f}x"
    ramp = ("never" if c["ramp_need_frac"] == float("inf")
            else f"{c['ramp_margin']:>9,.0f}x" if c["ramp_covered"] else "NOT COVERED")
    rec = "-" if c["reconverge_blocks"] is None else f"{c['reconverge_blocks']:,}"
    return (f"{c['sigma_over_phi']:>10.2f} {ramp:>12} {c['peak_adversary']:>9.2%}"
            f" {edge:>9} {rec:>7} {c['burn_diverted']:>8.0%}"
            f" {c['drain_per_block']:>9,.0f}{'!' if c['drain_reachable'] else ' '}")


_HEAD = (f"  {'axis':<14} {'sigma*/phi':>10} {'ramp cover':>12} {'peak adv':>9}"
         f" {'edge':>9} {'recon':>7} {'burn':>8} {'drain/blk':>10}")


def sweep_T(p: Params) -> dict:
    """The claim target. Specified at 10; swept to 500 to show where the wall is."""
    print("=== Sweep: TARGET_CLAIMS_PER_BLOCK (section 6) ===\n")
    print("  T divides the epoch's distribution, so the reward per claim falls as 1/T while")
    print("  the claim's own fee does not. It also sets the drain margin (T/rho against the")
    print("  block cap), the arrival noise (1/sqrt(T)) and the retarget's overshoot.\n")
    print(_HEAD)
    print("  " + "-" * 92)
    out = {}
    for T in T_VALUES:
        q = replace(p, T=T)
        c = cell(q)
        star = " <-" if T == p.T else ""
        print(f"  T = {T:<10} {_fmt(c, q)}{star}")
        out[T] = c
    print("\n  " + "-" * 92)
    print(f"  {'T':>6} {'break-even load':>16} {'claim share':>12} {'ceiling psi*beta':>17}"
          f" {'noise 1/sqrt(T)':>16} {'overshoot':>10}")
    for T in T_VALUES:
        q = replace(p, T=T)
        over = (q.P_ema - q.F_ema) / (2 * q.P_ema * T)
        print(f"  {T:>6} {core.min_fee_load(q):>16,.0f} {T / q.n_tx_ref:>12.1%}"
              f" {q.psi * q.beta:>17.2%} {1 / T ** 0.5:>16.1%} {over:>10.2%}")
    print("\n  ! drain is reachable inside one epoch (T/rho <= MAX_BLOCK_TXS).")
    print("  Raising T past ~120 puts the drain out of reach but takes the reward below the")
    print("  fee at reference traffic; 500 is under water by an order of magnitude and would")
    print("  need 83 % of every block to be claims. The specified 10 buys margin everywhere")
    print("  except the drain, which is left to the controller (section 3.8).")
    return out


def _sweep(p: Params, title: str, note: str, label: str, variants) -> dict:
    print(f"=== Sweep: {title} (section 6) ===\n")
    print(f"  {note}\n")
    print(_HEAD)
    print("  " + "-" * 92)
    out = {}
    for key, q, is_spec in variants:
        c = cell(q)
        print(f"  {label} = {key:<8} {_fmt(c, q)}{' <-' if is_spec else ''}")
        out[key] = c
    print()
    return out


def sweep_beta(p: Params) -> dict:
    return _sweep(p, "POW_SHARE", "The slice of fees the pool takes. Bounded below by the "
                  "fee floor, above by\n  mining staying junior to staking (~11.8 %).",
                  "beta", [(f"{n}%", replace(p, beta_num=n), n == p.beta_num)
                           for n in BETA_NUM])


def sweep_rho(p: Params) -> dict:
    return _sweep(p, "EPOCH_POW_DISTRIBUTION_RATE",
                  "Speed, never destination -- but it scales R_min, the reserve and the "
                  "drain margin\n  all as 1/rho.",
                  "rho", [(f"1/{d}", replace(p, rho_den=d), d == p.rho_den)
                          for d in RHO_DEN])


def sweep_endowment(p: Params) -> dict:
    return _sweep(p, "R0 / supply", "Generosity against section 4.1's security bound: a "
                  "larger endowment is distributed\n  faster, so more of it can be mined by "
                  "an adversary inside the horizon.",
                  "R0", [(f"{f:.1%}", replace(p, genesis_pool_fraction=f), f == p.genesis_pool_fraction)
                         for f in R0_FRAC])


def sweep_ramp(p: Params) -> dict:
    """The ramp is a property of the test, not of the config, so it gets its own table."""
    print("=== Sweep: adoption ramp horizon (section 6) ===\n")
    print("  How long traffic takes to reach capacity. The endowment must hold sigma >= phi")
    print("  across it; longer ramps need more, superlinearly.\n")
    print(f"  {'ramp':>8} {'endowment needed':>18} {'specified R0':>14} {'margin':>12}")
    print("  " + "-" * 58)
    out = {}
    for years in RAMP_YEARS:
        need = core.min_endowment_for_ramp(p, float(years))
        print(f"  {years:>6} yr {need / p.S_tge:>18.2e} {p.genesis_pool_fraction:>14.2e}"
              f" {p.R0 / need:>11,.0f}x")
        out[years] = need / p.S_tge
    print()
    return out


def sweep_d0(p: Params) -> dict:
    """Honest stake at launch -- section 4.1 shows this dominates the security answer."""
    print("=== Sweep: D0, honest stake at launch (section 6) ===\n")
    print("  The adversary's share is what it mines against what is already staked, so D0")
    print("  moves the answer far more than any reward parameter does.\n")
    print(f"  {'D0':>8} {'h=0.10':>10} {'h=0.33':>10} {'h=0.50':>10}   asymptote h/(h+(1-h)s)")
    print("  " + "-" * 70)
    out = {}
    for d0 in D0_FRAC:
        row = f"  {d0:>7.1%}"
        for h in (0.10, 0.33, 0.50):
            peak = core.peak_adversary_share(p, h, 1.0, d0)
            row += f" {peak:>9.2%}" + ("!" if peak >= 1 / 3 else " ")
            out[(d0, h)] = peak
        row += f"   {', '.join(f'{core.adversary_asymptote(h, 1.0):.0%}' for h in (0.10, 0.33, 0.50))}"
        print(row)
    print("\n  ! exceeds one third. Peaks are horizon figures (the refill never stops);")
    print("  the asymptote is the fixed-D0 artefact section 4.1 names, not a prediction.")
    return out


ALL = {"T": sweep_T, "beta": sweep_beta, "rho": sweep_rho,
       "endowment": sweep_endowment, "ramp": sweep_ramp, "d0": sweep_d0}


def report(p: Params) -> dict:
    out = {}
    for name, fn in ALL.items():
        out[name] = fn(p)
    return out
