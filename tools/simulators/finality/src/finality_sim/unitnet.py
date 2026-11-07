"""What carries the votes of counted units, and what they reveal (UNITS.md N.3, N.4, N.6).

**Blend's load (N.3).** Blend relays every message to all core nodes at every layer, so a core
connection carries ``F_1`` messages a round, every message of the network once for each of its
layers, and every node verifies the header of each (``blend-protocol.md`` at ``bd1ca2c8``, Relaying
and Expected Traffic). Today ``F_1 = 16`` (``committee.blend_load``). Votes add ``h`` messages a
connection for each vote message at ``h`` layers, whatever finally receives the payload. The
specification sizes the rest from ``F_1``: the read limit keeps a backlog draining,
``F_1 = r_1·(1 − 1/(Δ_max + η))``, and the slowest node verifies ``V`` messages a second with
``r_1 = ⌊(2V/3)/(Φ_CC + 1)⌋``. A node receives each message once from each of its ``Φ_CC``
neighbors, at 19,318 bytes a message.

- *One vote a message*, as Blend carries a block proposal: ``n/R`` vote messages a second for ``n``
  units a round of ``R`` seconds. A node's count of messages grows with its drawn units.
- *A vote schedule*: every core node sends exactly ``max(1, ⌈k/k_max⌉)`` vote messages a round for
  its ``k`` drawn units, empty when it has none, so a node holding at most ``k_max`` units always
  sends one and its count says nothing of its stake.
- *Point to point*, described only: each message crosses ``h`` links in all.

**What votes reveal (N.4).** D5's model: a node's message is attributed to it with ``q = f_adv^h``.
An attributed message that carries one unit's vote is one observation of the stake, as a block is.
An attributed message of the schedule reveals how many units it carries, ``k``, a draw from the
node's ``u`` units, worth ``c = E[k]²/Var[k]`` observations: ``Var[k]`` is hypergeometric for a
public draw and binomial for a private one, and nothing for every unit voting, which an attributed
message then sizes exactly. A holder is sized to ±10 % at 100 observations, as in M.3.

- *Unlinkable votes* carry a tag from the unit's secret and the round, so nothing ties a unit's
  votes across rounds.
- *Linkable keys*, one key a unit signing every vote of the epoch, allow one aggregate signature a
  round. With one vote a message, a unit is tied to its node once any of its messages in the
  epoch is attributed, and the tied units of an epoch are a binomial draw. In the schedule, one
  attributed message ties the node's messages for the rest of the epoch, every later message
  carrying one of its known units, so the stake is known by the epoch's end.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats

from finality_sim import committee as cm

# Blend at logos-lips bd1ca2c8 (blend-protocol.md, Global Parameters, Expected Traffic, Message
# Formatting): the peering degree, the slowest node's verifications a second and the 157 measured
# on one core of a Raspberry Pi 5, the maximal delay and one hop's absorption in rounds of one
# second, a message's bytes and the payload it carries.
PHI_CC, V, V_PI5 = 4, 156, 157
DELTA_MAX, ETA = 3, 2
MESSAGE_BYTES, MAX_PAYLOAD = 19_318, 18_195
TODAY_F1 = cm.blend_load(0.0)[0]

# A unit's vote: its tag and its RLN share, the share's abscissa being the hash of the signal. A
# message adds the block and the round once, and a Groth16 proof, 128 bytes, a unit or a message.
UNIT_VOTE = {"tag": 32, "share": 32}
MESSAGE_FIELDS = {"block": 32, "round": 8}
PROOF = 128


def read_limit(v: float) -> int:
    """``r_1 = ⌊(2V/3)/(Φ_CC + 1)⌋``."""
    return math.floor((2 * v / 3) / (PHI_CC + 1) + 1e-9)


def node_budget(r1: int) -> int:
    """The least ``V`` whose read limit is at least ``r1``."""
    return math.ceil(1.5 * (PHI_CC + 1) * r1 - 1e-9)


def needed_read_limit(f1: float) -> int:
    """The least read limit at which a backlog of ``F_1`` drains as the specification sizes it,
    ``F_1 ≤ r_1·(1 − 1/(Δ_max + η))``."""
    return math.ceil(f1 / (1 - 1 / (DELTA_MAX + ETA)) - 1e-9)


def connection_load(vote_messages_per_s: float, layers: int) -> float:
    """``F_1`` with the vote messages added at ``layers`` layers each."""
    return TODAY_F1 + layers * vote_messages_per_s


def k_max(per_unit_proof: bool) -> int:
    """The most units' votes one message's payload carries."""
    unit = sum(UNIT_VOTE.values()) + (PROOF if per_unit_proof else 0)
    fixed = sum(MESSAGE_FIELDS.values()) + (0 if per_unit_proof else PROOF)
    return (MAX_PAYLOAD - fixed) // unit


def schedule_messages(drawn: np.ndarray, kmax: int) -> np.ndarray:
    """The vote messages each node sends in a round for its drawn units."""
    return np.maximum(1, -(-np.asarray(drawn) // kmax))


def count_ceiling(kmax: int, n: int, units: int, eps: float) -> int:
    """The most units a node may hold for its drawn units, a public draw of ``n`` of ``units``,
    to exceed ``kmax`` with chance at most ``eps`` a round: up to it the node sends one message a
    round. With every unit drawn it is ``kmax``."""
    def tail(held: int) -> float:
        return float(stats.hypergeom.sf(kmax, units, held, n))

    lo, hi = kmax, units
    if tail(hi) <= eps:
        return hi
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if tail(mid) <= eps:
            lo = mid
        else:
            hi = mid
    return lo


def load(vote_messages_per_s: float, proofs_per_s: float, layers: int) -> dict:
    """What the votes cost a core node: its verifications a second, headers and proofs, the share
    of one Pi 5 core they take, the read limit and the node budget Blend's rules then need, and
    the bytes it receives a second."""
    f1 = connection_load(vote_messages_per_s, layers)
    r1 = needed_read_limit(f1)
    v = node_budget(r1)
    added = layers * vote_messages_per_s + proofs_per_s
    return dict(f1=f1, r1=r1, v=v, v_cores=v / V_PI5, added=added, added_cores=added / V_PI5,
                verifications=f1 + proofs_per_s, cores=(f1 + proofs_per_s) / V_PI5,
                received_mb=PHI_CC * f1 * MESSAGE_BYTES / 1e6)


def info_public(units_held: float, n: int, units: int) -> float:
    """Observations an attributed message of the schedule is worth under a public draw of ``n``
    of ``units``: ``E[k]²/Var[k]`` for ``k`` hypergeometric; ``inf`` when every unit is drawn."""
    p = units_held / units
    mean = n * p
    var = n * p * (1 - p) * (units - n) / (units - 1)
    return math.inf if var <= 0 else mean * mean / var


def info_private(units_held: float, chance: float) -> float:
    """The same under a private draw, each unit a seat with ``chance``: ``k`` binomial."""
    return math.inf if chance >= 1 else units_held * chance / (1 - chance)


def size_days(n_obs: float, rate_unit: float, rate_msg: float = 0.0, info: float = 1.0,
              epoch_s: float = math.inf, epoch_info: float = 0.0, epoch_exact: float = 0.0,
              points: int = 40_001) -> float:
    """Mean days until a holder's observations reach ``n_obs``.

    Single observations, blocks and one-vote messages, arrive as a Poisson process at
    ``rate_unit`` a second. Attributed messages of the schedule arrive at ``rate_msg`` a second,
    each worth ``info`` observations. With linkable keys, each epoch's end adds ``epoch_info``
    observations (one vote a message), or, with chance ``epoch_exact``, sizes the holder outright
    (the schedule)."""
    if math.isinf(info):
        info = n_obs                                     # one attributed message sizes it
    # each source's mean time alone, with the events it needs; the slowest tail past the fastest
    # source's mean bounds the horizon, as the holder is sized no later than by that source
    scales = []
    if rate_unit > 0:
        scales.append((n_obs / rate_unit, n_obs))
    if rate_msg > 0:
        scales.append((n_obs / (info * rate_msg), max(n_obs / info, 1.0)))
    if math.isfinite(epoch_s) and epoch_info > 0:
        scales.append((n_obs / epoch_info * epoch_s, max(n_obs / epoch_info, 1.0)))
    if math.isfinite(epoch_s) and epoch_exact > 0:
        scales.append((epoch_s / epoch_exact, 1.0))
    t_mean, k = min(scales)
    t_max = t_mean * (2 + 15 / math.sqrt(k) + 50 / k)
    t = np.linspace(0.0, t_max, points)
    have = np.zeros_like(t)
    if math.isfinite(epoch_s) and epoch_info > 0:
        have = epoch_info * np.floor(t / epoch_s)
    m_max = int(math.ceil(n_obs / info)) if rate_msg > 0 else 0
    survive = np.zeros_like(t)
    for m in range(m_max + 1):
        left = np.ceil(n_obs - info * m - have)          # single observations still needed
        p_m = stats.poisson.pmf(m, rate_msg * t) if rate_msg > 0 else 1.0
        survive += p_m * np.where(left > 0, stats.poisson.cdf(left - 1, rate_unit * t), 0.0)
    if math.isfinite(epoch_s) and epoch_exact > 0:
        survive *= (1 - epoch_exact) ** np.floor(t / epoch_s)
    return float(np.trapezoid(survive, t)) / 86400


def tie_chance(messages: float, q: float) -> float:
    """The chance that at least one of ``messages`` messages is attributed."""
    return -math.expm1(messages * math.log1p(-q))


def delivery_bound(d6_p95: float, layers: int) -> float:
    """The delivery at ``layers`` layers: D6's at the specification's three, and at most
    ``Δ_max`` rounds for each further layer."""
    return d6_p95 + max(layers - 3, 0) * DELTA_MAX
