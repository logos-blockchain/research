"""The reward pool dynamics and the two difficulty controllers, config-driven.

Transcribed from the specification (bedrock-v1.1-mantle-specification.md, Proof of Work
Operations). Exact integer arithmetic where the protocol uses it.
"""
from __future__ import annotations

from .params import P_FIELD, Params


def sigma(R: float, p: Params) -> float:
    """Per-claim reward for an epoch opened with pool R (LGO). compute_epoch_pow_reward."""
    return (R * p.rho_num) / (p.rho_den * p.T * p.N_b)


def epoch_refill(p: Params, n_tx: int | None = None) -> float:
    """Pool share of the fees one epoch collects, in LGO.

    Fees per block = n_tx * average fee, the average transaction taken as an ordinary
    transfer at the resting price.
    """
    n = p.n_tx_ref if n_tx is None else n_tx
    return p.beta * p.N_b * n * p.transfer_fee()


def r_star(p: Params, n_tx: int | None = None) -> float:
    """The pool's fixed point: refill / rho."""
    return epoch_refill(p, n_tx) / p.rho


def r_min(p: Params) -> float:
    """Pool below which a claim no longer beats its own fee: phi * T * N_b / rho."""
    return p.phi * p.T * p.N_b / p.rho


def sigma_over_phi(p: Params, n_tx: int | None = None) -> float:
    """Steady-state reward per claim over the claim's own fee: psi * beta * n_tx / T."""
    n = p.n_tx_ref if n_tx is None else n_tx
    return p.psi * p.beta * n / p.T


def fee_load(p: Params, n_tx: int | None = None) -> float:
    """A block's fee revenue counted in claim fees: ``Phi_b / phi``. The model's one axis.

    The report parameterises traffic by a transaction count and, separately, by a price
    level. Neither is identified on its own. The refill takes a share of what a block
    collects, so what enters is the *revenue*; and the test of whether mining pays compares
    that revenue against the claim's own fee, which moves with the price level too. The two
    scalings cancel, leaving one dimensionless quantity:

        Phi_hat = Phi_b / phi = psi * n_tx        and        sigma*/phi = beta * Phi_hat / T

    Sweeping ``Phi_hat`` therefore says everything the (n_tx, price) plane says, with one
    axis instead of two, and says it without committing to a price level -- the verdict is
    identical at the resting floor and a thousand times above it.

    It is also *exact* where the count-based form is not: the count form prices every
    transaction as an ordinary transfer, but T of them are claims paying more, so it
    understates the refill by ``T(1/psi - 1)/n_tx``. Revenue per block carries no such
    assumption, because it does not care how the revenue was composed.
    """
    n = p.n_tx_ref if n_tx is None else n_tx
    return p.transfer_fee() * n / p.phi


def sigma_over_phi_from_load(p: Params, load: float) -> float:
    """Steady-state reward over the claim fee, from the fee load alone: ``beta*load/T``."""
    return p.beta * load / p.T


def min_fee_load(p: Params, ratio: float = 1.0) -> float:
    """Fee load a block must collect for ``sigma* >= ratio * phi``: ``ratio * T / beta``.

    At the specified set the break-even load is ``T/beta = 100`` claim fees per block --
    a statement that needs no traffic estimate and no price level.
    """
    return ratio * p.T / p.beta


def builder_edge(p: Params, n_tx: int | None = None, tip_frac: float = 0.5) -> float:
    """A builder's advantage from recovering the tip on its own claims."""
    r = sigma_over_phi(p, n_tx)
    return float("inf") if r <= 1 else 1 + tip_frac / (r - 1)


def next_reward_difficulty(d: int, claims_in_block: int, p: Params) -> int:
    """The memoryless per-block retarget. compute_new_reward_difficulty."""
    demand = max(1, (p.P_ema - p.F_ema) * claims_in_block + p.F_ema * p.T)
    return min((p.T * d * p.P_ema) // demand, P_FIELD - 1)


def simulate_pool(p: Params, epochs: int | None = None, n_tx: int | None = None):
    """Epoch-level pool trajectory at a constant claim rate equal to the target.

    Returns a list of dicts, one per epoch. The controller holds the rate at T, so the
    drain each epoch is T * N_b * sigma_e; arrivals noise is deliberately not modelled
    (the report's A2 discusses what that omits).
    """
    E = p.horizon_epochs if epochs is None else epochs
    R = p.R0
    rows = []
    F = epoch_refill(p, n_tx)
    for e in range(E):
        s = sigma(R, p)
        enabled = s > 0 and R >= s
        drain = (p.T * p.N_b) * s if enabled else 0.0
        rows.append(dict(epoch=e, years=e / p.epochs_per_year, pool=R,
                         sigma=s, sigma_over_phi=s / p.phi, enabled=enabled))
        R = R - drain + F
        if R < 0:
            raise AssertionError(f"pool negative at epoch {e}")
    return rows


def logistic_traffic(p: Params, e: int, years: float, n0: int = 20) -> float:
    """Transactions per block at epoch ``e`` on a logistic ramp from ``n0`` to capacity.

    One definition, shared by the endowment sizing and by the plots, so the two cannot
    drift apart. Maturity is reached at ``years``; the 12.0 puts the ramp's ends near its
    asymptotes rather than cutting them off mid-rise.
    """
    import math

    n_max = p.max_block_txs
    epochs_to_mature = years * p.epochs_per_year
    if epochs_to_mature <= 0:
        return float(n_max)
    x = 12.0 * (e - epochs_to_mature / 2) / epochs_to_mature
    return n0 + (n_max - n0) / (1 + math.exp(-x))


def ramp_trajectory(p: Params, R0: float, years: float, n0: int = 20,
                    horizon_years: float = 20.0) -> list[dict]:
    """Pool and reward across a logistic adoption ramp, at a fixed endowment."""
    horizon = int(horizon_years * p.epochs_per_year)
    R, rows = R0, []
    for e in range(horizon):
        n = logistic_traffic(p, e, years, n0)
        s = sigma(R, p)
        rows.append(dict(epoch=e, years=e / p.epochs_per_year, pool=R, n_tx=n,
                         sigma=s, sigma_over_phi=s / p.phi))
        R = (1 - p.rho) * R + p.beta * p.N_b * n * p.transfer_fee()
    return rows


def peak_adversary_share(p: Params, h: float, honest_stake_frac: float,
                         d0_frac: float, rows: list[dict] | None = None) -> float:
    """Highest share of total stake an adversary with hashrate ``h`` reaches over the horizon.

    Mined coins age one epoch before they count, honest miners stake ``honest_stake_frac`` of
    their winnings, and ``d0_frac`` of supply is already staked at launch. One definition,
    used by both the section 4.1 table and the section 6 sweeps.
    """
    rows = simulate_pool(p) if rows is None else rows
    adv = pend_a = honest = pend_h = peak = 0.0
    for r in rows:
        adv += pend_a
        honest += pend_h
        d = p.T * p.N_b * r["sigma"] if r["enabled"] else 0.0
        pend_a, pend_h = d * h, d * (1 - h) * honest_stake_frac
        tot = d0_frac * p.S_tge + adv + honest
        peak = max(peak, adv / tot if tot else 0.0)
    return peak


def adversary_asymptote(h: float, honest_stake_frac: float) -> float:
    """The limit section 4.1 names: ``h / (h + (1-h)s)``, independent of share and supply."""
    den = h + (1 - h) * honest_stake_frac
    return h / den if den else 0.0


def reconvergence_blocks(p: Params, step: float = 10.0, tol: float = 0.1,
                         limit: int = 400) -> int | None:
    """Blocks for the reward difficulty to recover after the hashrate jumps by ``step``.

    Section 3.6 derives a pole of ``F/P`` and predicts about 22 blocks for a tenfold step.
    Mean-field, matching that derivation: arrivals are taken at their expectation, so this
    is the controller's own response and not an arrival-noise measurement (see
    :mod:`empowering.sampled` for the noisy version).
    """
    d_eq = P_FIELD >> p.reward_difficulty_exp
    d = d_eq
    for n in range(limit):
        lam = step * p.T * d / d_eq          # hashrate is `step` times its equilibrium level
        if abs(lam - p.T) <= tol * p.T:
            return n
        d = next_reward_difficulty(d, lam, p)
    return None


def min_endowment_for_ramp(p: Params, years: float,
                           n0: int = 20, horizon_years: float = 20.0) -> float:
    """Smallest R0 (LGO) keeping sigma_e >= phi across a logistic traffic ramp.

    Traffic grows from n0 to max_block_txs, reaching maturity at `years`. inf when the
    steady state itself sits below the fee, in which case no endowment suffices.
    """
    n_max = p.max_block_txs
    if sigma_over_phi(p, n_max) < 1.0:
        return float("inf")
    R_floor = r_min(p)
    horizon = int(horizon_years * p.epochs_per_year)

    def survives(R0: float) -> bool:
        R = R0
        for e in range(horizon):
            if R < R_floor:
                return False
            F = p.beta * p.N_b * logistic_traffic(p, e, years, n0) * p.transfer_fee()
            R = (1 - p.rho) * R + F
        return True

    lo = hi = R_floor
    while not survives(hi):
        hi *= 2
        if hi > 1e6 * R_floor:
            return float("inf")
    for _ in range(60):
        mid = (lo + hi) / 2
        if survives(mid):
            hi = mid
        else:
            lo = mid
    return hi
