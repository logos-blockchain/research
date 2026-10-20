"""Phase G, further routes (PLAN.md, phase G).

G1, a delayed nonce: ``finality_sim.formation``.

G4, settlement on a chain nobody withholds from. B4's elapsed-time rule accepts the ``n``-th
canonical block counting the target when the coalition's exact chance, given the time ``t`` since
the target's parent, is at most ``ε``. ``time_rule_depth`` is the block at which it accepts when
blocks arrive at their mean spacing: at the full rate ``g λ`` of a chain nobody withholds from, or
at the honest rate ``(1 - α) g λ`` of one the coalition withholds from. The total-stake inference
sets the lottery's thresholds from the previous period's occupied slots, so a coalition that
withholds for a whole period raises every rate by ``1 / (1 - α)``: the honest chain then runs at
``g λ`` while the coalition wins at ``α λ / (1 - α)``. The ``adjusted`` rule takes those rates,
which bound the coalition in both worlds since the catch-up ratio ``a / h`` is the same.
``density_depth`` is a rule that reads the chain's density directly; ``density_chance`` gives the
exact conditional chance at its acceptance, for comparison with the elapsed-time rule.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats

from finality_sim.elapsed import deadlines, log_fail
from finality_sim.private_race import log_strict, strict_depth


def _rule_rates(alpha: float, g: float, f: float, adjusted: bool) -> tuple[float, float]:
    lam = -math.log(1 - f)
    if adjusted:
        return alpha * lam / (1 - alpha), g * lam
    return alpha * lam, (1 - alpha) * g * lam


def time_rule_depth(alpha: float, g: float, eps: float, f: float = 1 / 30, full_rate: bool = True,
                    adjusted: bool = False) -> int:
    """The first canonical block counting the target at which B4's elapsed-time rule accepts when
    the ``n``-th block arrives ``n / rate`` slots after the parent, ``rate`` the full rate ``g λ`` or
    the withheld-from rate ``(1 - α) g λ``; -1 if none within three times B5's depth."""
    lam = -math.log(1 - f)
    a, h = _rule_rates(alpha, g, f, adjusted)
    world = g * lam if full_rate else (1 - alpha) * g * lam
    plain = int(strict_depth(alpha / (alpha + (1 - alpha) * g), math.log(eps)))
    dl = deadlines(a, h, eps, 3 * plain + 60)
    for n in range(1, dl.size):
        if dl[n] >= 0 and dl[n] >= n / world:
            return n
    return -1


def density_depth(alpha: float, g: float, eps: float, f: float = 1 / 30, step: float = 0.01,
                  test: bool = True) -> tuple[int, float]:
    """The depth at which a chain at the full rate settles against every withheld share up to
    ``alpha`` under a rule that multiplies the race's chance by the chance of seeing that many
    blocks under the attack, and the share that needs the most depth. Without ``test`` the density
    is ignored and the depth is B5's at ``alpha``."""
    lam = -math.log(1 - f)
    shares = np.arange(step, alpha + step / 2, step)
    shares = np.append(shares[shares < alpha], alpha)
    plain = int(strict_depth(alpha / (alpha + (1 - alpha) * g), math.log(eps)))
    for d in range(1, plain + 1):
        n = d + 1
        t = n / (g * lam)
        worst, worst_w = -math.inf, alpha
        for w in shares:
            q = w / (w + (1 - w) * g)
            lp = log_strict(q, n)
            if test:
                lp += float(stats.poisson.logsf(n - 1, (1 - w) * g * lam * t))
            if lp > worst:
                worst, worst_w = lp, float(w)
        if worst <= math.log(eps):
            return d, worst_w
    return plain, alpha


def density_chance(alpha: float, g: float, eps: float, f: float = 1 / 30) -> float:
    """log of the coalition's exact conditional chance (B4) at the point where ``density_depth``
    accepts a chain at the full rate."""
    lam = -math.log(1 - f)
    d, _ = density_depth(alpha, g, eps, f)
    n = d + 1
    a, h = _rule_rates(alpha, g, f, False)
    return log_fail(n, n / (g * lam), a, h)


# Phase H.1: recovery attestations and partition detection.

def attestation_seats(alpha: float, eps: float, eps_live: float,
                      undelivered: float = 0.0) -> tuple[int, int]:
    """The fewest expected seats ``n`` of a one-off attestation round, and its threshold ``theta``,
    such that a fork backed by a share ``alpha`` of the stake draws ``theta`` seats or more with
    chance at most ``eps``, while an honest side of an even partition, backed by ``(1 - alpha)/2``
    with a share ``undelivered`` of its votes lost, draws fewer than ``theta`` with chance at most
    ``eps_live``. Seats are Poisson in the share. ``(-1, -1)`` when the side's share is not above
    ``alpha``, where no threshold separates them.

    Whether ``n`` seats suffice is not monotone in ``n``, since ``theta`` moves in whole seats, so
    a bisection can stop above the fewest: the seats are doubled until they suffice, and every
    count below is scanned."""
    side = (1 - alpha) / 2 * (1 - undelivered)
    if side <= alpha:
        return -1, -1

    def holds(n: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        theta = stats.poisson.isf(eps, alpha * n).astype(np.int64) + 1     # P(X >= theta) <= eps
        return theta, stats.poisson.cdf(theta - 1, side * n) <= eps_live

    hi = 1
    while not holds(np.array([hi]))[1][0]:
        hi *= 2
        if hi > 1 << 30:
            return -1, -1
    n = np.arange(1, hi + 1)
    theta, ok = holds(n)
    first = int(np.argmax(ok))
    return int(n[first]), int(theta[first])


def detector_power(alpha: float, g: float, w: int, eps: float, sides, f: float = 1 / 30):
    """Rule 8 as a partition detector. The threshold is the ``eps`` lower tail of the canonical
    count the honest stake ``1 - alpha`` makes alone over ``w`` slots under random delay with
    growth ``g``; a chain below it is sparse. Returns the threshold and, for each share in
    ``sides``, the chance that a side holding that share of all stake falls below it."""
    from finality_sim.recovery import honest_logpmf, occupancy
    cdf = np.cumsum(np.exp(honest_logpmf(w, occupancy(f, 1 - alpha), growth=g)))
    threshold = int(np.searchsorted(cdf, eps, side="right"))    # P(N < threshold) <= eps
    powers = []
    for s in sides:
        c = np.cumsum(np.exp(honest_logpmf(w, occupancy(f, s), growth=g)))
        powers.append(float(c[threshold - 1]) if threshold > 0 else 0.0)
    return threshold, powers


# Phase H.3: the time-reading rule under a worst case.

def counting_ratio(alpha: float, delta: int, f: float = 1 / 30) -> float:
    """The catch-up ratio of the counting bound: after acceptance a competing chain gains at most
    the coalition's wins plus the honest wins the canonical chain does not keep, ``a + h - h_w``,
    against the canonical chain's worst-case growth ``h_w = 1 / (Δ + 1/p_h)``. At or above one the
    bound says nothing."""
    from finality_sim.recovery import occupancy
    a, h = occupancy(f, alpha), occupancy(f, 1 - alpha)
    h_w = 1.0 / (delta + 1.0 / h)
    return (a + h - h_w) / h_w


def counting_logp(n: int, t: float, alpha: float, delta: int, f: float = 1 / 30) -> float:
    """log of the counting bound on the coalition's chance, given ``n`` canonical blocks counting
    the target, under a worst case of ``delta``. ``t`` is the client's clock when it evaluates,
    less the parent's slot: a block the coalition released late carries a slot earlier than the
    clock, and the wins of the slots between count. The client keeps the chain it holds on a
    tie, as Cryptarchia's Online rule keeps the first-seen chain, so a competing chain must be
    strictly longer.

    Every block is a distinct lottery win. Above the parent the competing chain holds at most the
    coalition's wins ``A(t)``, each of which may also sit on the canonical chain, and the honest
    wins ``H(t)`` that the canonical chain does not hold. With ``n_h`` honest blocks among the
    canonical ``n``, it holds at most ``A + H - n_h`` blocks and must exceed ``n = n_h + A_c``, with
    ``A_c <= A`` the coalition's canonical blocks: it leads by at most ``2A + H - 2n``. Before the
    parent it holds the stationary lead ``L`` of the worst-case walk, geometric with the catch-up
    ratio ``counting_ratio``. The target falls if ``L + 2A + H >= 2n + 1`` at acceptance, or later
    with chance ``rho^(2n + 1 - L - 2A - H)``. ``A`` and ``H`` are Poisson at the slot occupancies.
    """
    from finality_sim.recovery import occupancy
    a, h = occupancy(f, alpha), occupancy(f, 1 - alpha)
    rho = counting_ratio(alpha, delta, f)
    if rho >= 1.0:
        return 0.0
    log_rho = math.log(rho)
    need = 2 * n + 1
    top = need + 1
    pa = stats.poisson.pmf(np.arange(top), a * t)                    # A = 0..need
    x = np.zeros(2 * top)                                             # 2A
    x[::2] = pa
    ph = stats.poisson.pmf(np.arange(top), h * t)
    x = np.convolve(x, ph)[:top]                                      # 2A + H below need + 1
    lead = (1 - rho) * rho ** np.arange(top)                          # L = 0..need
    y = np.convolve(x, lead)[:top]                                    # L + 2A + H
    below = y[:need]                                                  # values 0..need - 1
    catch = float(np.sum(below * rho ** (need - np.arange(need))))
    reach = max(0.0, 1.0 - float(np.sum(below)))                      # at least need
    return math.log(max(reach + catch, 1e-300))


def counting_observed_logp(n: int, t: float, forks: int, alpha: float, delta: int,
                           f: float = 1 / 30, ties_to_coalition: bool = False) -> float:
    """log of the counting bound when the client also counts the ``forks`` it has received: the
    distinct slots of the blocks with a slot after the target's parent's that do not descend from
    the target (``finality_sim.forks``). ``t`` is the client's clock less the parent's slot, as in
    ``counting_logp``.

    An honest block sits on one chain, and one that descends from the target sits on no chain
    without it. A chain holds one block per slot. The honest blocks a competing chain holds above
    the parent therefore sit at distinct slots among the forks received, once the blocks of the last
    ``delta`` slots, ``H_late``, Poisson at the honest occupancy over ``delta``, have arrived. The
    coalition's wins ``A(t)`` may sit anywhere, and the lead ``L`` before the parent is the
    worst-case walk's. The competing chain holds at most ``L + A + forks + H_late`` blocks above
    the parent against the canonical ``n``. The client keeps its chain on a tie, so the target
    falls if ``L + A + H_late >= n + 1 - forks`` at acceptance, or later by a catch-up at the
    ratio ``counting_ratio``; with ``ties_to_coalition`` a tie suffices. A coalition that
    publishes its wins as forks raises ``forks`` by at most one a win; the bound stays sound and
    the rule accepts later.
    """
    from finality_sim.recovery import occupancy
    a, h = occupancy(f, alpha), occupancy(f, 1 - alpha)
    rho = counting_ratio(alpha, delta, f)
    if rho >= 1.0:
        return 0.0
    need = n + 1 - forks - int(ties_to_coalition)                     # L + A + H_late must reach it
    if need <= 0:
        return 0.0
    top = need + 1
    x = np.convolve(stats.poisson.pmf(np.arange(top), a * t),
                    stats.poisson.pmf(np.arange(top), h * delta))[:top]
    y = np.convolve(x, (1 - rho) * rho ** np.arange(top))[:top]       # L + A + H_late, below top
    below = y[:need]
    catch = float(np.sum(below * rho ** (need - np.arange(need))))
    reach = max(0.0, 1.0 - float(np.sum(below)))
    return math.log(max(reach + catch, 1e-300))


def counting_observed_depth(alpha: float, delta: int, eps: float, rate: float, forks: int = 0,
                            forks_per_slot: float = 0.0, f: float = 1 / 30,
                            ties_to_coalition: bool = False) -> int:
    """The first depth at which ``counting_observed_logp`` holds ``eps`` when the client holds the
    ``n``-th block ``n / rate`` slots after the parent and has received ``forks`` plus
    ``forks_per_slot`` a slot; -1 if none below 5,000."""
    if counting_ratio(alpha, delta, f) >= 1.0:
        return -1
    for d in range(1, 5000):
        n = d + 1
        t = n / rate
        if counting_observed_logp(n, t, forks + int(forks_per_slot * t), alpha, delta, f,
                                  ties_to_coalition) <= math.log(eps):
            return d
    return -1


def counting_observed_deadlines(alpha: float, delta: int, eps: float, n_max: int, forks,
                                f: float = 1 / 30) -> np.ndarray:
    """For ``n = 1..n_max`` (rows) and each count in ``forks`` (columns), the latest ``t`` at
    which the ``n``-th block still settles under ``counting_observed_logp``; -1 where none does.
    The bound rises with ``t`` and with the forks."""
    out = np.full((n_max + 1, len(forks)), -1.0)
    target = math.log(eps)
    for j, k in enumerate(forks):
        for n in range(1, n_max + 1):
            if counting_observed_logp(n, 0.0, k, alpha, delta, f) > target:
                continue
            lo, hi = 0.0, 1.0
            while counting_observed_logp(n, hi, k, alpha, delta, f) <= target:
                hi *= 2
            for _ in range(40):
                mid = (lo + hi) / 2
                lo, hi = (mid, hi) if counting_observed_logp(n, mid, k, alpha, delta, f) <= target else (lo, mid)
            out[n, j] = lo
    return out


def observed_settle(canon: np.ndarray, deadlines: np.ndarray, forks: np.ndarray,
                    fork_grid, clock: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Play the observed counting rule: for each target canonical block ``i`` with a parent, the
    confirmations at which the rule accepts it and the slots from the target to acceptance, -1
    where it never does. ``deadlines[n, j]`` is the deadline for the ``n``-th block at
    ``fork_grid[j]`` forks, and a target with more forks than the grid holds is not accepted.
    ``clock[m]`` is the slot at which the client holds canonical block ``m``, its slot when not
    given: the rule reads its clock then, less the parent's slot."""
    clock = canon if clock is None else clock
    n_c, n_max = canon.size, deadlines.shape[0] - 1
    col = {int(k): j for j, k in enumerate(fork_grid)}
    k_out = np.full(n_c, -1, np.int64)
    t_out = np.full(n_c, -1, np.result_type(clock, np.int64))
    for i in range(1, n_c):
        j = col.get(int(forks[i]))
        if j is None:
            continue
        for n in range(1, n_max + 1):
            m = i + n - 1
            if m >= n_c:
                break
            if deadlines[n, j] >= 0 and clock[m] - canon[i - 1] <= deadlines[n, j]:
                k_out[i] = n - 1
                t_out[i] = clock[m] - canon[i]
                break
    return k_out, t_out


def counting_depth(alpha: float, delta: int, eps: float, rate: float, f: float = 1 / 30) -> int:
    """The first depth at which ``counting_logp`` holds ``eps`` when the client holds the ``n``-th
    block ``n / rate`` slots after the parent; -1 if none below 5,000."""
    if counting_ratio(alpha, delta, f) >= 1.0:
        return -1
    for d in range(1, 5000):
        n = d + 1
        if counting_logp(n, n / rate, alpha, delta, f) <= math.log(eps):
            return d
    return -1


def counting_deadlines(alpha: float, delta: int, eps: float, n_max: int,
                       f: float = 1 / 30) -> np.ndarray:
    """For ``n = 1..n_max``, the latest ``t`` at which the ``n``-th block still settles under the
    counting bound; -1 where none does. The bound rises with ``t``."""
    out = np.full(n_max + 1, -1.0)
    target = math.log(eps)
    for n in range(1, n_max + 1):
        if counting_logp(n, 0.0, alpha, delta, f) > target:
            continue
        lo, hi = 0.0, 1.0
        while counting_logp(n, hi, alpha, delta, f) <= target:
            hi *= 2
        for _ in range(40):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if counting_logp(n, mid, alpha, delta, f) <= target else (lo, mid)
        out[n] = lo
    return out
