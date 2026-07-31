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
    """LEGACY-mode ceiling: the equilibrium ratio under ``legacy_block_count=True``.

    Applies only to the superseded per-*block* counting (``tsi.density_m(...,
    legacy_block_count=True)``), which counted every lottery win (rate ``-ln(1-f)`` per slot
    in the small-stake limit) while ``f`` is the *active-slot* rate. In that mode, even with
    every orphan recovered the estimate equilibrated at ``-ln(1-f)/f`` (~1.017 for f=1/30) —
    a deterministic overshoot, not noise; concentrated (Pareto) stake gave a smaller value
    from the concavity of ``phi``. The default slot-counting engine has no such ceiling: the
    equilibrium is bounded by 1 (report §2.1/§2.2).
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
