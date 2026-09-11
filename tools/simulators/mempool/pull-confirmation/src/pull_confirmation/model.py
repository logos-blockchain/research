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
count here is hypergeometric rather than binomial. At the set sizes Bedrock
expects the distinction is not cosmetic: without-replacement draws concentrate
the count, so the binomial approximation *overstates* the security tail (by
roughly 3x at the design point). The exact model is what makes the calibrated
sample genuinely minimal — a binomial calibration would be safe but oversized.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, comb, fsum, inf, log2

__all__ = [
    "Parameters",
    "majority_threshold",
    "majority_parameters",
    "specification_parameters",
    "hypergeometric_pmf",
    "hypergeometric_sf",
    "security_failure",
    "liveness_failure",
    "attesting_count_pmf",
    "sequential_security_failure",
    "sequential_liveness_failure",
    "sequential_confirmation_by_round",
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
        min_sample: zero selects the fixed rule — ``threshold`` attestations
            over the whole run. A positive value selects the specification's
            rule: after every round, the transaction is confirmed when more
            than half of the providers asked so far attest, with the
            denominator floored at ``min_sample``. ``threshold`` is then the
            majority of that floor, which is the earliest the rule can fire.
            The floor is capped at the set, as ``PULL_SAMPLE`` is.
    """

    n_providers: int
    adversarial_fraction: float
    sample_size: int
    max_rounds: int
    threshold: int
    hold_probability: float = 1.0
    adversary_withholds: bool = False
    min_sample: int = 0

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
        if self.min_sample < 0:
            raise ValueError("min_sample must be non-negative")
        if self.min_sample and self.threshold != majority_threshold(
            min(self.min_sample, self.n_providers)
        ):
            raise ValueError(
                "under the sequential rule the threshold is the majority of the floor; "
                "build these with specification_parameters()"
            )

    @property
    def sequential(self) -> bool:
        """Whether the specification's rule, rather than a fixed threshold, applies."""
        return self.min_sample > 0

    @property
    def floor(self) -> int:
        """The denominator floor of the sequential rule, capped at the set."""
        return min(self.min_sample, self.n_providers)

    @property
    def n_adversarial(self) -> int:
        """Adversarial providers in the set, rounded **up** to a whole node.

        A security tool must not round the adversary away: banker's rounding
        would drop an exact half-node down half the time, and ``f = 1/3`` of
        5000 must mean 1667 adversaries, not 1666. The product is snapped to 6
        decimals first so float artifacts (``0.33 * 5000 == 1650.0000000000002``)
        do not conjure an extra adversary out of representation error.
        """
        return min(self.n_providers, ceil(round(self.adversarial_fraction * self.n_providers, 6)))

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


def majority_threshold(sample: int) -> int:
    """The smallest attestation count that is more than half of ``sample``.

    This is the specification's rule: a transaction is confirmed when more
    than half of the distinct providers asked about it attest. It is stated
    relative to the sample so that no absolute count is tied to a set size —
    the same rule is a majority of 128 on a large set and a majority of the
    whole set on a small one.
    """
    if sample < 1:
        raise ValueError("sample must be positive")
    return sample // 2 + 1


def majority_parameters(
    n_providers: int,
    adversarial_fraction: float,
    sample_size: int,
    max_rounds: int,
    hold_probability: float = 1.0,
    adversary_withholds: bool = False,
) -> Parameters:
    """Parameters whose threshold is the majority of the providers actually asked."""
    total = min(sample_size * max_rounds, n_providers)
    return Parameters(
        n_providers=n_providers,
        adversarial_fraction=adversarial_fraction,
        sample_size=sample_size,
        max_rounds=max_rounds,
        threshold=majority_threshold(total),
        hold_probability=hold_probability,
        adversary_withholds=adversary_withholds,
    )


def specification_parameters(
    n_providers: int,
    adversarial_fraction: float,
    sample_size: int = 16,
    max_rounds: int = 16,
    min_sample: int = 128,
    hold_probability: float = 1.0,
    adversary_withholds: bool = False,
) -> Parameters:
    """Parameters for the rule the specification states.

    A transaction is confirmed when more than half of the providers that have
    answered a query about it attest, counting at least ``min_sample``
    (``PULL_SAMPLE``) in the denominator, evaluated after every round for up to
    ``max_rounds`` rounds of ``sample_size`` draws. The defaults are the
    specification's constants.
    """
    if min_sample < 1:
        raise ValueError("min_sample must be positive")
    return Parameters(
        n_providers=n_providers,
        adversarial_fraction=adversarial_fraction,
        sample_size=sample_size,
        max_rounds=max_rounds,
        threshold=majority_threshold(min(min_sample, n_providers)),
        hold_probability=hold_probability,
        adversary_withholds=adversary_withholds,
        min_sample=min_sample,
    )


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

    n_rest = n_population - n_success
    for k in range(mode, hi):
        # P[k+1] / P[k]
        ratio = ((n_success - k) * (n_draws - k)) / ((k + 1) * (n_rest - n_draws + k + 1))
        unnormalised[k + 1] = unnormalised[k] * ratio

    for k in range(mode, lo, -1):
        # P[k-1] / P[k]
        ratio = (k * (n_rest - n_draws + k)) / ((n_success - k + 1) * (n_draws - k + 1))
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

    Under the sequential rule the question is instead whether the adversarial
    count ever exceeds half the draws at a round boundary, and the answer
    comes from :func:`sequential_security_failure`.
    """
    if params.sequential:
        return sequential_security_failure(params)
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
    if params.sequential:
        return sequential_liveness_failure(params)
    if not params.reachable:
        return 1.0
    pmf = attesting_count_pmf(params)
    return min(1.0, fsum(pmf[: params.threshold]))


def security_margin_bits(params: Parameters) -> float:
    """Security failure probability expressed as -log2, for readable comparison."""
    p = security_failure(params)
    return inf if p <= 0.0 else -log2(p)


# --- the sequential rule ----------------------------------------------------
#
# The specification does not fix the sample and then count. It keeps asking,
# and at the start of every round it confirms each transaction for which more
# than half of everyone who has answered attests, with the denominator floored
# at PULL_SAMPLE so that the first few answers cannot decide alone. Confirmation
# is recorded and never revisited. A refusal is therefore never final: it is
# outvoted by later draws rather than retried. Two things follow that the fixed
# rule's closed forms cannot give. The adversary gets a chance at every round
# boundary past the floor instead of one, so the security tail is a
# first-passage probability over those checks. And a slow-propagating
# transaction keeps collecting attestations after the floor, so liveness no
# longer hinges on the hold probability at one instant.
#
# Both are computed exactly by walking the draw sequence as a Markov chain on
# the running counts, removing the mass that confirms at each round boundary.
# Checking after every response instead would roughly double the security
# tail, which is why the specification checks once a round. Draws are without
# replacement, as in the rest of this module. The closed forms above are the
# special case of a single check at the last round.


def _confirms(count: int, drawn: int, floor: int) -> bool:
    """The specification's test: more than half of max(drawn, floor) attest."""
    return 2 * count > max(drawn, floor)


def _walk_tagged(params: Parameters) -> list[float]:
    """Mass confirmed in each round for a tagged transaction.

    Only adversarial draws attest, so the state is the adversarial count.
    """
    n, a_total = params.n_providers, params.n_adversarial
    floor = params.floor
    alive: dict[int, float] = {0: 1.0}
    drawn = 0
    out: list[float] = []
    for _ in range(params.max_rounds):
        for _ in range(params.sample_size):
            if drawn >= n:
                break
            remaining = n - drawn
            nxt: dict[int, float] = {}
            for a, mass in alive.items():
                p_adv = (a_total - a) / remaining
                if p_adv > 0.0:
                    nxt[a + 1] = nxt.get(a + 1, 0.0) + mass * p_adv
                if p_adv < 1.0:
                    nxt[a] = nxt.get(a, 0.0) + mass * (1.0 - p_adv)
            alive = nxt
            drawn += 1
        out.append(fsum(m for a, m in alive.items() if _confirms(a, drawn, floor)))
        alive = {a: m for a, m in alive.items() if not _confirms(a, drawn, floor)}
    return out


def _walk_broadcast(params: Parameters) -> tuple[list[float], float]:
    """Mass confirmed in each round for a broadcast transaction, and the rest.

    When the adversary cooperates every draw attests with the hold probability
    and the state is the attestation count alone. When it withholds only honest
    draws can attest, so the state carries the adversarial count as well.
    """
    n, a_total = params.n_providers, params.n_adversarial
    floor, hold = params.floor, params.hold_probability
    withholds = params.adversary_withholds
    alive: dict[tuple[int, int], float] = {(0, 0): 1.0}
    drawn = 0
    out: list[float] = []
    for _ in range(params.max_rounds):
        for _ in range(params.sample_size):
            if drawn >= n:
                break
            remaining = n - drawn
            nxt: dict[tuple[int, int], float] = {}

            def add(key: tuple[int, int], mass: float) -> None:
                if mass > 0.0:
                    nxt[key] = nxt.get(key, 0.0) + mass

            for (a, y), mass in alive.items():
                p_adv = (a_total - a) / remaining if withholds else 0.0
                if p_adv > 0.0:
                    add((a + 1, y), mass * p_adv)
                p_rest = 1.0 - p_adv
                if p_rest > 0.0:
                    add((a, y + 1), mass * p_rest * hold)
                    add((a, y), mass * p_rest * (1.0 - hold))
            alive = nxt
            drawn += 1
        out.append(fsum(m for (_, y), m in alive.items() if _confirms(y, drawn, floor)))
        alive = {k: m for k, m in alive.items() if not _confirms(k[1], drawn, floor)}
    return out, fsum(alive.values())


def sequential_security_failure(params: Parameters) -> float:
    """P[a tagged transaction confirms at some round boundary]."""
    if not params.sequential:
        raise ValueError("sequential_security_failure needs min_sample > 0")
    return min(1.0, fsum(_walk_tagged(params)))


def sequential_liveness_failure(params: Parameters) -> float:
    """P[a broadcast transaction is still unconfirmed after the last round]."""
    if not params.sequential:
        raise ValueError("sequential_liveness_failure needs min_sample > 0")
    _, rest = _walk_broadcast(params)
    return min(1.0, rest)


def sequential_confirmation_by_round(params: Parameters) -> list[float]:
    """P[a broadcast transaction confirms at round r], indexed from round 1.

    Sums to one minus the liveness failure. The mean of this distribution is
    the expected number of rounds a confirming transaction spends, which is the
    latency figure the deployment pays.
    """
    if not params.sequential:
        raise ValueError("sequential_confirmation_by_round needs min_sample > 0")
    out, _ = _walk_broadcast(params)
    return out
