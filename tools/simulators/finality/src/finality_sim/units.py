"""Stake counted in anonymous units (UNITS.md N.1, N.2).

**Units.** A unit is a fixed amount ``μ`` of stake. Once an epoch a holder registers each unit its
notes hold, under a fresh key and a proof that hides the note, so every node counts the ``U``
registered units and none can tell whose they are. The coalition holds ``A_U = round(α·U)`` of
them.

**What a counted committee holds (N.1).** Honest votes split between two sides still fill both, so
two conflicting certificates of quorum ``Q`` need ``H + 2A ≥ 2Q`` of the committee's honest and
coalition units: D0's rule, and M.1's count. A round stalls when the honest units online, each
online with chance ``u``, fall short of ``Q``.

- *Public draw.* The ``n`` keys with the lowest values of a function of the key and the round's
  randomness. Every node knows the drawn units, and the coalition's drawn units are hypergeometric,
  ``A ~ Hyp(U, A_U, n)``. Two conflicting certificates need ``A ≥ 2Q − n``.
- *Private draw.* Each unit draws by its secret, a seat with chance ``p``, so ``A ~ Bin(A_U, p)``
  and ``H ~ Bin(U − A_U, p)`` are independent, and the quorum is fixed from the count's mean ``pU``,
  which every node knows.
- *Every unit voting.* No draw, so safety is exact: ``A_U < 2Q − U``. Liveness needs
  ``u(1 − a) ≥ q > (1 + a)/2`` in the limit of many units, for the coalition's share ``a`` of the
  units and the quorum share ``q``.

**Rounding.** The coalition sizes its notes in whole units. An honest note loses its value below a
whole unit, less than one unit a note. With a share ``ρ`` of the honest stake lost, the coalition
holds ``α/(α + (1 − α)(1 − ρ))`` of the units.

**The registry and the lottery (N.2).** Registrations for an epoch go on chain in the previous
epoch's stake distribution snapshot phase, once the snapshot is final, so the registry closes a
buffer phase before the epoch nonce is fixed, as the snapshot does. If the leader lottery divides
by the registered stake, only registered stake leads, and the true over the counted stake is the
online share of the registered stake, ``α + (1 − α)·u`` with the coalition online: at most one.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import special, stats

from finality_sim import netcert as nc

F = 1 / 30
K_OVER_F = math.floor(2160 / F)          # ⌊k/f⌋ = 64,800 slots
EPOCH_SLOTS = 10 * K_OVER_F              # cryptarchia-v1-protocol.md, Epoch Schedule
SNAPSHOT_PHASE = 3 * K_OVER_F            # the stake distribution snapshot phase
SCAN = 400                               # the window below a bisected committee scanned for the lattice

# A registration: the unit key, its proof (a Groth16 proof, 128 bytes, as inside
# ProofOfLeadership), the tag that stops a second registration, and the epoch it is for.
REGISTRATION_FIELDS = {"unit key": 32, "proof": 128, "tag": 32, "epoch": 4}


def registered_units(active: float = nc.STAKED_SHARE, unit: float = nc.MIN_STAKE_SHARE) -> int:
    """The units the active stake makes, both as shares of the supply."""
    return math.floor(active / unit + 1e-9)


def coalition_units(alpha: float, units: int) -> int:
    """The coalition's units: its share of the registered units, rounded."""
    return round(alpha * units)


def hyper_pmf(n: int, units: int, adv: int) -> np.ndarray:
    """``P(A = a)`` for ``a = 0..n``, ``A ~ Hyp(units, adv, n)``, from log-gamma."""
    a = np.arange(n + 1)
    ok = (a <= adv) & (n - a <= units - adv)
    ac = np.where(ok, a, 0)
    log = (special.gammaln(adv + 1) - special.gammaln(ac + 1) - special.gammaln(adv - ac + 1)
           + special.gammaln(units - adv + 1) - special.gammaln(n - ac + 1)
           - special.gammaln(units - adv - n + ac + 1)
           - special.gammaln(units + 1) + special.gammaln(n + 1) + special.gammaln(units - n + 1))
    return np.where(ok, np.exp(log), 0.0)


def _public_quorum(n: int, units: int, adv: int, eps: float,
                   pmf: np.ndarray | None = None) -> int | None:
    """The smallest quorum that keeps two conflicting certificates within ``eps``:
    ``P(A ≥ 2Q − n) ≤ eps`` for ``A ~ Hyp(units, adv, n)``."""
    pmf = hyper_pmf(n, units, adv) if pmf is None else pmf
    sf = np.cumsum(pmf[::-1])[::-1]                                     # sf[a] = P(A ≥ a)
    qs = np.arange(n // 2 + 1, n + 1)
    safe = sf[2 * qs - n] <= eps
    return int(qs[np.argmax(safe)]) if safe.any() else None


def public_holds(n: int, units: int, adv: int, eps: float,
                 uptime: float = 1.0) -> tuple[bool, int | None]:
    """Whether ``n`` publicly drawn units hold safety and liveness at ``eps``, with the quorum."""
    pmf = hyper_pmf(n, units, adv)
    q = _public_quorum(n, units, adv, eps, pmf)
    if q is None:
        return False, None
    a = np.arange(n + 1)
    short = stats.binom.cdf(q - 1, np.maximum(n - a, 0), uptime)       # online honest below Q
    return float(pmf @ short) <= eps, q


def public_draw(alpha: float, eps: float, units: int, uptime: float = 1.0,
                scan: int = SCAN) -> tuple[int, int] | None:
    """The fewest units ``n`` a round, with the quorum, of a public draw without replacement from
    ``units``; ``None`` if even every unit voting fails. Bisected, then scanned ``scan`` below for
    a smaller ``n`` that the quorum's lattice lets hold."""
    adv = coalition_units(alpha, units)

    def ok(n: int) -> bool:
        return public_holds(n, units, adv, eps, uptime)[0]

    if not ok(units):
        return None
    lo, hi = 0, units
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid
    for n in range(max(1, hi - scan), hi):
        if ok(n):
            hi = n
            break
    return hi, public_holds(hi, units, adv, eps, uptime)[1]


def _private_safety(q: int, p: float, adv: int, honest: int) -> float:
    """``P(H + 2A ≥ 2Q)`` for ``A ~ Bin(adv, p)`` and ``H ~ Bin(honest, p)``."""
    a = np.arange(adv + 1)
    return float(stats.binom.pmf(a, adv, p) @ stats.binom.sf(2 * q - 2 * a - 1, honest, p))


def private_holds(p: float, units: int, adv: int, eps: float,
                  uptime: float = 1.0) -> tuple[bool, int | None]:
    """Whether a private draw at chance ``p`` a unit holds both tails at ``eps``, with the
    smallest safe quorum."""
    honest = units - adv
    lo, hi = 0, units + 1                       # the safety tail falls as the quorum rises
    if _private_safety(hi, p, adv, honest) > eps:
        return False, None
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if _private_safety(mid, p, adv, honest) <= eps:
            hi = mid
        else:
            lo = mid
    live = float(stats.binom.cdf(hi - 1, honest, p * uptime))
    return live <= eps, hi


def private_draw(alpha: float, eps: float, units: int, uptime: float = 1.0,
                 tol: float = 0.25) -> tuple[float, int] | None:
    """The fewest expected seats ``pU`` a round, with the quorum, of a private draw over
    ``units`` counted units; ``None`` if even every unit voting fails. Bisected on ``p`` to
    ``tol`` seats."""
    adv = coalition_units(alpha, units)
    if not private_holds(1.0, units, adv, eps, uptime)[0]:
        return None
    lo, hi = 0.0, 1.0
    while (hi - lo) * units > tol:
        mid = (lo + hi) / 2
        if private_holds(mid, units, adv, eps, uptime)[0]:
            hi = mid
        else:
            lo = mid
    return hi * units, private_holds(hi, units, adv, eps, uptime)[1]


def every_unit(alpha: float, eps: float, units: int,
               uptime: float = 1.0) -> tuple[int, int] | None:
    """Every unit voting: the quorum ``Q = ⌊(U + A_U)/2⌋ + 1``, the least that two coalition-backed
    certificates cannot both reach, and whether the online honest units reach it at ``eps``."""
    adv = coalition_units(alpha, units)
    q = (units + adv) // 2 + 1
    if q > units - adv:
        return None
    live = float(stats.binom.cdf(q - 1, units - adv, uptime))
    return (units, q) if live <= eps else None


def every_unit_uptime(alpha: float, eps: float, units: int, tol: float = 1e-5) -> float:
    """The least honest uptime at which every unit voting holds; ``inf`` if none does."""
    if every_unit(alpha, eps, units, 1.0) is None:
        return math.inf
    lo, hi = 0.0, 1.0
    while hi - lo > tol:
        mid = (lo + hi) / 2
        if every_unit(alpha, eps, units, mid) is None:
            lo = mid
        else:
            hi = mid
    return hi


def every_unit_limit(alpha: float) -> float:
    """The least uptime in the limit of many units: ``q > (1 + a)/2`` and ``u(1 − a) ≥ q``."""
    return (1 + alpha) / (2 * (1 - alpha))


def unit_share(alpha: float, loss: float) -> float:
    """The coalition's share of the units when the honest stake loses ``loss`` of itself to
    rounding and the coalition loses none."""
    return alpha / (alpha + (1 - alpha) * (1 - loss))


def units_held(values: np.ndarray, unit: float) -> np.ndarray:
    """The whole units each note holds."""
    return np.floor(np.asarray(values, float) / unit * (1 + 1e-12)).astype(np.int64)


def registration_bytes() -> int:
    return sum(REGISTRATION_FIELDS.values())


def registrations_per_s(units: int, window_slots: float = SNAPSHOT_PHASE - K_OVER_F) -> float:
    """Registrations a second network-wide, every unit registered within the window: the
    snapshot phase after the snapshot is final."""
    return units / window_slots


def registered_rates(alpha: float, uptime: float) -> tuple[float, float]:
    """The wait bound's arguments when the lottery divides by the registered stake and a share
    ``uptime`` of the honest registered stake is online: the coalition's share of the online
    stake, and the online share of the registered stake, by which both rates scale."""
    online = alpha + (1 - alpha) * uptime
    return alpha / online, online


def inferred_rates(alpha: float, uptime: float) -> tuple[float, float]:
    """The same once the inference has corrected to the online stake: the rates are the full
    lottery's again."""
    return alpha / (alpha + (1 - alpha) * uptime), 1.0


def block_interval(scale: float, f: float = F) -> float:
    """The mean slots between won slots when the online stake is ``scale`` of the total the
    lottery divides by."""
    return 1 / (1 - (1 - f) ** scale)
