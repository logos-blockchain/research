"""Deanonymization metrics: exact closed forms + a Monte-Carlo tie to the actual draw.

A *deanonymization* event is a round whose whole blend path is adversarial; *full* deanonymization
additionally requires the honest sender to be directly peered with an adversary. Relays are drawn
uniformly blind to who is adversarial, so both rates are exact (no sampling in production)."""

import numpy as np

from blend.adversary import adversary_metrics, deanon_metrics, place_adversary
from blend.config import SimConfig
from blend.engine import run_graph_cell
from blend.graph import build_graph


def test_deanon_rate_hand_computed():
    # n=4, 2 adversaries, honest sender leaves 3 nodes (2 adversarial) in the relay pool;
    # k=2 distinct relays both adversarial: C(2,2)/C(3,2) = 1/3.
    dz = deanon_metrics(n=4, n_adv=2, observed_frac=0.5, blend_hops=2)
    assert abs(dz["deanon_rate"] - 1.0 / 3.0) < 1e-12
    assert abs(dz["full_deanon_rate"] - (1.0 / 3.0) * 0.5) < 1e-12


def test_deanon_rate_zero_when_too_few_adversaries():
    assert deanon_metrics(n=100, n_adv=1, observed_frac=0.9, blend_hops=2)["deanon_rate"] == 0.0
    assert deanon_metrics(n=100, n_adv=0, observed_frac=0.0, blend_hops=1)["deanon_rate"] == 0.0
    # too few adversaries -> no full deanonymization either
    too_few = deanon_metrics(n=100, n_adv=1, observed_frac=0.9, blend_hops=2)
    assert too_few["full_deanon_rate"] == 0.0


def test_full_deanon_is_deanon_times_observed():
    dz = deanon_metrics(n=5000, n_adv=1000, observed_frac=0.73, blend_hops=3)
    assert abs(dz["full_deanon_rate"] - dz["deanon_rate"] * 0.73) < 1e-12
    assert dz["full_deanon_rate"] <= dz["deanon_rate"] + 1e-12


def test_deanon_rate_is_placement_independent_but_full_is_not():
    """The whole-path-adversarial rate depends only on the adversary COUNT; the full rate also
    tracks how many honest nodes are peered with an adversary, which the worst case maximizes."""
    g = build_graph(SimConfig(n_nodes=2000, degree=6, graph_seed=0))
    rng = np.random.default_rng(0)
    rand = adversary_metrics(g, place_adversary(g, 0.2, "random", rng, 10**9))
    wc = adversary_metrics(g, place_adversary(g, 0.2, "worstcase_coverage", rng, 10**9))
    assert rand["n_adv"] == wc["n_adv"]                       # same budget
    dz_rand = deanon_metrics(g.n, rand["n_adv"], rand["observed_frac"], 3)
    dz_wc = deanon_metrics(g.n, wc["n_adv"], wc["observed_frac"], 3)
    assert abs(dz_rand["deanon_rate"] - dz_wc["deanon_rate"]) < 1e-12   # placement-independent
    assert dz_wc["full_deanon_rate"] >= dz_rand["full_deanon_rate"] - 1e-12  # worst case >= random


def test_deanon_asymptotic_fadv_power():
    # C(A,k)/C(n-1,k) -> f_adv^k for large n.
    f, k, n = 0.3, 3, 20000
    dz = deanon_metrics(n=n, n_adv=int(round(f * n)), observed_frac=0.5, blend_hops=k)
    assert abs(dz["deanon_rate"] - f ** k) < 0.002


def test_deanon_matches_direct_sampling():
    """Closed form == empirical rate of the exact honest-sender/blind-relay draw the sim uses."""
    f, k = 0.33, 2
    cfg = SimConfig(n_nodes=1500, degree=8, graph_seed=3, f_adv=f, blend_hops=k)
    g = build_graph(cfg)
    mask = place_adversary(g, f, "random", np.random.default_rng(1), cfg.worstcase_max_n)
    adv = adversary_metrics(g, mask)
    dz = deanon_metrics(g.n, adv["n_adv"], adv["observed_frac"], k)

    counts = np.add.reduceat(mask[g.indices].astype(np.int32), g.indptr[:-1])
    observed_node = counts >= 1
    honest = np.where(~mask)[0]
    n = g.n
    rng = np.random.default_rng(42)
    trials, d_hit, fd_hit = 40_000, 0, 0
    for _ in range(trials):
        s = int(rng.choice(honest))
        r = rng.choice(n - 1, size=k, replace=False)
        r[r >= s] += 1
        if mask[r].all():
            d_hit += 1
            fd_hit += int(observed_node[s])
    assert abs(dz["deanon_rate"] - d_hit / trials) < max(0.006, 0.1 * dz["deanon_rate"])
    assert abs(dz["full_deanon_rate"] - fd_hit / trials) < max(0.006, 0.12 * dz["full_deanon_rate"])


def test_engine_emits_deanon_rows():
    base = SimConfig(n_nodes=1000, degree=8, graph_seed=0, n_placements=2)
    prop_grid = [(2, 0), (3, 0)]                 # distinct blend_hops = {2, 3}
    adv_grid = [(0.2, "random"), (0.0, "random")]
    prop_rows, adv_rows, deanon_rows, _ = run_graph_cell(base, prop_grid, [0.0], [1], adv_grid)

    # one deanon row per (placement, distinct blend_hops, redundancy)
    assert len(deanon_rows) == len(adv_rows) * 2
    cols = {"n_nodes", "degree", "blend_hops", "redundancy", "f_adv", "adversary_mode",
            "graph_seed", "placement_rep", "n_adv", "n_honest", "observed_frac",
            "deanon_rate", "full_deanon_rate"}
    assert cols <= set(deanon_rows[0])
    assert {row["blend_hops"] for row in deanon_rows} == {2, 3}
    for row in deanon_rows:
        assert 0.0 <= row["full_deanon_rate"] <= row["deanon_rate"] + 1e-12
        if row["f_adv"] == 0.0:
            assert row["deanon_rate"] == 0.0            # no adversary -> no deanonymization


# --- attribution confidence -----------------------------------------------------------------------

def test_attribution_confidence_endpoints_and_monotonicity():
    """d/(2d-a): the 0.5 prior with no watched links, certainty when every link is watched."""
    from blend.adversary import attribution_confidence
    d = 8
    assert abs(float(attribution_confidence(0, d)) - 0.5) < 1e-12
    assert abs(float(attribution_confidence(d, d)) - 1.0) < 1e-12
    vals = [float(attribution_confidence(a, d)) for a in range(d + 1)]
    assert all(b > a for a, b in zip(vals, vals[1:], strict=False))
    assert abs(vals[1] - 1 / (2 - 1 / 8)) < 1e-12          # one peer buys only ~0.53


def test_confidence_does_not_depend_on_the_number_of_relays():
    """The conditioning event fixes the relays as adversarial, so an honest sender is not one of
    them; the path length cannot enter the estimator."""
    import inspect

    from blend.adversary import attribution_confidence
    src = inspect.getsource(attribution_confidence)
    assert "blend_hops" not in src and "hops" not in src.split('"""')[2]


def test_high_confidence_attribution_equals_the_eclipse_condition():
    """At degree 8, 90% confidence needs a >= 8 -- every peer adversarial. So the confidence-
    weighted attribution collapses onto eclipse, not onto observed."""
    from blend.adversary import adversary_metrics, attribution_metrics, place_adversary
    g = build_graph(SimConfig(n_nodes=20000, degree=8, graph_seed=0))
    for f in (0.33, 0.5):
        mask = place_adversary(g, f, "random", np.random.default_rng(0), 10**9)
        am = adversary_metrics(g, mask)
        at = attribution_metrics(g, mask)
        assert abs(at["attributable_frac_90"] - am["eclipsed_frac"]) < 1e-12
        assert abs(at["attributable_frac_50"] - am["observed_frac"]) < 1e-12   # >=1 peer clears 0.5


def test_confident_attribution_is_far_rarer_than_observation():
    """The correction that matters: observed_frac massively overstates confident attribution."""
    from blend.adversary import adversary_metrics, attribution_metrics, place_adversary
    g = build_graph(SimConfig(n_nodes=20000, degree=8, graph_seed=1))
    mask = place_adversary(g, 0.2, "random", np.random.default_rng(1), 10**9)
    am = adversary_metrics(g, mask)
    at = attribution_metrics(g, mask)
    assert am["observed_frac"] > 0.8
    assert at["attributable_frac_90"] < 1e-4
    assert at["attribution_conf_mean"] < 0.6        # one or two peers buys very little
