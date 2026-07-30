"""Closed-form TSI results from ``analysis-total-stake-inference.md``.

Used both as figure overlays and as ground truth for the verification checks. ``q`` is
the honest active-slot utilisation; with uncle references, substitute the effective
``q_eff`` to predict the improved accuracy.
"""

from __future__ import annotations

import numpy as np

ArrayLike = np.ndarray | float


def expected_ratio(f: float, q: ArrayLike) -> ArrayLike:
    """Equilibrium ``E[D_inf] / D_true = log(1-f) / log(1 - f/q)`` for ``q in (f, 1]``."""
    q = np.asarray(q, dtype=float)
    return np.log(1.0 - f) / np.log(1.0 - f / q)


def block_count_ceiling(f: float) -> float:
    """Equilibrium ratio at *full* uncle recovery for the equal-stake limit.

    TSI counts blocks (all lottery wins, rate ``-ln(1-f)`` per slot in the small-stake
    limit), whereas ``f`` is the *active-slot* rate. So even with every orphan recovered the
    estimate equilibrates at ``-ln(1-f)/f`` (~1.017 for f=1/30), not 1.0. This is a
    deterministic overshoot floor, not noise; concentrated (Pareto) stake gives a smaller
    value because of the concavity of ``phi``.
    """
    return -np.log(1.0 - f) / f


def fixed_point_bias(f: float, precision: int = 1000) -> float:
    """Extra multiplicative bias from the spec's integer f-truncation ``int(f*P)/P``."""
    f_p = int(f * precision) / precision
    return f / f_p


def variance_ratio(f: float, q: ArrayLike, T: int, beta: float = 1.0) -> ArrayLike:
    """Equilibrium ``Var[D_inf / D_true]``."""
    q = np.asarray(q, dtype=float)
    er = expected_ratio(f, q)
    return (beta / f) ** 2 * (q / T) * er**2 * (1.0 - f) * f


def variance_bound(f: float, T: int, beta: float = 1.0) -> float:
    """Upper bound on ``Var[D_inf / D_true]`` at ``q = 1`` (perfect network)."""
    return (beta / f) ** 2 / T * (1.0 - f) * f


def beta_stability_bound(f: float, q: ArrayLike) -> ArrayLike:
    """Stability threshold: convergence requires ``beta < 2f/((q-f) log(1/(1-f/q)))``."""
    q = np.asarray(q, dtype=float)
    return 2.0 * f / ((q - f) * np.log(1.0 / (1.0 - f / q)))


def optimal_beta(f: float, q: ArrayLike) -> ArrayLike:
    """Convergence-optimal learning rate ``f/((q-f) log(1/(1-f/q)))``."""
    q = np.asarray(q, dtype=float)
    return f / ((q - f) * np.log(1.0 / (1.0 - f / q)))
