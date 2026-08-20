"""**de novo\\*** — the base design plus a bound on how fast the endowment can leave.

The base design accepts, under Q8, that the borrow-forward is unbounded: a large actor
arriving early can take most of the endowment inside the demand index's one-epoch repricing
lag (88% at epoch 20, collapsing a 195-epoch phase to 23). This module is the alternative that
addresses it, kept separate so the base design stays exactly as specified and the variant can
be compared against it rather than replacing it.

**Why the obvious cap does not work.** The intuitive bound is on the borrow itself: no epoch
may spend more than `m` budgets. It cannot separate the honest case from the hostile one,
because they are the same shape to the mechanism. One budget is about `1/195` of the
endowment, and an honest ×100 cohort borrows about 97 of them — so a cap loose enough to admit
the cohort R5 exists to protect already permits half the endowment to leave in a single epoch.
(An earlier draft of the adversarial analysis recommended `m ≈ 3` on the strength of a
mis-measured 2.6× figure; at the true ~97 that cap would ration the honest cohort savagely.)

**What the variant does instead.** Bound the *endowment draw* per epoch as a fraction of what
remains, and let the demand index do the rest:

| `drawable_this_epoch = draw_cap_fraction * endowment_at_epoch_start` |
| --- |

The point is not the ceiling itself but what it converts. Beyond the cap the epoch stops
admitting claims — but the claimants have not gone anywhere, and they claim again next epoch,
by which time `claims_prev` has exploded and the reward has fallen. **The cap turns instant
extraction into extraction across several epochs, which is exactly the interval the index
needs to reprice.** For an honest cohort that is a deferral of a few epochs against a
median time-to-bond of thirty-nine; for a whale it is the difference between beating the
index and being metered by it.

It costs one parameter, against R1, and it softens R6's letter — the pool no longer pays
purely until exhausted. Whether that is worth buying is the decision the comparison sets out.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import arrivals, engine, study
from .params import Derived
from .scenarios import CohortDraw

# Fraction of the standing endowment one epoch may draw. At 10% a whale needs a dozen epochs
# to take what it took in one, and every epoch after its first is priced off its own inflated
# claims_prev.
DEFAULT_CAP = 0.10


@dataclass(frozen=True)
class Outcome:
    label: str
    uniform_bonds: int
    transition: int
    spike_bonded_fraction: float
    spike_median_epochs: float
    whale_capture: float
    whale_phase_end: int


def whale_run(d: Derived, whale_epoch: int, multiple: float, cap: float,
              per_epoch: int = 130, epochs: int = 220):
    """A whale against a field of committed boards, with the variant's cap applied."""
    cfg = d.cfg
    base = study.hashrate_draw(cfg)
    mean_rate = 24_146.0 * (1.0 + 1.0 / 0.16)          # Pareto(1.16) mean at the board floor
    a = arrivals.uniform(epochs, per_epoch)
    a[whale_epoch] += 1
    draw = CohortDraw(base, specials={whale_epoch: multiple * per_epoch * whale_epoch * mean_rate})
    return engine.run(d, a, draw, epochs=epochs, draw_cap_fraction=cap)


def evaluate(d: Derived, cap: float, label: str, retire: bool = True) -> Outcome:
    """One design point: what it onboards, and what it concedes to a whale."""
    cfg = d.cfg
    uni = engine.run(d, arrivals.uniform(220, 130), study.hashrate_draw(cfg), epochs=360,
                     retire_on_bond=retire, draw_cap_fraction=cap)
    spike = engine.run(d, arrivals.spike(220, 130, at=30, factor=100),
                       study.hashrate_draw(cfg), epochs=360, retire_on_bond=retire,
                       draw_cap_fraction=cap)
    row = study.cohort_table(spike, [30])[0]
    w = whale_run(d, whale_epoch=20, multiple=10.0, cap=cap)
    return Outcome(
        label=label,
        uniform_bonds=uni.rows[-1].bonds_total,
        transition=uni.transition_epoch,
        spike_bonded_fraction=row["bonded_frac"],
        spike_median_epochs=row["median_epochs_to_bond"],
        whale_capture=w.pop.balance.max() / d.endowment_genesis,
        whale_phase_end=w.transition_epoch,
    )


def sweep(d: Derived, caps=(0.0, 0.20, 0.10, 0.05, 0.02)) -> list[Outcome]:
    out = []
    for c in caps:
        out.append(evaluate(d, c, "de novo (base)" if c == 0 else f"de novo* cap {c:.0%}"))
    return out


def main() -> int:
    from .params import Triple
    d = Triple().derived()
    print("de novo* -- bounding the endowment draw per epoch")
    print(f"{'design':<20} {'bonds':>8} {'transition':>11} {'x100 bonded':>12} "
          f"{'median ep':>10} {'whale takes':>12} {'phase ends':>11}")
    for o in sweep(d):
        print(f"{o.label:<20} {o.uniform_bonds:>8,} {o.transition:>11} "
              f"{o.spike_bonded_fraction:>11.0%} {o.spike_median_epochs:>10.0f} "
              f"{o.whale_capture:>11.0%} {o.whale_phase_end:>11}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
