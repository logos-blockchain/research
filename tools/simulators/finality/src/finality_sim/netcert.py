"""Phase L: certificates signed by Blend's declared nodes, in closed form (PLAN.md Phase L).

**The quorum (L.0).** A certificate needs links carrying a share ``q`` of the declared weight. The
coalition holds a share ``a`` of it and signs on every side. The honest declarations, ``1 − a``,
vote one link each, and a share ``u`` of them is online.

- *Safety.* Two conflicting links need ``h_1 + a ≥ q`` and ``h_2 + a ≥ q`` with
  ``h_1 + h_2 ≤ 1 − a``, which some split of the honest votes meets exactly when ``a ≥ 2q − 1``.
  Casper FFG's accountable safety is this count: two conflicting finalized checkpoints need
  ``2q − 1`` of the weight to have signed both.
- *Liveness.* A link carries ``q`` from the honest votes alone once ``u(1 − a) ≥ q``.

**The declared set (L.1).** A coalition holding ``α`` of the active stake ``D`` can lock all of it
in service notes, which "can still participate in Proof of Stake", and a note backs at most one
declaration per service (Mantle, Service notes). Honest declarations lock ``L_h`` in all.

- *One weight per declaration.* The coalition splits its stake into notes of the minimum stake
  ``m`` and holds ``⌊αD/m⌋`` declarations. Honest declarations lock ``m`` each, so there are
  ``L_h/m`` of them.
- *Weight by value.* The coalition weighs ``αD`` and the honest declarations ``L_h``, however
  either splits its notes.

Either way ``a = αD / (αD + L_h)``, up to the floor, and the honest declared stake ``L_h`` the
quorum needs follows from the two conditions. With weight by value and the honest declarations a
share ``v`` of the honest stake, ``L_h = v(1 − α)D``, which is D1b's opt-in committee
(``privacy.volunteer_share``).

**Partitions (L.3).** The coalition signs on both sides. A side whose honest declarations hold
``h`` of the declared weight certifies once ``u·h + a ≥ q``. Both sides of a split can do so only
when ``a ≥ 2q − 1``, the safety condition above.

**Cost (L.5).** ``n`` declarations vote once a round of ``R`` slots, so a node verifies ``n/R``
votes a second, and a certificate carries ``⌈q·n⌉`` signatures.
"""

from __future__ import annotations

import json
import math
import pathlib

# The repository's reference-grade signature benchmark on a Raspberry Pi 5 (reports/pqc).
PI5 = (pathlib.Path(__file__).resolve().parents[5] / "reports" / "pqc" / "results"
       / "rasberrypi5-20260811T211615Z.json")

Q = 2 / 3                      # the quorum, as Casper FFG's supermajority
SUPPLY = 100_000_000            # the minimum-stake analysis' S_TGE = S_max, in LGO
MIN_STAKE_SHARE = 1e-5          # its minimum stake, 0.001 % of S_TGE
CAP_SHARE = 0.15 / 1000         # its cap, r_stake · S_TGE / N_stakers: 15 % over 1,000 nodes
STAKED_SHARE = 0.30             # the block rewards' target of the supply staked
SMALL_NETWORK = 1000            # the analysis' "network size that is considered small"


def analysis_min_stake(supply: float = SUPPLY, share: float = MIN_STAKE_SHARE) -> float:
    """The analysis' minimum stake in LGO, ``0.001 % · S_TGE``."""
    return share * supply


def analysis_cap(supply: float = SUPPLY, r_stake: float = 0.15,
                 n_stakers: int = SMALL_NETWORK) -> float:
    """The analysis' cap on the minimum stake, ``r_stake · S_TGE / N_stakers``, in LGO."""
    return r_stake * supply / n_stakers


def coalition_declarations(alpha: float, min_stake: float, active: float = 1.0) -> int:
    """The most declarations a coalition holding ``alpha`` of the active stake can back, one note
    of at least ``min_stake`` each."""
    return int(math.floor(alpha * active / min_stake + 1e-9))


def coalition_share(alpha: float, honest_locked: float, min_stake: float | None = None,
                    active: float = 1.0) -> float:
    """The coalition's share ``a`` of the declared weight. With ``min_stake``, one weight per
    declaration, the honest declarations locking ``min_stake`` each; without, weight by value."""
    if min_stake is None:
        c = alpha * active
        return c / (c + honest_locked)
    c = coalition_declarations(alpha, min_stake, active)
    h = honest_locked / min_stake
    return c / (c + h)


def safe(a: float, q: float = Q) -> bool:
    """No split of the honest votes lets two conflicting links both carry ``q``."""
    return a < 2 * q - 1


def live(a: float, uptime: float = 1.0, q: float = Q) -> bool:
    """The honest declarations online carry ``q`` on their own."""
    return uptime * (1 - a) >= q - 1e-12


def holds(a: float, uptime: float = 1.0, q: float = Q) -> bool:
    return safe(a, q) and live(a, uptime, q)


def largest_share_held(uptime: float = 1.0, q: float = Q) -> float:
    """The largest coalition share of the declared weight that keeps both conditions: below
    ``2q − 1`` for safety, at most ``1 − q/u`` for liveness."""
    return min(2 * q - 1, 1 - q / uptime) if uptime > 0 else -math.inf


def honest_locked_needed(alpha: float, uptime: float = 1.0, q: float = Q) -> float:
    """The least honest declared stake, as a share of the active stake, that holds a coalition of
    ``alpha``: ``a = α/(α + x)`` must stay within ``largest_share_held``. ``inf`` when even the
    whole honest stake falls short, or when no share is held."""
    a_max = largest_share_held(uptime, q)
    if a_max <= 0:
        return math.inf
    x = alpha * (1 - a_max) / a_max
    return x if x < (1 - alpha) - 1e-12 else math.inf


def largest_alpha_held(honest_locked: float, uptime: float = 1.0, q: float = Q) -> float:
    """The largest coalition stake share, of the active stake, that honest declarations locking
    ``honest_locked`` of it hold, with weight by value or at whole declarations of the minimum
    stake: ``α/(α + x) ≤ a_max``."""
    a_max = largest_share_held(uptime, q)
    if a_max <= 0:
        return 0.0
    return honest_locked * a_max / (1 - a_max)


def side_certifies(h_side: float, a: float, uptime: float = 1.0, q: float = Q) -> bool:
    """A side whose honest declarations hold ``h_side`` of the declared weight, with the
    coalition's ``a`` signing on it too, reaches the quorum."""
    return uptime * h_side + a >= q - 1e-12


def side_share_needed(a: float, uptime: float = 1.0, q: float = Q) -> float:
    """The share of the honest declared weight a side needs to certify, ``(q − a)/(u(1 − a))``."""
    return max(q - a, 0.0) / (uptime * (1 - a))


def both_sides_certify(a: float, q: float = Q) -> bool:
    """Some split of the honest declarations lets both sides certify: an even split at full
    uptime is the best the coalition can find."""
    h = (1 - a) / 2
    return side_certifies(h, a, 1.0, q)


def pi5_signature(alg: str, implementation: str, path: pathlib.Path = PI5) -> tuple[float, int]:
    """The median verification time, in nanoseconds on one core, and the signature's size in
    bytes, as the repository measured them on a Raspberry Pi 5."""
    data = json.loads(path.read_text())
    for it in data["sig"]:
        if it["alg"] == alg and it["implementation"] == implementation:
            return float(it["operations"]["verify"]["median"]), int(it["sizes"]["signature"])
    raise KeyError((alg, implementation))


def verify_core_share(n: int, round_slots: float, verify_ns: float) -> float:
    """The share of one core that verifying ``n`` votes a round of ``round_slots`` one-second
    slots takes, at ``verify_ns`` nanoseconds a verification."""
    return n / round_slots * verify_ns * 1e-9


VOTE_FIELDS = {"source block": 32, "source round": 8, "target block": 32, "target round": 8,
               "declaration index": 4}


def vote_bytes(signature: int) -> int:
    """A vote: the link's two checkpoints, the signer's index in the registry, a signature."""
    return sum(VOTE_FIELDS.values()) + signature


def certificate_bytes(n: int, signature: int, q: float = Q) -> int:
    """A certificate of separate signatures: ``⌈q·n⌉`` signatures, each with its signer's index,
    and the link once."""
    k = math.ceil(q * n - 1e-9)
    link = sum(v for f, v in VOTE_FIELDS.items() if f != "declaration index")
    return link + k * (signature + VOTE_FIELDS["declaration index"])
