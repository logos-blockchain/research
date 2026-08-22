"""Search the parameter space for a (sample, threshold) pair that satisfies both bounds.

The calibration question is not "is this threshold safe" but "what is the
cheapest run that is safe *and* live". Cheapest means fewest providers queried,
because the query count is what the protocol pays per transaction batch.

For a fixed total sample ``S`` the two bounds pull ``t`` in opposite directions,
so the feasible thresholds for that ``S`` form an interval — possibly empty. The
search walks ``S`` upward and returns the first ``S`` whose interval is
non-empty, together with the ``t`` in it that leaves the most security margin,
since security failure is the one that cannot be retried away.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

from .model import (
    Parameters,
    attesting_count_pmf,
    hypergeometric_pmf_array,
    liveness_failure,
    security_failure,
    upper_tails,
)

__all__ = ["Target", "Feasible", "feasible_thresholds", "calibrate", "sweep_fraction"]


@dataclass(frozen=True)
class Target:
    """Failure probabilities the calibration must not exceed.

    ``max_security_failure`` is a cryptographic-style bound: a tagging attempt
    that succeeds once has revealed a proposer, and no retry undoes it.
    ``max_liveness_failure`` may be looser — a transaction that fails to confirm
    in one run is still pending, still gossiped, and confirms on a later run.
    """

    max_security_failure: float = 1e-9
    max_liveness_failure: float = 1e-6


@dataclass(frozen=True)
class Feasible:
    params: Parameters
    security_failure: float
    liveness_failure: float

    @property
    def total_queries(self) -> int:
        return self.params.total_sampled


def feasible_thresholds(params: Parameters, target: Target) -> list[int]:
    """Thresholds that satisfy both bounds at this sample size, low to high.

    ``params.threshold`` is ignored; every threshold up to the total sample is
    tried. The two distributions are built once and every threshold is read off
    their cumulative sums — evaluating the closed forms per threshold instead
    would rebuild the same two distributions for each one.

    Security failure falls as the threshold rises and liveness failure rises with
    it, so the result is contiguous. It is still produced by scanning rather than
    by bisecting on that monotonicity, so that a modelling error which broke it
    would show up as a gap here rather than as a silently wrong boundary.
    """
    draws = params.total_sampled

    adversarial_tail = upper_tails(
        hypergeometric_pmf_array(params.n_providers, params.n_adversarial, draws)
    )
    attesting = attesting_count_pmf(params)
    attesting_below = _prefix_sums(attesting)

    out: list[int] = []
    for threshold in range(1, draws + 1):
        if adversarial_tail[threshold] > target.max_security_failure:
            continue
        if attesting_below[threshold] > target.max_liveness_failure:
            continue
        out.append(threshold)
    return out


def _prefix_sums(pmf: list[float]) -> list[float]:
    """``out[k] = P[X < k]``, accumulated from below so small head mass survives."""
    out = [0.0] * (len(pmf) + 1)
    running = 0.0
    for k, value in enumerate(pmf):
        out[k] = min(1.0, running)
        running += value
    out[len(pmf)] = min(1.0, running)
    return out


def calibrate(
    base: Parameters,
    target: Target,
    *,
    max_total_sample: int = 4096,
    stability_window: int = 4,
) -> Feasible | None:
    """Smallest total sample from which both bounds are met *and stay* met.

    ``base`` supplies the set size, adversarial fraction, hold probability and
    withholding assumption. Its ``sample_size``, ``max_rounds`` and ``threshold``
    are placeholders: the search sets the total sample directly and reports it,
    leaving how to split that total across rounds to the caller, since rounds
    trade latency against nothing else.

    **Why stability rather than the first feasible sample.** Both bounds are
    thresholds on an integer count, and they step at different sample sizes. Just
    where the window opens it is one or two thresholds wide, so a sample size
    that admits a threshold is often followed by one that admits none — the
    security bound steps up while the liveness bound has not yet moved. Those
    isolated points are real, but they are knife edges: a percent of drift in the
    hold probability or the adversarial fraction closes them. Reporting one as a
    protocol constant would be reporting a coincidence. The search therefore
    looks for the first sample from which feasibility holds across
    ``stability_window`` consecutive sizes, which is also what makes it safe to
    bisect — the stable predicate is monotone where raw feasibility is not.

    Returns ``None`` when nothing within ``max_total_sample`` works, which is the
    honest answer when the adversarial fraction leaves no window at all.
    """
    ceiling = min(max_total_sample, base.n_providers)

    def has_option(total: int) -> bool:
        # Clamp instead of failing: a nominal sample beyond the ceiling draws
        # exactly the ceiling (total_sampled caps at the set), so its
        # feasibility IS the ceiling's. Returning False here instead would make
        # stable() structurally false near the ceiling and the search would
        # report feasible regions as infeasible.
        probe = replace(base, sample_size=min(total, ceiling), max_rounds=1, threshold=1)
        return bool(feasible_thresholds(probe, target))

    def stable(total: int) -> bool:
        return all(has_option(total + offset) for offset in range(stability_window))

    # Widen by doubling, but land on the ceiling rather than jumping past it —
    # a bracket that only ever tests powers of two would miss a first stable
    # sample lying between the last power of two and the ceiling.
    upper = 1
    while not stable(upper):
        if upper >= ceiling:
            return None
        upper = min(upper * 2, ceiling)

    lower = upper // 2 + 1
    while lower < upper:
        middle = (lower + upper) // 2
        if stable(middle):
            upper = middle
        else:
            lower = middle + 1

    probe = replace(base, sample_size=lower, max_rounds=1, threshold=1)
    options = feasible_thresholds(probe, target)
    # Lowest security failure among feasible thresholds — the highest one, given
    # that security failure is decreasing in the threshold. Recomputed rather
    # than assumed, for the reason given in feasible_thresholds.
    best = min((replace(probe, threshold=t) for t in options), key=security_failure)
    return Feasible(
        params=best,
        security_failure=security_failure(best),
        liveness_failure=liveness_failure(best),
    )


def first_feasible_sample(
    base: Parameters,
    target: Target,
    *,
    max_total_sample: int = 4096,
) -> int | None:
    """The smallest feasible sample, isolated knife edges included.

    Exposed so that the gap between this and :func:`calibrate` can be inspected
    rather than taken on faith. Scans, because the predicate it tests is the
    non-monotone one.
    """
    ceiling = min(max_total_sample, base.n_providers)
    for total in range(1, ceiling + 1):
        probe = replace(base, sample_size=total, max_rounds=1, threshold=1)
        if feasible_thresholds(probe, target):
            return total
    return None


def sweep_fraction(
    base: Parameters,
    target: Target,
    fractions: list[float],
    *,
    max_total_sample: int = 4096,
) -> list[tuple[float, Feasible | None]]:
    """Calibrate across adversarial fractions, to show how the cost grows."""
    return [
        (
            f,
            calibrate(
                replace(base, adversarial_fraction=f),
                target,
                max_total_sample=max_total_sample,
            ),
        )
        for f in fractions
    ]
