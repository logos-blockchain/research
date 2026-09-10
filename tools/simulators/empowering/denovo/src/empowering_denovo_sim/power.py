"""What a mining node actually is, stated rather than assumed.

Every claim-rate figure in these studies rests on an assumption about how much silicon one
"node" commits, and that assumption was previously implicit and *inconsistent between the two
simulators*: `empowering_sim.elevation` seated nodes at a whole four-core Raspberry Pi 5
board while the de-novo engine seated them at one pinned core. A factor of four, in studies
whose numbers are compared against each other.

This module fixes the basis and makes the bracket explicit. The rates themselves follow the
config's `seconds_per_candidate_reward`, which since 2026-09 is the Mantle text's own
three-permutation attempt (prefix precomputed) rather than our measured naive candidate --
a board is 58,446 candidates a second on that basis, where the naive measurement gave
24,146. Every cross-class *ratio* below is unchanged by that rescaling, because the
permutation count cancels.

**The credibility problem with the synthetic field.** The studies draw hashrates from
``Pareto(1.16)`` floored at a Pi 5. The shape is not measured: 1.16 is the "80/20 rule" index
(`log 5 / log 4`), a folk constant from *wealth* distributions, applied here to hardware. That
is a leap. Wealth compounds; hardware is bought. Real mining populations are concentrated, but
by pooling and capital access rather than by the mechanism a Pareto describes, and no
measurement of a Logos mining population exists to fit against — the network has not launched.

So the synthetic draw is best read as *a* plausible spread rather than *the* expected one, and
anything that depends on its exact shape should be treated as indicative. What follows instead
are two bounds that do not depend on the shape at all:

* ``MINIMAL`` — one pinned core of a Raspberry Pi 5. The least a participant can commit and
  still be mining: a spare core on a board bought for something else. This is the "barely
  profitable" end, and at the bootstrap difficulty floor it is profitable at any plausible
  token price, so it is a floor on commitment rather than on viability.
* ``WORST`` — every core of the most efficient hardware measured, at full duty. This is the
  adversarial assumption: an attacker buys the best available and runs it flat out.

**Where the GPU sits, now that it is estimated.** The worst case here is the best *measured*
class. `powcost.rates` now also carries an ESTIMATED `gpurig` rate for `poseidon2_reward`
(``measured=False``), derived from published BN254 field-multiplication throughput, and it
splits the old blanket caveat rather than confirming it:

* **Cost-bounded attacks are not understated.** On the naive-candidate basis both were
  stated on, a card spends about 1.54e-3 J per candidate against a Pi 5 board's measured
  3.65e-4 -- roughly **four times worse per joule** -- and the ratio survives the
  three-permutation rescaling, which divides both sides alike. Anything priced per
  candidate, the sybil flood included, is unaffected by GPUs.
* **Share-bounded attacks are understated.** A card is about twelve times a board in raw rate
  and a six-card rig about 73x, so an attacker buying hashrate *share* -- the whale -- reaches
  a given share far faster than a Pi 5 field suggests.

Poseidon2 over BN254 rather than over a small field is itself a GPU-resistance decision, and
it is doing that work whether or not it was chosen for it. The GPU figure is an estimate and
should be replaced by `make poseidon2` on a CUDA host before anything rests on it.
"""
from __future__ import annotations

from dataclasses import dataclass

from empowering_sim.config import Config

PI5_CORES = 4                     # protocol-snapshot.toml, [work] pi5_cores

# powcost.rates TABLE[("poseidon2_reward", "apple")]: measured on an M4 Pro performance core,
# release build with link-time optimisation, over ten usable performance cores. That
# measurement is of the naive candidate; the adversarial basis must match the config's
# three-permutation attempt (an attacker precomputes at least as well as the honest field),
# so it is scaled by the same permutation-count factor the Pi 5 basis uses. DERIVED, not
# measured -- re-measure with the precomputed-prefix miner alongside the Pi 5 re-run.
APPLE_NAIVE_SECONDS_PER_CANDIDATE = 26.6e-6
APPLE_SECONDS_PER_CANDIDATE = APPLE_NAIVE_SECONDS_PER_CANDIDATE * (68.439 / 165.658)
APPLE_CORES = 10


@dataclass(frozen=True)
class PowerBasis:
    """One node's committed search rate, and where the figure comes from."""

    key: str
    candidates_per_second: float
    note: str


def minimal(cfg: Config) -> PowerBasis:
    """One pinned core of a Pi 5 — the least commitment that is still mining."""
    return PowerBasis("minimal-1-core", 1.0 / cfg.seconds_per_candidate_reward,
                      "one pinned core of a Raspberry Pi 5, measured")


def board(cfg: Config) -> PowerBasis:
    """A whole Pi 5, all cores, full duty — the honest default for a committed miner.

    This is what `empowering_sim.elevation` has always used, so it is also the basis that
    makes the de-novo figures comparable with the strategy study's.
    """
    return PowerBasis("board-4-core", PI5_CORES / cfg.seconds_per_candidate_reward,
                      "all four cores of a Raspberry Pi 5, measured, at full duty")


def worst(cfg: Config) -> PowerBasis:
    """The adversarial assumption: the best measured hardware, every core, full duty.

    Built from the Apple class's own **measured** Poseidon2 rate, not from a stand-in. Until
    2026-08-20 this multiplied the Pi 5 board rate by 3.45 -- the Apple class's cost advantage
    per candidate (2.025e-11 against 5.864e-12 USD) -- which is an energy ratio applied to a
    rate, a category error that also understated the bracket 4.5-fold. The rate ratio is
    directly available: `powcost.rates` carries the M4 Pro at 26.6 microseconds per candidate,
    measured, over ten performance cores.
    """
    rate = APPLE_CORES / APPLE_SECONDS_PER_CANDIDATE
    return PowerBasis("worst-measured", rate,
                      f"best measured class, all cores, full duty -- "
                      f"{rate / (PI5_CORES / cfg.seconds_per_candidate_reward):.1f}x a Pi 5 "
                      f"board, from the measured rate rather than a cost ratio")


def homogeneous(basis: PowerBasis):
    """A draw with no distributional assumption at all: every node identical.

    Used for the adversarial bounds, where a synthetic spread would only add unexamined
    variance to a number meant to bracket rather than to predict.
    """
    import numpy as np

    def draw(n: int) -> np.ndarray:
        return np.full(n, basis.candidates_per_second, dtype=float)
    return draw
