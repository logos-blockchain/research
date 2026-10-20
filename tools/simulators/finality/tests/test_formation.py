"""Gates for the choices a delayed nonce leaves (src/finality_sim/formation.py)."""

import math

import numpy as np
import pytest
from numba import njit

from finality_sim.formation import (NONE, _suffix_max, _window_counts, branch_survival,
                                    distinct_minima, evaluator_bound, formation_counts, open_law)
from finality_sim.nonce import _choices_min, _feasible, _rates

F = 1 / 30
WINDOW = 6 * math.floor(2160 / F)


def test_the_open_event_follows_its_law_under_random_delay():
    """Under random delay the share of windows still open T after the cut-off is the law from B6's
    walk: the backward maximum, the lead after T slots and a post-cut-off maximum."""
    ts = [0, 300, 600, 1200]
    r = formation_counts(F, 1 / 3, WINDOW, 25, ts, 20_000, 3, growth=0.845)
    share = r["open"].mean(axis=0)
    sem = np.sqrt(share * (1 - share) / r["open"].shape[0])
    for t, s, e in zip(ts, share, sem):
        assert open_law(F, 1 / 3, t, 0.845) == pytest.approx(s, abs=4 * e)
    assert all(x > y for x, y in zip(share, share[1:]))
    assert open_law(F, 1 / 3, 3600, 0.845) < 0.05


@pytest.mark.parametrize("kw", [dict(growth=0.845), dict(delta=10)])
def test_with_every_candidate_formed_at_the_start_and_no_margin_the_count_is_g_min(kw):
    """Formed at the sub-window's start and seen at the cut-off, every value B7's count holds is still
    reachable: the per-win count is G_min in every window, crossing or not."""
    for window, m, near in ((WINDOW, 25, 20_000), (77_760, 27, 10_000)):
        r = formation_counts(F, 1 / 3, window, m, [0], 1_500, 5, near_slots=near, honest_at_start=True,
                             **kw)
        assert np.array_equal(r["per_win"][:, 0], r["g"])
        assert r["g"].max() > 2
    assert r["cross"].any()


def _scan(canon, adv, sm, sub, margins, h_rho, w_rho, z):
    """The counts of ``_window_counts`` by a scan of every fork point; None for a crossing window."""
    n = canon.size
    start = n - sub if sub < n else 1
    honest = [t for t in range(n - 1, 0, -1) if canon[t]] + [0]
    wins = [t for t in range(n - 1, 0, -1) if adv[t]]
    nh = len(honest) - 1

    def after(d):
        return [t for t in wins if t > honest[d]]

    def lead(d):
        return len(after(d)) - d

    d_max = max(d for d in range(nh + 1) if d == 0 or lead(d) + z >= 1)
    n0 = sum(1 for t in honest[:nh] if t >= start)
    if d_max >= n0:
        return None
    theta = [min(h_rho[d:n0]) for d in range(n0)]
    rows = []
    for t in margins:
        seen = set()
        for d in range(n0):
            if theta[d] == theta[0]:
                continue
            j = list(h_rho[:n0]).index(theta[d])
            idx = t + honest[j] - start
            if idx < sm.size and lead(d) + sm[idx] >= 1:
                seen.add(theta[d])
        reach = [d for d in range(n0) if lead(d) + sm[t] >= 1]
        per_win = 0
        if reach:
            ds = max(reach)
            per_win = sum(1 for w, tw in enumerate(wins) if tw > honest[ds] and w_rho[w] < theta[ds])
        singles, multi = 0.0, False
        for d in range(n0):
            idx = t + honest[d] - start
            if idx >= sm.size or sm[idx] == NONE:
                continue
            later = after(d)
            for i in range(len(later)):
                if (i + 1) - d + sm[idx] >= 1:
                    singles += theta[d]
            if len(later) >= 2 and len(later) - d + sm[idx] >= 1:
                multi = True
        j0 = list(h_rho[:n0]).index(theta[0])
        idx0 = t + honest[j0] - start
        blind_tag = blind_chained = 0.0
        if idx0 < sm.size and sm[idx0] > NONE:
            for d in range(j0):
                w_d, idx = len(after(d)), t + honest[d] - start
                if w_d and lead(d) + sm[idx0] >= 1 and not (idx < sm.size and lead(d) + sm[idx] >= 1):
                    blind_tag += w_d * theta[0]
                    blind_chained += (2 ** w_d - 1) * theta[0]
        hi = lo = 0.0
        for i2, t2 in enumerate(wins):
            for i1 in range(i2):
                gap = sum(1 for tw in wins if t2 < tw < wins[i1])
                for d in range(n0 - 1, -1, -1):
                    if honest[d] >= t2:
                        continue
                    size = len(after(d)) - gap
                    if sm[t] > NONE and size - d + sm[t] >= 1:
                        hi += theta[d]
                        lo += (1 - (1 - theta[d]) ** size) / size
                        break
        rows.append((len(seen), per_win, singles, hi, lo, multi, min(1.0, blind_tag), min(1.0, blind_chained)))
    return rows


def test_the_counts_follow_a_scan_of_every_fork_on_small_windows():
    """Every count of a window, at every margin, as a direct scan of the fork points finds it."""
    rng = np.random.default_rng(8)
    margins = np.array([0, 2, 5, 9], dtype=np.int64)
    checked = nonzero = blind = 0
    for _ in range(2000):
        n = int(rng.integers(20, 60))
        sub = int(rng.integers(8, n + 4))
        canon = rng.random(n) < 0.25
        canon[0] = False
        adv = rng.random(n) < 0.22
        adv[0] = False
        z = int(rng.integers(0, 4))
        steps = rng.choice([-1, 0, 1], size=40, p=[0.45, 0.3, 0.25])
        path = np.concatenate(([0], np.cumsum(steps)))[: int(rng.integers(5, 41))].astype(np.int64)
        path[0] = max(path[0], 0)
        sm = np.empty(margins.max() + sub + 2, np.int64)
        _suffix_max(path, path.size, sm)
        nh, nw = int(canon[1:].sum()), int(adv[1:].sum())
        h_rho, w_rho = rng.random(nh), rng.random(nw)
        want = _scan(canon, adv, sm, sub, margins, h_rho, w_rho, z)
        if want is None:
            continue
        work = [np.zeros(n + 1, np.bool_)] + [np.zeros(n + 1, np.int64) for _ in range(4)]
        got = _window_counts(canon, adv, sm, n, sub, margins, h_rho, w_rho, math.inf, z, work[0],
                             work[1], work[2], work[3], work[4], np.zeros(n + 1), np.zeros(n + 1, np.int64),
                             np.zeros(n + 1, np.int64), False)
        for k, (hon, per_win, singles, hi, lo, multi, blind_tag, blind_chained) in enumerate(want):
            assert got[4][k] == hon and got[3][k] == per_win and got[8][k] == multi
            assert got[5][k] == pytest.approx(singles, abs=1e-12)
            assert got[6][k] == pytest.approx(hi, abs=1e-12) and got[7][k] == pytest.approx(lo, abs=1e-12)
            assert got[9][k] == pytest.approx(blind_tag, abs=1e-12)
            assert got[10][k] == pytest.approx(blind_chained, abs=1e-12)
            nonzero += (hon + per_win + singles + hi) > 0
            blind += blind_chained > 0
        checked += 1
    assert checked > 600 and nonzero > 300 and blind > 20


def test_the_enumeration_counts_one_value_per_win_as_b7_does():
    """Over every subset, as B7's count allows, one value per win gives B7's G_min; on average a value
    per parent gives more, and a value per prefix more still."""
    rng = np.random.default_rng(9)
    equal = 0
    for _ in range(1500):
        n = int(rng.integers(4, 30))
        canon = rng.random(n) < 0.3
        adv = rng.random(n) < 0.25
        if adv[1:].sum() > 7:
            continue
        z = int(rng.integers(0, 3))
        feasible = np.zeros(n + 1, dtype=bool)
        nh = _feasible(canon, adv, z, feasible)
        d_max = max(d for d in range(nh + 1) if feasible[d])
        if d_max >= nh:
            continue
        wins = [t for t in range(n - 1, 0, -1) if adv[t]]
        honest = [t for t in range(n - 1, 0, -1) if canon[t]]
        w_after = [sum(1 for h in honest if h >= t) for t in wins]     # a win precedes its slot's block
        kept = [x for x in w_after if x <= d_max]
        seed = int(rng.integers(1 << 30))
        got = distinct_minima(z, d_max, nh, np.array(kept), np.random.default_rng(seed), 10**6,
                              any_subset=True)
        values = np.random.default_rng(seed)
        h_rho = values.random(nh)
        w_rho = np.concatenate((values.random(len(kept)), np.ones(len(wins) - len(kept))))
        g, _ = _choices_min(canon, adv, feasible, h_rho, w_rho, math.inf, n)
        assert got["per_win"] == g
        equal += 1
    assert equal > 500
    r = {k: [] for k in ("per_win", "per_parent", "per_prefix")}
    for s in range(300):
        rr = np.random.default_rng(s)
        got = distinct_minima(3, 2, 6, np.array([0, 0, 1, 1, 2]), rr, 10**6)
        for k in r:
            r[k].append(got[k])
    means = {k: float(np.mean(v)) for k, v in r.items()}
    assert means["per_prefix"] > means["per_parent"] + 0.2 > means["per_win"] + 0.4


@njit(cache=True)
def _branch_sample(n_samples, h, a, dead, slots, seed):
    """From a canonical honest block, ``slots`` slots drawn one by one, then the race followed on until
    the branch's lead falls to -60: whether its lead reaches one at the end of slot ``slots`` or at
    any later point."""
    np.random.seed(seed)
    hit = 0
    for _ in range(n_samples):
        lead, best, t, last = 0, -(1 << 30), 0, 0
        while lead > -60 or t < slots:
            t += 1
            if np.random.random() < a:
                lead += 1
            if t > slots and lead > best:
                best = lead
            if np.random.random() < h and t - last > dead:
                last = t
                lead -= 1
            if t == slots:
                best = lead
        hit += best >= 1
    return hit / n_samples


@pytest.mark.parametrize("kw", [dict(growth=0.845), dict(delta=10)])
def test_a_branch_survives_as_its_law_says(kw):
    """A branch from an honest block can still be published after ``slots`` slots as often as
    ``branch_survival`` says: exactly under random delay, from above under a worst case."""
    a, h, dead, _ = _rates(F, 1 / 3, kw.get("growth"), kw.get("delta"))
    for slots in (300, 1200):
        p = _branch_sample(40_000, h, a, dead, slots, 3 + slots)
        sem = math.sqrt(p * (1 - p) / 40_000)
        law = branch_survival(F, 1 / 3, slots, **kw)
        if "growth" in kw:
            assert law == pytest.approx(p, abs=4 * sem + 1e-4)
        else:
            assert p - 3 * sem <= law <= 1.6 * p + 4 * sem


def test_the_evaluator_bound_lies_above_the_branches_seen():
    r = formation_counts(F, 1 / 3, 6 * math.floor(1080 / F), 26, [600], 40_000, 11, delta=10)
    seen = float(r["multi"][:, 0].mean())
    b = evaluator_bound(F, 1 / 3, 6 * math.floor(1080 / F) // 26, 600, delta=10)
    assert seen > 0 and b["bound"] >= seen
    assert evaluator_bound(F, 1 / 3, WINDOW // 25, 600, delta=10)["bound"] < 1e-5


def test_the_delayed_factor_runs_from_every_choice_to_none():
    """With no margin every choice at the cut-off counts: a window with a choice is open there; with a
    margin no lead outlasts, none; in between the factor falls with the margin."""
    r = formation_counts(F, 1 / 3, 6 * 32_400, 26, [0, 300, 1200, 86_400], 4_000, 11, delta=10)
    f = r["open_factor"].mean(axis=0)
    assert np.array_equal(r["open_factor"][:, 0], r["g"]) and r["g"].mean() > 1.05
    assert f[0] > f[1] > f[2] >= 1.0 and f[3] == 1.0


def test_the_blind_switch_lies_below_the_open_chance_after_the_margin():
    """The sampled chance of a blind switch, with its union over the branches' values, stays below the
    open chance averaged over the default's arrival in the sub-window."""
    from finality_sim.formation import blind_bound, open_curve
    window = 6 * math.floor(1080 / F)
    sub = window // 26
    r = formation_counts(F, 1 / 3, window, 26, [600], 20_000, 31, delta=10, level=1)
    ts, shares = open_curve(F, 1 / 3, sub + 1_200, 20_000, 32, delta=10)
    bound = blind_bound(ts, shares, 600, sub)
    sampled = float(r["blind_chained"][:, 0].mean())
    assert 0 < sampled <= bound < 0.1
