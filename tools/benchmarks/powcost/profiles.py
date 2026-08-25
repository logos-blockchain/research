"""Device profiles: what a class of machine draws, and on what basis it was measured.

**The basis is the whole problem.** A Raspberry Pi's published figures are whole-board and
measured at the AC wall, so they already contain the DRAM, the southbridge and the adapter's
conversion loss. A desktop processor's are CPU package power read from an on-die counter,
which contains none of those. A graphics card's are board power for the card alone. Those
three numbers are not comparable, and subtracting an idle figure taken on one basis from a
busy figure taken on another produces nonsense -- for the Apple bucket below it produces a
*negative* marginal draw, which is how this was noticed.

So every figure carries its basis, and the kernel refuses to combine figures across bases
rather than quietly returning a number. The model's headline output is a ratio between device
classes, so a systematic basis error does not cancel: it goes straight into the answer.

Provenance is carried per figure, not per profile, because within one bucket a measured
all-core draw commonly sits beside an estimated single-core one -- nobody publishes
single-core board power for a Pi 5.

Sourced 2026-08-16 by a research pass with an adversarial audit. **Two of the four buckets
were audited; the Pi 5 and Intel audits did not run.** Those two carry ``audited=False`` and
should be read as first-pass research, not as verified figures.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Basis(str, Enum):
    """What a wattage is measured across. Figures may only be combined within one basis."""

    WALL = "wall"          # whole machine, AC side: includes platform and supply losses
    PLATFORM = "platform"  # whole machine, DC side: includes board, memory, storage
    PACKAGE = "package"    # the processor package alone, DC side
    CARD = "card"          # one accelerator board, DC side
    RIG = "rig"            # a multi-accelerator chassis, DC side, cards only


class Provenance(str, Enum):
    MEASURED = "measured"      # an instrumented reading, cited
    VENDOR = "vendor"          # a rating or limit the vendor publishes -- NOT a draw
    ESTIMATED = "estimated"    # derived or judged; no source measures this


@dataclass(frozen=True)
class Figure:
    """One wattage, with everything needed to know whether it may be used."""

    watts: float
    basis: Basis
    provenance: Provenance
    source: str = ""
    note: str = ""

    @property
    def is_draw(self) -> bool:
        """A vendor rating is a cooling or supply specification, never a power draw."""
        return self.provenance is not Provenance.VENDOR


@dataclass(frozen=True)
class Profile:
    """One device bucket."""

    key: str
    label: str
    part: str
    cores: int
    rated: Figure
    idle: Figure
    busy_one_core: Figure
    busy_all_cores: Figure
    platform_watts: float
    psu_efficiency: float
    utilization: float
    audited: bool
    caveats: tuple[str, ...] = field(default_factory=tuple)

    def marginal_watts_per_core(self) -> tuple[float | None, str]:
        """Draw a single busy core adds above idle. The honest-user basis.

        Returns ``(watts, why)``; ``watts`` is None when the figures cannot be combined,
        with ``why`` naming the obstruction. A caller that wants a number regardless must
        supply the missing measurement, not relax the check.
        """
        if not (self.idle.is_draw and self.busy_one_core.is_draw):
            return None, "one of the figures is a vendor rating, not a draw"
        if self.idle.basis is not self.busy_one_core.basis:
            return None, (f"basis mismatch: idle is {self.idle.basis.value}, "
                          f"one-core busy is {self.busy_one_core.basis.value}")
        delta = self.busy_one_core.watts - self.idle.watts
        if delta <= 0:
            return None, f"non-positive marginal ({delta:.2f} W) -- the figures disagree"
        return delta, f"{self.idle.basis.value} basis"

    def total_watts_all_cores(self) -> tuple[float | None, str]:
        """Whole-platform draw at the wall with every core loaded. The miner/attacker basis."""
        busy = self.busy_all_cores
        if not busy.is_draw:
            return None, "the all-core figure is a vendor rating, not a draw"
        if busy.basis is Basis.WALL:
            # Already at the wall: platform and supply losses are inside the number.
            return busy.watts, "wall basis, platform and supply already included"
        dc = busy.watts + self.platform_watts
        return dc / self.psu_efficiency, f"{busy.basis.value} basis, platform and supply added"

    def workload_watts(self) -> float:
        """What our puzzle is expected to draw with every core loaded, DC side.

        A thermal rating times a utilization fraction. This is the fallback where a measured
        all-core draw under a comparable workload is missing, and it is the least trustworthy
        number in the profile -- the utilization fraction is a judgement in every bucket.
        """
        return self.rated.watts * self.utilization


# --------------------------------------------------------------------------- the buckets

RPI5 = Profile(
    key="rpi5",
    label="Raspberry Pi 5",
    part="Raspberry Pi 5 Model B, Broadcom BCM2712, 4x Cortex-A76 at 2.4 GHz",
    cores=4,
    rated=Figure(27.0, Basis.WALL, Provenance.VENDOR,
                 "raspberrypi.com 27 W USB-C PD supply; product brief specifies 5 V/5 A input",
                 "A SUPPLY CEILING, NOT A DRAW. The board has no thermal design point. "
                 "Measured all-core draw is about a third of this."),
    idle=Figure(2.8, Basis.WALL, Provenance.MEASURED,
                "geerlingguy/sbc-reviews#21, 8 GB board, official supply",
                "Corroborated 2.6-3.6 W across Tom's Hardware, CNX Software and raspberry.tips."),
    busy_one_core=Figure(4.5, Basis.WALL, Provenance.ESTIMATED, "",
                         "NO PUBLISHED MEASUREMENT EXISTS with exactly one core loaded. "
                         "Derived as idle plus ~40% of the idle-to-all-core delta, because "
                         "the first busy core pays the whole DVFS step. Range 4.0-5.0 W."),
    busy_all_cores=Figure(8.8, Basis.WALL, Provenance.MEASURED,
                          "CNX Software, wall meter, 'stress -c 4'",
                          "Published spread 6.8-9.7 W depending on governor, cooling and "
                          "stressor. Linpack's 13.8 W is vector-saturating and NOT our case."),
    platform_watts=0.0,      # already inside the wall figures; adding again double-counts
    psu_efficiency=1.0,      # likewise: the adapter loss is already inside them
    utilization=0.28,
    audited=False,
    caveats=(
        "NOT AUDITED -- the adversarial pass for this bucket did not run.",
        "Every figure is whole-board at the AC wall. Comparing them against a package-power "
        "bucket without normalising overstates the Pi and understates the desktop. DC-side "
        "board equivalents are about 2.4 W idle and 7.5 W all-core, at ~0.85 adapter "
        "efficiency.",
        "THERMAL THROTTLING DOMINATES SUSTAINED LOAD, which is the case proof-of-work mining "
        "actually is. An uncooled board reaches 80 C in minutes and hard-throttles 2.4 GHz to "
        "1.5 GHz at 85 C. Draw falls to ~7 W while the clock falls ~38%, so energy per "
        "candidate gets WORSE. Active cooling is effectively mandatory for any sustained "
        "figure here to be valid.",
        "The single-core figure is unsourced and estimated; it is the weakest number in the "
        "bucket and it is the one the honest-user basis depends on.",
    ),
)

APPLE = Profile(
    key="apple",
    label="Apple M3/M4 Mac",
    part="Apple M4 Pro, 14-core, 10 performance and 4 efficiency cores",
    cores=14,
    rated=Figure(46.0, Basis.PACKAGE, Provenance.VENDOR, "Notebookcheck sustained package limit",
                 "Apple publishes no thermal design point; this is an observed sustained "
                 "ceiling, so treat it as a limit rather than a specification."),
    idle=Figure(4.3, Basis.WALL, Provenance.MEASURED, "whole-machine idle",
                "WALL basis, so it includes the display and the platform. It cannot be "
                "subtracted from the package-basis busy figures below -- doing so is what "
                "surfaced the basis problem."),
    busy_one_core=Figure(3.0, Basis.PACKAGE, Provenance.MEASURED,
                         "eclecticlight.co (Howard Oakley), powermetrics, one performance core",
                         "Package power for a single loaded performance core."),
    busy_all_cores=Figure(32.0, Basis.PACKAGE, Provenance.MEASURED,
                          "eclecticlight.co, 10 performance cores at ~3.85 GHz",
                          "AUDIT FOUND: this is a NEON VECTOR figure, measured on tight vector "
                          "loops. Our puzzle is scalar integer and field arithmetic, so this "
                          "OVERSTATES it. The audited correction is to treat 32 W as an upper "
                          "bound, not the expected draw."),
    platform_watts=18.0,
    psu_efficiency=0.90,
    utilization=0.65,
    audited=True,
    caveats=(
        "Audited. The all-core figure was found to be a NEON vector measurement presented as "
        "a general one, and overstates a scalar integer workload.",
        "Idle is wall basis while the busy figures are package basis, so no marginal draw can "
        "be computed for this bucket until a package-basis idle reading exists. A "
        "powermetrics run on the target machine supplies it in one command.",
        "Efficiency cores and performance cores differ several-fold in draw. Only the "
        "performance-core figure is relevant, since a miner pins to those.",
    ),
)

INTEL = Profile(
    key="intel",
    label="Intel PC",
    part="Intel Core Ultra 9 285HX, Arrow Lake-HX, 8 P-cores and 16 E-cores",
    cores=24,
    rated=Figure(160.0, Basis.PACKAGE, Provenance.VENDOR,
                 "Intel ARK, maximum turbo power for the 285HX",
                 "A POWER LIMIT, NOT A DRAW, and one that can be sustained for minutes. "
                 "Base power is far lower."),
    idle=Figure(6.0, Basis.PACKAGE, Provenance.ESTIMATED, "",
                "Estimated package idle. Unsourced."),
    busy_one_core=Figure(25.0, Basis.PACKAGE, Provenance.ESTIMATED, "",
                         "Estimated. A single loaded P-core at high boost carries a large "
                         "share of the uncore step, which is why this is not a twenty-fourth "
                         "of the all-core figure."),
    busy_all_cores=Figure(100.0, Basis.PACKAGE, Provenance.MEASURED,
                          "Notebookcheck sustained multi-core package power",
                          "Sustained rather than peak; the part exceeds this transiently."),
    platform_watts=25.0,
    psu_efficiency=0.88,
    utilization=0.65,
    audited=False,
    caveats=(
        "NOT AUDITED -- the adversarial pass for this bucket did not run.",
        "Both the idle and single-core figures are unsourced estimates, so the marginal draw "
        "this bucket reports rests on two judgements and no measurement. A RAPL reading on "
        "the benchmark machine replaces both.",
        "This is the exact part in the Equi-X benchmark set, so its throughput is measured "
        "even though its power is not -- the reverse of the Apple bucket's position.",
    ),
)

GPU_RIG = Profile(
    key="gpurig",
    label="GPU rig",
    part="6x NVIDIA GeForce RTX 5090 in an open-frame chassis",
    cores=6,                 # accelerators, not CPU cores
    rated=Figure(575.0, Basis.CARD, Provenance.VENDOR, "NVIDIA board power for the RTX 5090",
                 "A BOARD POWER LIMIT set against a graphics worst case, NOT a draw. The "
                 "1000 W figure on the same page is a supply recommendation and is further "
                 "still from being a draw."),
    idle=Figure(30.0, Basis.CARD, Provenance.MEASURED, "Igor's Lab / GamersNexus, per card",
                "Per card. Sources spread 29-46 W; near-irrelevant at mining duty cycles."),
    busy_one_core=Figure(362.0, Basis.CARD, Provenance.ESTIMATED, "",
                         "AUDIT-CORRECTED from 415 W. The original pinned utilization at 0.72 "
                         "against an OctaneBench render, which engages ray-tracing and wide "
                         "vector units our kernel does not touch. Same-part mining "
                         "measurements land at 50-63% of the rating."),
    busy_all_cores=Figure(2172.0, Basis.RIG, Provenance.ESTIMATED, "",
                          "Six cards at the corrected per-card figure. RIG basis: cards only, "
                          "excluding the host and supply losses."),
    platform_watts=150.0,
    psu_efficiency=0.905,
    utilization=0.63,
    audited=True,
    caveats=(
        "Audited, and the audit found real errors: supply efficiency applied twice in the "
        "wall-power derivation, a cited mining figure that the source does not support, and a "
        "utilization fraction sitting above every same-part measurement. The corrections are "
        "applied above; utilization moved 0.72 to 0.63 and the per-card busy draw 415 W to "
        "362 W.",
        "NO LAB MEASUREMENT OF THIS PUZZLE ON THIS HARDWARE EXISTS. Nobody has published "
        "Poseidon2 over BN254, or any zero-knowledge prover kernel, instrumented on a 4090 or "
        "5090. This is the largest single gap in the table.",
        "The card count is a design choice, not a measurement, and the rig figures move "
        "linearly in it. Practical builds run four to eight cards.",
        "Transient spikes reach 900 W for under a millisecond. Those size the supply and the "
        "breaker; they contribute nothing to an energy integral and must not be used here.",
    ),
)

BUCKETS: dict[str, Profile] = {p.key: p for p in (RPI5, APPLE, INTEL, GPU_RIG)}


def coverage() -> list[dict]:
    """What is measured, what is estimated, and what was never audited.

    Printed rather than assumed. A table where half the load-bearing figures are judgements
    is usable, but only if that is visible at the point of use.
    """
    rows = []
    for p in BUCKETS.values():
        figs = dict(rated=p.rated, idle=p.idle, one_core=p.busy_one_core,
                    all_cores=p.busy_all_cores)
        marginal, why = p.marginal_watts_per_core()
        rows.append(dict(
            bucket=p.key,
            audited=p.audited,
            measured=[k for k, f in figs.items() if f.provenance is Provenance.MEASURED],
            estimated=[k for k, f in figs.items() if f.provenance is Provenance.ESTIMATED],
            vendor_ratings=[k for k, f in figs.items() if f.provenance is Provenance.VENDOR],
            marginal_watts_per_core=marginal,
            marginal_status=why,
        ))
    return rows
