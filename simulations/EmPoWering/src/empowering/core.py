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


def min_endowment_for_ramp(p: Params, years: float,
                           n0: int = 20, horizon_years: float = 20.0) -> float:
    """Smallest R0 (LGO) keeping sigma_e >= phi across a logistic traffic ramp.

    Traffic grows from n0 to max_block_txs, reaching maturity at `years`. inf when the
    steady state itself sits below the fee, in which case no endowment suffices.
    """
    import math

    n_max = p.max_block_txs
    if sigma_over_phi(p, n_max) < 1.0:
        return float("inf")
    R_floor = r_min(p)
    epochs_to_mature = years * p.epochs_per_year
    horizon = int(horizon_years * p.epochs_per_year)

    def traffic(e: int) -> float:
        if epochs_to_mature <= 0:
            return n_max
        x = 12.0 * (e - epochs_to_mature / 2) / epochs_to_mature
        return n0 + (n_max - n0) / (1 + math.exp(-x))

    def survives(R0: float) -> bool:
        R = R0
        for e in range(horizon):
            if R < R_floor:
                return False
            F = p.beta * p.N_b * traffic(e) * p.transfer_fee()
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
