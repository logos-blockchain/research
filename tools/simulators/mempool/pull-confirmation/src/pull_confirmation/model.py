"""Closed-form failure probabilities for mempool pull confirmation.

The protocol under analysis is the pull half of mempool dissemination: a node
samples providers from the active declaration set, asks whether they hold a
transaction, and treats signed positive answers as attestations. A transaction
that collects ``t`` attestations from distinct providers is *confirmed*, and only
confirmed transactions are offered to block building.

Two failure modes bound ``t`` from opposite sides, and the whole point of this
module is that they are opposite.

**Security failure — a tagged transaction confirms.** The adversary delivers a
transaction to exactly one node and to nobody else. Every honest provider
truthfully answers that it does not hold it, so the only providers that can
attest are the adversary's own, which do hold it (the adversary authored it).
The attack succeeds precisely when the node draws ``t`` or more adversarial
providers over the whole run. Note what this means: a *larger* ``t`` is safer.

**Liveness failure — a genuinely broadcast transaction never confirms.** The
transaction really did spread, so an honest provider holds it with probability
``p_hold`` and attests. The node fails to confirm when fewer than ``t`` of the
providers it samples attest. Here a *smaller* ``t`` is safer.

So ``t`` must sit strictly between the number of adversarial providers a run is
likely to draw and the number of attesting providers it is likely to draw. That
window exists only when the adversarial fraction leaves room for it, and its
width — not the value of ``t`` alone — is what decides how large the sample has
to be.

Sampling is without replacement from a finite set of declarations, so every
count here is hypergeometric rather than binomial. For the set sizes Bedrock
expects that distinction is not cosmetic: at ``N`` a few hundred and a sample of
tens, the binomial approximation understates the tail that matters.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb, fsum, inf, isfinite

__all__ = [
    "Parameters",
    "hypergeometric_pmf",
    "hypergeometric_sf",
    "security_failure",
    "liveness_failure",
    "attesting_count_pmf",
]


@dataclass(frozen=True)
class Parameters:
    """One point in the parameter space.

    Attributes:
        n_providers: size of the active declaration set the node samples from.
        adversarial_fraction: share of that set the adversary controls.
        sample_size: providers queried per confirmation round.
        max_rounds: rounds a node spends on one transaction before giving up.
        threshold: distinct attestations required to confirm.
        hold_probability: probability that an honest sampled provider already
            holds a genuinely broadcast transaction when it is asked. This is
            the propagation coverage reached after ``PULL_DELAY``; it is the
            only place the delay parameter enters the analysis.
        adversary_withholds: whether the adversary refuses to attest to
            transactions it does hold. Withholding cannot make a tagged
            transaction confirm, so it does not enter the security bound; it
            costs liveness, by removing the adversary's share of the sample
            from the attesting pool.
    """

    n_providers: int
    adversarial_fraction: float
    sample_size: int
    max_rounds: int
    threshold: int
    hold_probability: float = 1.0
    adversary_withholds: bool = False

    def __post_init__(self) -> None:
        if self.n_providers < 1:
            raise ValueError("n_providers must be positive")
        if not 0.0 <= self.adversarial_fraction < 1.0:
            raise ValueError("adversarial_fraction must be in [0, 1)")
        if self.sample_size < 1 or self.max_rounds < 1:
            raise ValueError("sample_size and max_rounds must be positive")
        if self.threshold < 1:
            raise ValueError("threshold must be positive")
        if not 0.0 <= self.hold_probability <= 1.0:
            raise ValueError("hold_probability must be in [0, 1]")

    @property
    def n_adversarial(self) -> int:
        """Adversarial providers in the set, rounded to a whole node."""
        return round(self.adversarial_fraction * self.n_providers)

    @property
    def total_sampled(self) -> int:
        """Distinct providers queried over a whole run.

        Rounds draw fresh providers, so the run's draws accumulate — but they
        cannot exceed the set. A node that would query more providers than exist
        simply queries all of them.
        """
        return min(self.sample_size * self.max_rounds, self.n_providers)

    @property
    def reachable(self) -> bool:
        """Whether the threshold can be met at all within the round budget."""
        return self.threshold <= self.total_sampled


def hypergeometric_pmf(n_population: int, n_success: int, n_draws: int, k: int) -> float:
    """P[X = k] for X hypergeometric: k successes in n_draws from n_population."""
    if k < 0 or k > n_draws or k > n_success:
        return 0.0
    if n_draws - k > n_population - n_success:
        return 0.0
    return comb(n_success, k) * comb(n_population - n_success, n_draws - k) / comb(
        n_population, n_draws
    )


def hypergeometric_pmf_array(n_population: int, n_success: int, n_draws: int) -> list[float]:
    """The whole hypergeometric pmf, indexed by success count.

    Built by walking a ratio recurrence out from the mode rather than by calling
    :func:`hypergeometric_pmf` per point. Both the cost and the accuracy matter:
    the per-point form evaluates three binomial coefficients that are astronomically
    large before they cancel, which is slow at the set sizes this tool sweeps and
    loses precision exactly in the far tail the security bound lives in.
    """
    lo = max(0, n_draws - (n_population - n_success))
    hi = min(n_draws, n_success)
    if hi < lo:
        return [0.0] * (n_draws + 1)

    # Anchor at the mode, where the pmf is largest, and spread outward. Starting
    # from an endpoint would underflow long before reaching the mode.
    mode = min(hi, max(lo, (n_draws + 1) * (n_success + 1) // (n_population + 2)))
    unnormalised = [0.0] * (n_draws + 1)
    unnormalised[mode] = 1.0

    for k in range(mode, hi):
        # P[k+1] / P[k]
        ratio = ((n_success - k) * (n_draws - k)) / ((k + 1) * (n_population - n_success - n_draws + k + 1))
        unnormalised[k + 1] = unnormalised[k] * ratio

    for k in range(mode, lo, -1):
        # P[k-1] / P[k]
        ratio = (k * (n_population - n_success - n_draws + k)) / ((n_success - k + 1) * (n_draws - k + 1))
        unnormalised[k - 1] = unnormalised[k] * ratio

    total = fsum(unnormalised)
    return [value / total for value in unnormalised]


def binomial_pmf_array(n: int, p: float) -> list[float]:
    """The whole binomial pmf, by the same anchored recurrence and for the same reasons."""
    if p <= 0.0:
        return [1.0] + [0.0] * n
    if p >= 1.0:
        return [0.0] * n + [1.0]

    mode = min(n, max(0, int((n + 1) * p)))
    unnormalised = [0.0] * (n + 1)
    unnormalised[mode] = 1.0
    odds = p / (1.0 - p)

    for k in range(mode, n):
        unnormalised[k + 1] = unnormalised[k] * ((n - k) / (k + 1)) * odds
    for k in range(mode, 0, -1):
        unnormalised[k - 1] = unnormalised[k] * (k / (n - k + 1)) / odds

    total = fsum(unnormalised)
    return [value / total for value in unnormalised]


def upper_tails(pmf: list[float]) -> list[float]:
    """``out[k] = P[X >= k]``, accumulated from the top so tail digits survive."""
    out = [0.0] * (len(pmf) + 1)
    running = 0.0
    for k in range(len(pmf) - 1, -1, -1):
        running += pmf[k]
        out[k] = min(1.0, running)
    return out


def hypergeometric_sf(n_population: int, n_success: int, n_draws: int, k: int) -> float:
    """P[X >= k]."""
    if k <= 0:
        return 1.0
    if k > min(n_draws, n_success):
        return 0.0
    return upper_tails(hypergeometric_pmf_array(n_population, n_success, n_draws))[k]


def security_failure(params: Parameters) -> float:
    """P[a transaction delivered to one node only reaches the threshold].

    Honest providers do not hold the transaction and say so, so the node's
    attestations can only come from adversarial providers. The attack therefore
    succeeds exactly when the run draws ``threshold`` or more of them.
    """
    if not params.reachable:
        return 0.0
    return hypergeometric_sf(
        params.n_providers,
        params.n_adversarial,
        params.total_sampled,
        params.threshold,
    )


def attesting_count_pmf(params: Parameters) -> list[float]:
    """Distribution of attestations collected for a genuinely broadcast transaction.

    When the adversary cooperates, who is adversarial does not matter: every
    drawn provider holds the transaction with ``hold_probability`` and attests,
    so the count is plainly binomial in the number of draws and the hypergeometric
    split never enters.

    Withholding is what makes the split matter. The willing providers are then
    the honest ones drawn — a hypergeometric count — and the attestations are
    binomial within them, so the answer is a mixture over the split.

    Returns a list indexed by attestation count.
    """
    draws = params.total_sampled

    if not params.adversary_withholds:
        return binomial_pmf_array(draws, params.hold_probability)

    split = hypergeometric_pmf_array(params.n_providers, params.n_adversarial, draws)
    pmf = [0.0] * (draws + 1)
    for n_adv_drawn, p_split in enumerate(split):
        if p_split == 0.0:
            continue
        n_willing = draws - n_adv_drawn
        inner = binomial_pmf_array(n_willing, params.hold_probability)
        for k, p_k in enumerate(inner):
            pmf[k] += p_split * p_k
    return pmf


def liveness_failure(params: Parameters) -> float:
    """P[a genuinely broadcast transaction fails to reach the threshold]."""
    if not params.reachable:
        return 1.0
    pmf = attesting_count_pmf(params)
    return min(1.0, fsum(pmf[: params.threshold]))


def security_margin_bits(params: Parameters) -> float:
    """Security failure probability expressed as -log2, for readable comparison."""
    p = security_failure(params)
    if p <= 0.0:
        return inf
    from math import log2

    value = -log2(p)
    return value if isfinite(value) else inf
