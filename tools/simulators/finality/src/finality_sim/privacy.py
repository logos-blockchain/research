"""Phases D5 and D1b: what votes leak, and what an opt-in public committee needs (PLAN.md D1b, D5).

**Votes as samples of stake (D5).** A seat is a lottery win as a block is. A holder of stake share
``s`` makes on average ``s·f`` blocks a slot and ``s·n`` votes a round of ``R`` slots, so an
observer who attributes a node's votes samples its stake ``1 + n/(R·f)`` times as fast: the
emission multiple of D0.

- **Time to identify and to size a holder.** The Blend report's linkability model
  (``tools/simulators/blend/src/blend/linkability.py``, loaded from the repository): each emission
  of a node with an adversarial peer is attributed to it with probability ``q``, and ``N``
  attributions estimate its stake to ``1/sqrt(N)``. Through Blend ``q = f_adv^hops`` for blocks and
  votes alike. A vote gossiped directly has no blend path, so ``q = 1``.
- **The specification's confidence.** ``analysis-cryptarchia-de-anonymisation-of-relative-stake.md``
  gives the probability that the naive estimator of a node's stake lands within ``±γ`` after ``T``
  slots of which a share ``q`` is observed (``spec_confidence``, transcribed), and splits a holder's
  stake until that probability falls below ``θ``. With votes, each observed round adds a Poisson
  count of mean ``n·α``; ``confidence`` adds its Fisher information to the slots'.

**The opt-in committee (D1b).** Volunteers vote with their declared stake, and a certificate needs
two thirds of the declared stake. An adversary holding ``α`` declares all of it. Honest holders
declare a share ``v`` of the honest stake, of which a share ``u`` is online. Two conflicting
certificates need the adversary to hold a third of the declared stake, and a certificate needs
the online honest stake to reach two thirds, so both hold when
``v ≥ 2α / ((1 − α)(3u − 2))``.
"""

from __future__ import annotations

import importlib.util
import math
import pathlib
from functools import lru_cache

import numpy as np
from scipy import stats

BLEND = (pathlib.Path(__file__).resolve().parents[3] / "blend" / "src" / "blend" / "linkability.py")


@lru_cache(maxsize=1)
def linkability():
    """The Blend report's ``blend.linkability``, loaded from the repository."""
    spec = importlib.util.spec_from_file_location("blend_linkability", BLEND)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def attribution_days(stake: float, n_obs: int, q_blocks: float, f: float = 1 / 30,
                     seats: float = 0.0, round_s: float = 1.0, q_votes: float = 0.0,
                     notes: float = math.inf, phases: int = 64) -> float:
    """Mean days until ``n_obs`` of a holder's blocks and votes are attributed to it.

    Blocks come at ``f`` a second network-wide, a share ``stake`` of them the holder's, each
    attributed with ``q_blocks``. Votes are cast together at the start of each round of
    ``round_s`` seconds: the holder's ``notes`` equal notes each win a seat with probability
    ``1 - exp(-seats·stake/notes)``, at most one a round, and each vote is attributed with
    ``q_votes``. The observer starts at a uniformly random point of a round. Without votes this
    is the Blend report's ``time_to_stake_seconds``.
    """
    rate = stake * q_blocks * f                         # attributed blocks per second
    if math.isinf(notes):
        batch = seats * stake * q_votes                 # attributed votes per round
    else:
        batch = notes * (1 - math.exp(-seats * stake / notes)) * q_votes
    if batch == 0.0:
        return linkability().time_to_stake_seconds(stake, q_blocks * f, n_obs, 1.0) / 86400
    mean_rate = rate + batch / round_s
    t_max = (n_obs + 12 * math.sqrt(n_obs) + 40) / mean_rate + 2 * round_s
    if t_max > 2000 * round_s:                         # many rounds: the batches average out
        return n_obs / mean_rate / 86400
    t = np.linspace(0.0, t_max, int(min(400_001, max(20_001, 40 * t_max / round_s))))
    phi = (np.arange(phases) + 0.5) / phases * round_s
    rounds = np.floor((t[None, :] - phi[:, None]) / round_s) + 1   # round starts by t
    survive = stats.poisson.cdf(n_obs - 1, rate * t[None, :] + batch * rounds)
    return float(np.trapezoid(survive, t, axis=1).mean()) / 86400


def spec_confidence(alpha: float, gamma: float, T: float, q: float, f: float) -> float:
    """``Prob2`` of the specification's analysis, with ``epsilon = dphi(alpha) * alpha * gamma``."""
    phi = 1 - (1 - f) ** alpha
    dphi = -((1 - f) ** alpha) * math.log(1 - f)
    epsilon = dphi * alpha * gamma
    sd = math.sqrt(phi * (1 - phi) / (T * q))
    numerator = -2.0 * math.erf(math.sqrt(2.0) * epsilon / (2 * sd))
    denominator = (-math.erf(phi * math.sqrt(2.0) / (2 * sd))
                   + math.erf(math.sqrt(2.0) * (phi - 1) / (2 * sd)))
    return numerator / denominator


def confidence(alpha: float, gamma: float, T: float, q_blocks: float, f: float,
               seats: float = 0.0, round_slots: float = 1.0, q_votes: float | None = None,
               notes: float = math.inf) -> float:
    """P(the estimate lies within ``±γ·α``) after ``T`` slots, from the exact Poisson count of the
    holder's attributed wins.

    The count has mean ``Λ(α) = T·q_blocks·φ(α) + (T/round_slots)·q_votes·v(α)``, where ``φ`` is
    the lottery function and ``v(α)`` the holder's expected votes a round (one at most per note,
    as in ``attribution_days``). The estimate solves ``Λ(α̂) = N``, so it lies within ``±γ``
    exactly when ``Λ(α(1 − γ)) ≤ N ≤ Λ(α(1 + γ))``. Rounds are attributed with ``q_votes``, by
    default ``q_blocks``.
    """
    qv = q_blocks if q_votes is None else q_votes

    def lam(a):
        votes = seats * a if math.isinf(notes) else notes * (1 - math.exp(-seats * a / notes))
        return T * q_blocks * (1 - (1 - f) ** a) + T / round_slots * qv * votes

    m = lam(alpha)
    hi, lo = math.floor(lam(alpha * (1 + gamma))), math.ceil(lam(alpha * (1 - gamma)))
    return float(stats.poisson.cdf(hi, m) - stats.poisson.cdf(lo - 1, m))


def split(alpha0: float, theta: float, conf) -> int:
    """The fewest equal nodes ``m`` with ``conf(alpha0 / m) <= theta`` (the specification's loop,
    without its cap of ten)."""
    if conf(alpha0) <= theta:
        return 1
    hi = 2
    while conf(alpha0 / hi) > theta:
        hi *= 2
    lo = hi // 2                                   # conf(alpha0 / lo) > theta
    while hi - lo > 1:
        mid = (lo + hi) // 2
        lo, hi = (mid, hi) if conf(alpha0 / mid) > theta else (lo, mid)
    return hi


def volunteer_share(alpha: float, uptime: float = 1.0) -> float:
    """The share of the honest stake that must declare, at least, for the committee to stay safe
    and live; ``inf`` when even all of it falls short (safety needs the adversary strictly below a
    third)."""
    if 3 * uptime - 2 <= 0:
        return math.inf
    v = 2 * alpha / ((1 - alpha) * (3 * uptime - 2))
    return v if v < 1 - 1e-12 else math.inf


def holders_needed(stakes: np.ndarray, share: float) -> int | None:
    """The fewest of the largest holders whose stake reaches ``share`` of the total; ``None`` when
    the share exceeds one."""
    if not share <= 1:
        return None
    s = np.sort(np.asarray(stakes, float))[::-1]
    cum = np.cumsum(s) / s.sum()
    return int(np.searchsorted(cum, share - 1e-12) + 1)
