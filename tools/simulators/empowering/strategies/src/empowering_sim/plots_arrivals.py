"""Figures for the dynamic-arrivals study: Poisson joiners, and what the mechanism absorbs.

Run as ``python -m empowering_sim.plots_arrivals --out <dir>``. Separate from
`plots_strategies` because the runs behind these are long -- a horizon of 600 epochs across
an amplitude sweep and both retirement rules -- and folding them in would make regenerating
the six cheap figures take minutes.

Style, palette and the title block come from `plots_strategies`, imported rather than
restated: these figures sit in the same report beside those ones and any drift between the
two would read as meaning.

**Amplitude is ordered, so it is not coloured categorically.** The arrival rate is a
magnitude, and the reader should be able to see the order in the colour without consulting a
legend, so the amplitude series take a single-hue ordinal ramp -- the documented blue steps
250/350/450/550/700 -- validated for monotone lightness, adjacent step separation and a light
end that still clears the surface. Identity that is *not* ordered -- which measure, which
retirement rule, which arrival shape -- keeps the categorical palette in its fixed order.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import numpy as np

from . import arrivals as ar
from .config import load
from .plots_strategies import GRID, INK_2, SERIES, SURFACE, _style, _thousands

# Ordinal ramp for the arrival amplitude: one hue, light to dark, five steps. Validated on the
# light surface -- monotone lightness, every adjacent gap over 0.06, and the light end at
# 2.06:1 against the surface, which is the documented floor for an ordinal ramp.
AMP_RAMP = ("#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b")
DANGER = "#e34948"

AMPLITUDES = (2, 5, 10, 25, 50, 100, 250, 500)
COHORT_AMPS = (5, 25, 50, 100, 250)
QUEUE_AMPS = (10, 50, 100)
EPOCHS = 600


class Runs:
    """Every run the figures need, computed once and shared.

    The amplitude sweep alone is sixteen runs of six hundred epochs; the figures overlap
    heavily in what they ask for, and running the study once per panel would triple the cost
    for no additional information.
    """

    def __init__(self, cfg, epochs: int = EPOCHS, seed: int = 40_001):
        self.cfg, self.epochs, self.seed = cfg, epochs, seed
        self._cache: dict[tuple, ar.DynamicRun] = {}

    def get(self, amplitude: float, *, retire: bool = False, shape: str = ar.FLAT):
        key = (amplitude, retire, shape)
        if key not in self._cache:
            process = ar.Arrivals(amplitude=amplitude, shape=shape)
            self._cache[key] = ar.run_dynamic(self.cfg, process, epochs=self.epochs,
                                              seed=self.seed, retire=retire)
        return self._cache[key]

    def sweep(self, retire: bool = False) -> list[ar.DynamicRun]:
        return [self.get(a, retire=retire) for a in AMPLITUDES]


def _end_label(ax, x, y, text, colour) -> None:
    """Name a line at its right-hand end, so identity never rests on colour alone."""
    ax.annotate(text, xy=(x, y), xytext=(6, 0), textcoords="offset points",
                color=colour, fontsize=8.5, va="center", ha="left", zorder=6)


def _end_labels(ax, x, entries, gap: float) -> None:
    """End labels for lines that finish close together, pushed apart just enough to read.

    Two of the four arrival shapes land within two percent of each other, which is itself the
    result -- so the labels must not overlap into illegibility, and must not move so far that
    they stop pointing at their own line. One upward pass with a minimum gap does both:
    nothing moves unless it has to, and then only by what it has to.

    ``entries`` is a sequence of ``(y, text, colour)``.
    """
    place = 0.0
    for i, (y, text, colour) in enumerate(sorted(entries, key=lambda e: e[0])):
        place = y if i == 0 else max(y, place + gap)
        _end_label(ax, x, place, text, colour)


def arrival_process(runs: Runs, out: Path) -> Path:
    """The process itself, and the queue it leaves behind.

    Left is one realisation, drawn rather than described: Poisson arrivals jitter around the
    amplitude epoch by epoch, and the elevation rate separates from them within the first
    year and never comes back. The pool's own capacity -- the bonds an epoch's payout could
    fund if every lepton of it landed on a miner at the threshold -- is the falling ceiling
    above both, and it is the reason the gap never closes.

    Right is the study's central picture, and the two lines are in the same units on purpose.
    The queue of miners waiting below the bond RISES with every arrival; the bonds the
    remaining pool could ever fund FALLS on the drain clock. Where they cross, the waiting
    population has passed what the endowment can still pay for, whatever anyone does next.
    """
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))
    cfg, epochs = runs.cfg, runs.epochs
    x = np.arange(epochs)

    # -- left: one realisation
    r = runs.get(50)
    axes[0].plot(x, r.per_epoch_in, color=SERIES[list(SERIES)[0]], linewidth=1.0, alpha=0.85,
                 zorder=3)
    axes[0].plot(x, ar._smooth(r.per_epoch_up, 9), color=SERIES[list(SERIES)[1]], linewidth=2,
                 zorder=4, solid_capstyle="round")
    axes[0].plot(x, r.capacity, color=INK_2, linewidth=1.4, linestyle=(0, (5, 3)), zorder=5)
    _end_label(axes[0], x[-1], r.capacity[-1], "pool capacity", INK_2)
    _end_label(axes[0], x[-1], r.per_epoch_in[-20:].mean(), "arrivals", SERIES[list(SERIES)[0]])
    _end_label(axes[0], x[-1], ar._smooth(r.per_epoch_up, 9)[-1], "elevations",
               SERIES[list(SERIES)[1]])
    axes[0].set_xlim(0, epochs * 1.20)
    axes[0].set_ylim(0, 275)
    axes[0].set_xlabel("epoch", color=INK_2, fontsize=9.5)
    axes[0].set_ylabel("nodes per epoch", color=INK_2, fontsize=9.5)
    _style(axes[0], "One realisation, at 50 arrivals an epoch",
           "the arrivals jitter; the elevations fall away from them for good")

    # -- right: the queue against what can still be paid for
    ramp = (AMP_RAMP[0], AMP_RAMP[2], AMP_RAMP[4])
    for i, amp in enumerate(QUEUE_AMPS):
        q = runs.get(amp)
        backlog = np.cumsum(q.per_epoch_in) - np.cumsum(q.per_epoch_up)
        axes[1].plot(x, backlog, color=ramp[i], linewidth=2, zorder=4, solid_capstyle="round")
        _end_label(axes[1], x[-1], backlog[-1], f"{amp}/epoch", ramp[i])
        nr = q.absorption.no_return_epoch
        if nr is not None:
            axes[1].plot([nr], [backlog[nr]], marker="o", markersize=6, color=ramp[i],
                         markeredgecolor=SURFACE, markeredgewidth=1.6, zorder=6)
    fundable = runs.get(50).pool_pct / 100.0 * cfg.to_lgo(cfg.genesis_pool) / cfg.min_stake_lgo
    axes[1].plot(x, fundable, color=DANGER, linewidth=1.6, linestyle=(0, (5, 3)), zorder=5)
    # Named where it is alone. At the right edge it lands on the smallest backlog curve --
    # which is the crossing this panel is about, so the labels collide exactly where the
    # picture matters most.
    axes[1].annotate("bonds the pool can still fund", xy=(epochs * 0.12, fundable[int(epochs * 0.12)]),
                     xytext=(8, 8), textcoords="offset points", color=DANGER, fontsize=8.5,
                     va="bottom", ha="left", zorder=6)
    axes[1].set_xlim(0, epochs * 1.20)
    axes[1].set_xlabel("epoch", color=INK_2, fontsize=9.5)
    axes[1].set_ylabel("nodes", color=INK_2, fontsize=9.5)
    _thousands(axes[1], "y")
    _style(axes[1], "The queue rises, the money to clear it falls",
           "the dot is where the queue passes what the pool can still fund")

    fig.tight_layout(rect=(0, 0, 1, 0.88), w_pad=4.0)
    p = out / "arrival_process.png"
    fig.savefig(p, dpi=170, facecolor=SURFACE)
    plt.close(fig)
    return p


def absorption_window(runs: Runs, out: Path) -> Path:
    """How long the door stays open, and what closes it.

    Left: the odds a miner arriving in a given epoch ever reaches the bond. Every amplitude
    starts at certainty and ends at nothing; the amplitude decides only how long the first
    part lasts. This is the study's answer to "how many can be absorbed" -- not a number but a
    window, and the window is what a prospective joiner actually faces.

    Right: that window against the arrival rate, beside the two bounds that explain it. The
    arithmetic crossing is where the pool's gross capacity falls under the arrival rate and
    knows nothing about conversion; the point of no return is where the queue passes what the
    pool can ever fund. The measured door sits below both, because a miner needs to reach the
    bond before the pool empties AND before the field it is competing with has grown.
    """
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))
    cfg, epochs = runs.cfg, runs.epochs
    x = np.arange(epochs)

    for i, amp in enumerate(COHORT_AMPS):
        r = runs.get(amp)
        y = ar._smooth(r.cohort_share, 15) * 100
        axes[0].plot(x, y, color=AMP_RAMP[i], linewidth=2, zorder=4, solid_capstyle="round")
        axes[0].plot([], [], color=AMP_RAMP[i], linewidth=2, label=f"{amp} an epoch")
        door = r.absorption.door_epoch
        if door is not None:
            axes[0].plot([door], [y[door]], marker="o", markersize=5.5, color=AMP_RAMP[i],
                         markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=6)
    # Five series is past the point where direct labels help: every door dot sits on the
    # same horizontal line by construction, so the labels stack there. The ordinal ramp
    # carries the order and the legend carries the values.
    axes[0].legend(frameon=False, fontsize=9, loc="upper right", labelcolor=INK_2,
                   title="arrivals", title_fontsize=9, alignment="left")
    axes[0].axhline(50, color=INK_2, linewidth=1.2, linestyle=(0, (4, 3)), zorder=3)
    axes[0].text(epochs * 0.99, 44, "even odds", color=INK_2, fontsize=8, va="top", ha="right")
    axes[0].set_xlim(0, epochs)
    axes[0].set_ylim(0, 108)
    axes[0].set_xlabel("epoch a miner arrives", color=INK_2, fontsize=9.5)
    axes[0].set_ylabel("odds of ever reaching the bond, %", color=INK_2, fontsize=9.5)
    _style(axes[0], "The door closes on everyone, at a speed the amplitude sets",
           "share of an arrival cohort that ever bonds; the dot is where it passes even odds")

    # -- right: the clocks against the amplitude
    amps = np.array(AMPLITUDES, dtype=float)
    door = [runs.get(a).absorption.door_epoch for a in AMPLITUDES]
    nore = [runs.get(a).absorption.no_return_epoch for a in AMPLITUDES]
    closed = [ar.saturation_epoch_closed_form(a, cfg) for a in AMPLITUDES]
    slots = list(SERIES.values())
    for series, colour, name in ((closed, slots[2], "arithmetic crossing"),
                                 (nore, slots[1], "point of no return"),
                                 (door, slots[0], "door closes")):
        vals = np.array([np.nan if v is None else float(v) for v in series])
        ok = ~np.isnan(vals)
        if not ok.any():                   # a measure that never triggered at this horizon
            continue
        axes[1].plot(amps[ok], vals[ok], color=colour, linewidth=2, marker="o", markersize=5,
                     markeredgecolor=SURFACE, markeredgewidth=1.2, zorder=4, label=name)
    # All three converge on zero at the right, so end labels would land on top of one
    # another exactly where the curves already agree. A legend instead.
    axes[1].legend(frameon=False, fontsize=9, loc="upper right", labelcolor=INK_2)
    # The run ends at the horizon, and two of these measures can be censored by it -- a
    # missing point means "not within twelve years", which is a result and not a gap.
    axes[1].axhline(epochs, color=INK_2, linewidth=1.2, linestyle=(0, (4, 3)), zorder=3)
    axes[1].text(2_900, epochs * 0.97, "the run ends here  ", color=INK_2, fontsize=8,
                 va="top", ha="right")
    axes[1].set_xscale("log")
    axes[1].set_xlim(1.6, 3_000)
    axes[1].set_ylim(0, epochs * 1.7)
    axes[1].set_xlabel("arrivals per epoch (mean of the Poisson draw)", color=INK_2,
                       fontsize=9.5)
    axes[1].set_ylabel("epoch", color=INK_2, fontsize=9.5)
    _thousands(axes[1], "x")
    _style(axes[1], "Every closing clock runs on the amplitude",
           "the drain clock would be flat here — it is the one thing arrivals miss")

    fig.tight_layout(rect=(0, 0, 1, 0.88), w_pad=4.0)
    p = out / "absorption_window.png"
    fig.savefig(p, dpi=170, facecolor=SURFACE)
    plt.close(fig)
    return p


def absorption_yield(runs: Runs, out: Path) -> Path:
    """What the amplitude buys, and what the timing buys.

    Left: elevations against the arrival rate, and the surprise is that the curve has a
    maximum. Too few arrivals and there is nobody to elevate; too many and the same fixed
    payout spreads so thin that most of it strands in balances that never reach the bond.
    Both retirement rules have the interior optimum; retiring moves it and roughly
    quadruples it.

    Right: four arrival shapes carrying the SAME population over the horizon, differing only
    in when it turns up. The pool's price per claim decays geometrically, so early arrivals
    are cheap to elevate and late ones are not -- and a mechanism that pays a fixed fraction
    of a shrinking pool cannot be indifferent to timing.
    """
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))
    cfg, epochs = runs.cfg, runs.epochs
    amps = np.array(AMPLITUDES, dtype=float)
    slots = list(SERIES.values())

    for retire, colour, name in ((False, slots[3], "bonded miners keep mining"),
                                 (True, slots[4], "bonded miners retire")):
        y = np.array([r.absorption.elevated for r in runs.sweep(retire)], dtype=float)
        axes[0].plot(amps, y, color=colour, linewidth=2, marker="o", markersize=5,
                     markeredgecolor=SURFACE, markeredgewidth=1.2, zorder=4, label=name)
        peak = int(np.argmax(y))
        axes[0].annotate(f"{y[peak]:,.0f} at {AMPLITUDES[peak]}/epoch",
                         xy=(amps[peak], y[peak]), xytext=(0, 9), textcoords="offset points",
                         color=colour, fontsize=8.5, va="bottom", ha="center", zorder=6)
    axes[0].axhline(cfg.genesis_pool / cfg.min_stake, color=DANGER, linewidth=1.4,
                    linestyle=(0, (2, 2)), zorder=3)
    axes[0].text(1.7, cfg.genesis_pool / cfg.min_stake * 0.95,
                 "50,000 — the arithmetic ceiling", color=DANGER, fontsize=8, va="top",
                 ha="left")
    axes[0].set_xscale("log")
    axes[0].set_xlim(1.6, 800)
    axes[0].set_ylim(0, cfg.genesis_pool / cfg.min_stake * 1.10)
    axes[0].set_xlabel("arrivals per epoch (mean of the Poisson draw)", color=INK_2,
                       fontsize=9.5)
    axes[0].set_ylabel("miners elevated by epoch 600", color=INK_2, fontsize=9.5)
    axes[0].legend(frameon=False, fontsize=9, ncol=2, loc="upper center",
                   bbox_to_anchor=(0.5, -0.22), labelcolor=INK_2)
    _thousands(axes[0], "x")
    _thousands(axes[0], "y")
    _style(axes[0], "Adoption has a best speed, and it is not the fastest",
           "the same endowment, spent on more people than it can carry")

    shapes = (ar.FLAT, ar.RAMP, ar.WAVE, ar.BURST)
    names = {ar.FLAT: "flat", ar.RAMP: "adoption ramp", ar.WAVE: "yearly wave",
             ar.BURST: "one early burst"}
    x = np.arange(epochs)
    ins = axes[1].inset_axes((0.52, 0.14, 0.44, 0.30))
    ins.set_in_layout(False)               # else tight_layout shrinks the row around it
    ends = []
    for i, shape in enumerate(shapes):
        r = runs.get(50, shape=shape)
        cum = np.cumsum(r.per_epoch_up)
        axes[1].plot(x, cum, color=slots[i], linewidth=2, zorder=4, solid_capstyle="round")
        ends.append((float(cum[-1]), f"{names[shape]} — {cum[-1]:,.0f}", slots[i]))
        ins.plot(x, ar.Arrivals(amplitude=50, shape=shape).profile(epochs), color=slots[i],
                 linewidth=1.3, zorder=3 + i)
    _end_labels(axes[1], x[-1], ends, gap=max(e[0] for e in ends) * 0.055)
    ins.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ins.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ins.spines[side].set_color(GRID)
    ins.tick_params(colors=INK_2, labelsize=7, length=2, width=0.8)
    ins.grid(True, color=GRID, linewidth=0.6, alpha=0.9)
    ins.set_axisbelow(True)
    # Linear, not log: the burst's tails fall to numbers no reader has a use for, and a log
    # axis spends most of its height on them. What the inset has to show is that one shape
    # spikes and the others do not, which is a linear fact.
    ins.set_ylim(0, 430)
    ins.text(0, 1.06, "arrivals an epoch — same total, four timings", transform=ins.transAxes,
             color=INK_2, fontsize=8, va="bottom", ha="left")
    axes[1].set_xlim(0, epochs * 1.42)
    axes[1].set_xlabel("epoch", color=INK_2, fontsize=9.5)
    axes[1].set_ylabel("miners elevated, cumulative", color=INK_2, fontsize=9.5)
    _thousands(axes[1], "y")
    _style(axes[1], "Timing moves the outcome, and earlier is not better",
           "one population of thirty thousand, four timings — one realisation of each")

    fig.tight_layout(rect=(0, 0.06, 1, 0.88), w_pad=4.0)
    p = out / "absorption_yield.png"
    fig.savefig(p, dpi=170, facecolor=SURFACE)
    plt.close(fig)
    return p


def numbers(runs: Runs) -> None:
    """Print the table the report quotes, so a figure is never the only record of a number."""
    cfg = runs.cfg
    print(f"\n  Dynamic arrivals, Poisson, {runs.epochs} epochs, seed {runs.seed}")
    print(f"  {'λ':>5} {'seated':>8} {'elevated':>9} {'absorbed':>9} {'keeps up':>9} "
          f"{'door':>6} {'no-return':>10} {'wait':>6} {'providers':>10} {'LGO/prov':>9} "
          f"{'pool%':>7}")
    for amp in AMPLITUDES:
        r = runs.get(amp)
        a = r.absorption
        print(f"  {amp:>5} {a.seated:>8,} {a.elevated:>9,} {a.absorbed:>8.1%} "
              f"{str(a.keeps_up_until):>9} {str(a.door_epoch):>6} "
              f"{str(a.no_return_epoch):>10} {a.median_wait:>6.0f} "
              f"{r.providers[-1]:>10,} {r.service_lgo[-1]:>9,.0f} {r.pool_pct[-1]:>7.3f}")
    print(f"\n  and with bonded miners retiring")
    print(f"  {'λ':>5} {'elevated':>9} {'absorbed':>9} {'of ceiling':>11}")
    ceiling = cfg.genesis_pool / cfg.min_stake
    for amp in AMPLITUDES:
        a = runs.get(amp, retire=True).absorption
        print(f"  {amp:>5} {a.elevated:>9,} {a.absorbed:>8.1%} {a.elevated / ceiling:>10.1%}")

    drains = np.array([runs.get(a).pool_pct for a in AMPLITUDES])
    print(f"\n  widest gap between any two drain curves: "
          f"{float((drains.max(axis=0) - drains.min(axis=0)).max()):.4f} points of the pool")
    without_smallest = np.array([runs.get(a).pool_pct for a in AMPLITUDES[1:]])
    print(f"  and with the smallest amplitude dropped: "
          f"{float((without_smallest.max(axis=0) - without_smallest.min(axis=0)).max()):.6f}")
    for shape in (ar.FLAT, ar.RAMP, ar.WAVE, ar.BURST):
        r = runs.get(50, shape=shape)
        print(f"  shape {shape:>6}: seated {r.absorption.seated:,}, "
              f"elevated {r.absorption.elevated:,}, absorbed {r.absorption.absorbed:.1%}")


def main() -> int:
    ap = argparse.ArgumentParser(prog="plots_arrivals")
    ap.add_argument("--out", default="figures/strategies")
    ap.add_argument("--epochs", type=int, default=EPOCHS)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    runs = Runs(load(), epochs=args.epochs)
    for p in (arrival_process(runs, out), absorption_window(runs, out),
              absorption_yield(runs, out)):
        print(f"  wrote {p}")
    numbers(runs)

    print("\n  regenerate with:")
    print(f"    python3 -m empowering_sim.plots_arrivals --out {args.out} "
          f"--epochs {args.epochs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
