"""Splits and eclipses when finality is counted in slots (SLOTS.md, K.3).

With finality counted in slots, ``B_imm`` is the latest block of the local chain at least ``K``
slots old. A node then fixes its chain once a block the rest of the network lacks is ``K`` slots
old, whatever stake made that block, the node's own blocks included. Counted in blocks the chain
needs ``k`` blocks after the divergence first. A density floor ``φ`` holds ``B_imm`` back until
``φ`` blocks of the local chain follow the block.

The floor takes two forms. The depth form moves ``B_imm`` to a block once it is ``K`` slots old
and ``φ`` blocks deep, the later of a time and a depth: a sparse chain is fixed once it has made
``φ`` blocks. The density form moves it there only once the ``K`` slots after the block hold ``φ``
blocks: a chain too sparse over ``K`` is not fixed until its density rises, when its inference has
corrected or the split has ended.

Counts over a window of ``w`` slots follow B5's laws (``recovery.honest_logpmf``): binomial at the
canonical growth ``g`` times the stake's slot occupancy under random delay; under a worst case of
``Δ`` the renewal law, ``P(N ≤ n) = P(Bin(w − (n + 1)Δ, p) ≤ n)``. A chain made by a share ``s`` at
its fastest holds one block per slot the share occupies, ``growth = 1``.
"""

from __future__ import annotations

import math

from scipy import stats

from .recovery import occupancy

F = 1 / 30


def log_cdf(n: int, w: int, share: float, f: float = F, growth: float | None = None,
            delta: int | None = None) -> float:
    """log P(N ≤ n) for the blocks a chain made by ``share`` holds in ``w`` slots."""
    if (growth is None) == (delta is None):
        raise ValueError("set exactly one of growth and delta")
    if n < 0:
        return -math.inf
    p = occupancy(f, share)
    if growth is not None:
        return float(stats.binom.logcdf(n, w, growth * p))
    trials = w - (n + 1) * delta
    if trials < n + 1:
        return 0.0
    return float(stats.binom.logcdf(n, trials, p))


def chain_rate(share: float, f: float = F, growth: float | None = None,
               delta: int | None = None) -> float:
    """The blocks per slot of a chain made by ``share``, in either model."""
    p = occupancy(f, share)
    return growth * p if growth is not None else 1.0 / (delta + 1.0 / p)


def floor_for(w: int, alpha: float, eps: float, f: float = F, growth: float | None = None,
              delta: int | None = None) -> int:
    """The largest floor ``φ`` that the honest chain a coalition of ``alpha`` withholds from
    reaches within ``w`` slots with chance at least ``1 − eps``: ``P(N ≤ φ − 1) ≤ eps``."""
    target = math.log(eps)
    lo, hi = 0, w + 1                     # lo satisfies the condition; hi does not
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if log_cdf(mid - 1, w, 1.0 - alpha, f, growth, delta) <= target:
            lo = mid
        else:
            hi = mid
    return lo


def log_short(w: int, phi: int, share: float, f: float = F, growth: float | None = None,
              delta: int | None = None) -> float:
    """log P(N < φ): the chance that a chain made by ``share`` holds fewer than ``φ`` blocks in
    ``w`` slots, so that the floor holds its finality past ``w``."""
    return log_cdf(phi - 1, w, share, f, growth, delta)


def log_reach(w: int, phi: int, share: float, f: float = F, growth: float = 1.0) -> float:
    """log P(N ≥ φ) for a chain made by ``share`` at ``growth`` blocks per occupied slot."""
    return float(stats.binom.logsf(phi - 1, w, growth * occupancy(f, share)))


def safe_floor(w: int, share: float, eps: float, f: float = F, growth: float = 1.0) -> int:
    """The smallest floor that a chain made by ``share`` at ``growth`` reaches within ``w`` slots
    with chance at most ``eps``: ``P(N ≥ φ) ≤ eps``."""
    return int(stats.binom.isf(eps, w, growth * occupancy(f, share))) + 1


def provisional_share(w: int, phi: int, eps: float, f: float = F, growth: float = 1.0) -> float:
    """The largest share whose chain, at its fastest, reaches the floor within ``w`` slots with
    chance at most ``eps``: a side of a split at or below it stays provisional."""
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if log_reach(w, phi, mid, f, growth) <= math.log(eps) else (lo, mid)
    return lo


def quorum(w: int, alpha: float, eps: float, f: float = F, live_growth: float | None = None,
           live_delta: int | None = None, side_growth: float = 1.0) -> tuple[int, int]:
    """The floor's two limits over a window of ``w`` slots, ``(φ_live, φ_safe)``. Liveness: the
    honest chain a coalition of ``alpha`` withholds from reaches ``φ_live`` (``floor_for``).
    Safety: a side of share ``(1 + α)/2``, the smaller of two partition sides that both hold the
    coalition's blocks, reaches ``φ_safe`` with chance at most ``eps``. A floor that does both
    exists when ``φ_live ≥ φ_safe``."""
    live = floor_for(w, alpha, eps, f, live_growth, live_delta)
    safe = safe_floor(w, (1.0 + alpha) / 2, eps, f, side_growth)
    return live, safe


def least_quorum_window(alpha: float, eps: float, f: float = F, live_growth: float | None = None,
                        live_delta: int | None = None, side_growth: float = 1.0,
                        w_max: int = 400_000_000) -> int | None:
    """The shortest window at which a floor separates the sides of any partition and lets the
    honest chain a coalition of ``alpha`` withholds from finalize, each at ``eps``. ``None`` when
    the honest chain grows no faster than the side, where no window does, or past ``w_max``."""
    if chain_rate(1.0 - alpha, f, live_growth, live_delta) <= chain_rate((1.0 + alpha) / 2, f,
                                                                          growth=side_growth):
        return None

    def ok(w: int) -> bool:
        live, safe = quorum(w, alpha, eps, f, live_growth, live_delta, side_growth)
        return live >= safe

    hi = 1024
    while not ok(hi):
        hi *= 2
        if hi > w_max:
            return None
    lo = hi // 2
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (lo, mid) if ok(mid) else (mid, hi)
    return hi


def blocks_time(n: int, share: float, eps: float, f: float = F) -> tuple[float, int]:
    """For a chain made by ``share`` alone at one block per occupied slot: the mean slots to its
    ``n``-th block, and the earliest slot by which it holds ``n`` with chance at least ``eps``."""
    p = occupancy(f, share)
    target = math.log(eps)
    lo, hi = n - 1, n                     # lo fails; hi is raised until it holds
    while stats.binom.logsf(n - 1, hi, p) < target:
        lo, hi = hi, hi * 2
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (lo, mid) if stats.binom.logsf(n - 1, mid, p) >= target else (mid, hi)
    return n / p, hi


def after_correction(n: int, share: float, epoch_slots: int, f: float = F) -> float:
    """The mean slots to the ``n``-th block of a chain made by ``share`` alone, started with an
    epoch: its inference corrects in full at the next epoch, ``epoch_slots`` later, and from then
    the share fills its slots at ``f`` (``FURTHER.md`` G7). Before that, the share's own occupancy."""
    p = occupancy(f, share)
    before = p * epoch_slots
    if n <= before:
        return n / p
    return epoch_slots + (n - before) / f


def density_fix(share: float, phi: int, w: int, epoch_slots: int, eps: float, f: float = F,
                growth: float = 1.0) -> tuple[float, float]:
    """Under the density form: the log10 chance that the ``w`` slots after a block of a chain made
    by ``share`` hold ``φ`` blocks, and when such a chain, started with an epoch, is fixed. At even
    odds or better, ``w`` slots after its first block. At ``eps`` or less, only once its inference
    has corrected at the next epoch and a window after it is dense: ``epoch_slots + w``. Between
    the two, ``nan``."""
    lr = log_reach(w, phi, share, f, growth)
    if lr >= math.log(0.5):
        return lr / math.log(10), w + 1.0 / occupancy(f, share)
    if lr <= math.log(eps):
        return lr / math.log(10), float(epoch_slots + w)
    return lr / math.log(10), math.nan
