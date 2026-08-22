"""The closed forms are distributions, and the tail is where they are used."""

from __future__ import annotations

from math import fsum

import pytest

from pull_confirmation.model import (
    Parameters,
    binomial_pmf_array,
    hypergeometric_pmf,
    hypergeometric_pmf_array,
    hypergeometric_sf,
    liveness_failure,
    security_failure,
    upper_tails,
)


def base(**overrides) -> Parameters:
    kwargs = dict(
        n_providers=500,
        adversarial_fraction=0.33,
        sample_size=8,
        max_rounds=5,
        threshold=20,
        hold_probability=0.99,
    )
    kwargs.update(overrides)
    return Parameters(**kwargs)


@pytest.mark.parametrize(
    "population,successes,draws",
    [(500, 165, 40), (100, 50, 10), (1000, 1, 40), (60, 59, 30), (25, 10, 25)],
)
def test_hypergeometric_array_matches_pointwise(population, successes, draws):
    array = hypergeometric_pmf_array(population, successes, draws)
    for k in range(draws + 1):
        expected = hypergeometric_pmf(population, successes, draws, k)
        assert array[k] == pytest.approx(expected, rel=1e-9, abs=1e-15)


@pytest.mark.parametrize(
    "population,successes,draws",
    [(500, 165, 40), (100, 50, 10), (2000, 900, 200)],
)
def test_hypergeometric_array_is_a_distribution(population, successes, draws):
    assert fsum(hypergeometric_pmf_array(population, successes, draws)) == pytest.approx(1.0)


@pytest.mark.parametrize("n,p", [(40, 0.99), (200, 0.5), (10, 0.01), (64, 1.0), (64, 0.0)])
def test_binomial_array_is_a_distribution(n, p):
    assert fsum(binomial_pmf_array(n, p)) == pytest.approx(1.0)


def test_upper_tails_are_consistent_with_the_pmf():
    pmf = hypergeometric_pmf_array(500, 165, 40)
    tails = upper_tails(pmf)
    assert tails[0] == pytest.approx(1.0)
    for k in range(len(pmf)):
        assert tails[k] == pytest.approx(fsum(pmf[k:]), abs=1e-15)


def test_tail_keeps_its_digits_far_from_the_mode():
    # The security bound lives out here: 40 draws from a set that is a third
    # adversarial, asking for 35 of them. Summing from the mode outward would
    # round this to zero.
    value = hypergeometric_sf(1000, 330, 40, 35)
    assert 0.0 < value < 1e-12


def test_security_falls_and_liveness_rises_with_the_threshold():
    security = [security_failure(base(threshold=t)) for t in range(1, 41)]
    liveness = [liveness_failure(base(threshold=t)) for t in range(1, 41)]
    assert security == sorted(security, reverse=True)
    assert liveness == sorted(liveness)


def test_an_unreachable_threshold_is_secure_and_dead():
    # More attestations demanded than providers queried: nothing can confirm,
    # which is perfectly private and perfectly useless.
    params = base(sample_size=4, max_rounds=2, threshold=99)
    assert not params.reachable
    assert security_failure(params) == 0.0
    assert liveness_failure(params) == 1.0


def test_an_honest_network_never_confirms_a_tagged_transaction():
    assert security_failure(base(adversarial_fraction=0.0)) == 0.0


def test_a_sample_cannot_exceed_the_set():
    params = base(n_providers=20, sample_size=8, max_rounds=10)
    assert params.total_sampled == 20


@pytest.mark.parametrize("fraction", [-0.1, 1.0, 1.5])
def test_rejects_impossible_fractions(fraction):
    with pytest.raises(ValueError):
        base(adversarial_fraction=fraction)


class TestAdversaryRounding:
    """The adversary count rounds up — a security tool must not round it away."""

    def test_one_third_of_5000_is_1667(self):
        assert base(n_providers=5000, adversarial_fraction=1 / 3).n_adversarial == 1667

    def test_exact_halves_round_up(self):
        assert base(n_providers=50, adversarial_fraction=0.33).n_adversarial == 17
        assert base(n_providers=10, adversarial_fraction=0.45).n_adversarial == 5

    def test_float_artifacts_do_not_add_an_adversary(self):
        # 0.33 * 5000 == 1650.0000000000002 in floats; a naive ceil would say 1651.
        assert base(n_providers=5000, adversarial_fraction=0.33).n_adversarial == 1650

    def test_the_count_never_exceeds_the_set(self):
        assert base(n_providers=10, adversarial_fraction=0.999999).n_adversarial == 10
