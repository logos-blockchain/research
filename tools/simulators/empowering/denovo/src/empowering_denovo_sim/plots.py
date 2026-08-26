"""The report's figures. One function per figure, all data from `study`'s runs.

Same visual system as the strategy report: categorical colours follow the entity, never the
rank; a legend whenever there are two or more series; recessive grid; direct labels where the
curve earns one.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

from . import arrivals, engine, scenarios, study
from .params import Triple

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
BLUE = "#2a78d6"
ORANGE = "#eb6834"
GREEN = "#1baf7a"
YELLOW = "#eda100"
PINK = "#e87ba4"
DANGER = "#e34948"

SHAPE_COLOURS = {
    "uniform": BLUE, "spike x10": ORANGE, "spike x100": GREEN,
    "front-loaded": YELLOW, "back-loaded": PINK,
}


def _style(ax, title="", subtitle=""):
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK_2, labelsize=8.5)
    if title:
        ax.set_title(title, color=INK, fontsize=10.5, loc="left", pad=10)
    if subtitle:
        ax.text(0, 1.015, subtitle, transform=ax.transAxes, color=INK_2, fontsize=8.5)


def _fig(n=2, w=11.6, h=4.4):
    f, axes = plt.subplots(1, n, figsize=(w, h))
    f.patch.set_facecolor(SURFACE)
    for a in (axes if n > 1 else [axes]):
        _style(a)
    return f, axes


def _thousands(ax, axis="y"):
    getattr(ax, f"{axis}axis").set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))


def two_regimes(d, r, out: Path) -> Path:
    rows = r.rows
    x = [q.epoch for q in rows]
    f, (a0, a1) = _fig()

    a0.plot(x, [q.endowment / d.endowment_genesis * 100 for q in rows], color=BLUE,
            linewidth=2, zorder=4, label="endowment, % of genesis")
    a0.plot(x, [q.fee_bucket_opening / d.endowment_genesis * 100 for q in rows],
            color=GREEN, linewidth=2, zorder=4, label="fee bucket, same scale")
    a0.annotate("the fee bucket never clears 0.02% of the endowment —\n"
                "during bootstrap, fees are a rounding error",
                (150, 3), fontsize=8.5, color=INK_2)
    a0.axvline(r.transition_epoch, color=INK_2, linewidth=1.1, linestyle=(0, (4, 3)))
    a0.axvspan(r.transition_epoch, x[-1], color=GREEN, alpha=0.06, zorder=1)
    a0.text(r.transition_epoch + 2, 88, f"post-bootstrap\nfrom epoch {r.transition_epoch}",
            color=INK_2, fontsize=8.5)
    a0.set_xlabel("epoch", color=INK_2, fontsize=9)
    a0.set_ylabel("bucket level, % of the genesis endowment", color=INK_2, fontsize=9)
    a0.legend(frameon=False, fontsize=8.5, labelcolor=INK_2, loc="center left")
    _style(a0, "The endowment spends on schedule and ends",
           "linear amortisation: the phase has an end, which a geometric rate never had")

    a1.semilogy(x, [q.reward / 1e9 for q in rows], color=ORANGE, linewidth=2, zorder=4)
    a1.axhline(d.anchor / 1e9, color=INK_2, linewidth=1.1, linestyle=(0, (4, 3)))
    a1.text(3, d.anchor / 1e9 * 1.6, f"the anchor: two transfers, "
            f"{d.anchor:,} lepta", color=INK_2, fontsize=8.5)
    a1.axvline(r.transition_epoch, color=INK_2, linewidth=1.1, linestyle=(0, (4, 3)))
    a1.set_xlabel("epoch", color=INK_2, fontsize=9)
    a1.set_ylabel("reward per claim, LGO (log)", color=INK_2, fontsize=9)
    _style(a1, "The reward glides from subsidy to anchor",
           "demand-indexed while the endowment lasts, the anchor exactly afterwards")

    f.suptitle("One run, two regimes, no parameter at the boundary", color=INK,
               fontsize=12.5, x=0.008, ha="left", y=0.99)
    f.tight_layout(rect=(0, 0, 1, 0.90))
    p = out / "two_regimes.png"
    f.savefig(p, dpi=170, facecolor=SURFACE)
    plt.close(f)
    return p


def spike_absorption(d, runs, out: Path) -> Path:
    f, (a0, a1) = _fig()

    for name in ("uniform", "spike x10", "spike x100"):
        rows = runs[name].rows[20:46]
        a0.semilogy([q.epoch for q in rows], [max(q.claims_paid, 1) for q in rows],
                    color=SHAPE_COLOURS[name], linewidth=2, zorder=4, label=name)
    a0.axvline(30, color=INK_2, linewidth=1.0, linestyle=(0, (2, 2)))
    a0.text(30.3, 2e6, "the cohort lands", color=INK_2, fontsize=8.5)
    a0.set_xlabel("epoch", color=INK_2, fontsize=9)
    a0.set_ylabel("claims paid per epoch (log)", color=INK_2, fontsize=9)
    a0.legend(frameon=False, fontsize=8.5, labelcolor=INK_2, loc="upper right")
    _style(a0, "A cohort is paid, not queued",
           "the epoch saturates, the borrow-forward covers it, the index reprices next epoch")

    r100 = runs["spike x100"]
    table = study.cohort_table(r100, range(24, 41))
    xs = [t["cohort"] for t in table]
    fr = [t["bonded_frac"] * 100 for t in table]
    cols = [GREEN if t["cohort"] == 30 else BLUE for t in table]
    a1.bar(xs, fr, 0.7, color=cols, zorder=4)
    a1.set_ylim(0, 119)
    spike_row = next(t for t in table if t["cohort"] == 30)
    a1.annotate(f"the ×100 cohort: {spike_row['n']:,} nodes,\n"
                f"{spike_row['bonded_frac']:.0%} bonded, median "
                f"{spike_row['median_epochs_to_bond']:.0f} epochs",
                (30, 103), ha="center", fontsize=8.5, color=INK_2)
    a1.set_xticks([24, 26, 28, 30, 32, 34, 36, 38, 40])
    a1.set_xlabel("arrival cohort (epoch)", color=INK_2, fontsize=9)
    a1.set_ylabel("cohort members reaching the bond, %", color=INK_2, fontsize=9)
    _style(a1, "Nobody in the cohort is pushed away (R5)",
           "bond rate by arrival cohort; the hundredfold cohort in green")

    f.suptitle("A hundredfold spike of interest, absorbed", color=INK, fontsize=12.5,
               x=0.008, ha="left", y=0.99)
    f.tight_layout(rect=(0, 0, 1, 0.90))
    p = out / "spike_absorption.png"
    f.savefig(p, dpi=170, facecolor=SURFACE)
    plt.close(f)
    return p


def arrival_shapes_fig(d, runs, out: Path) -> Path:
    f, (a0, a1) = _fig()

    finals = sorted((r.rows[-1].bonds_total, name) for name, r in runs.items())
    slots = {}
    last_y = None
    for val, name in finals:                     # stagger labels that land within 900 bonds
        y = val if last_y is None or val - last_y > 900 else last_y + 900
        slots[name] = y
        last_y = y
    for name, r in runs.items():
        rows = r.rows
        a0.plot([q.epoch for q in rows], [q.bonds_total for q in rows],
                color=SHAPE_COLOURS[name], linewidth=2, zorder=4, label=name)
        a0.annotate(f"{rows[-1].bonds_total:,}", (rows[-1].epoch, slots[name]),
                    textcoords="offset points", xytext=(4, -2), fontsize=8,
                    color=SHAPE_COLOURS[name])
    a0.axhline(25_000, color=INK_2, linewidth=1.0, linestyle=(0, (4, 3)))
    a0.text(4, 25_600, "the 25,000-node target", color=INK_2, fontsize=8.5)
    a0.set_xlim(0, 385)
    a0.set_xlabel("epoch", color=INK_2, fontsize=9)
    a0.set_ylabel("nodes bonded", color=INK_2, fontsize=9)
    _thousands(a0)
    a0.legend(frameon=False, fontsize=8.5, labelcolor=INK_2, loc="center right")
    _style(a0, "Arrival timing moves the schedule, not the outcome",
           "all five shapes convert; late interest takes longer, on the Q7 nominal-rate tail")

    labels, vals, cols = [], [], []
    for name, r in runs.items():
        labels.append(name)
        vals.append(r.transition_epoch if r.transition_epoch != engine.NOT_SET else 0)
        cols.append(SHAPE_COLOURS[name])
    y = np.arange(len(labels))
    a1.barh(y, vals, 0.62, color=cols, zorder=4)
    a1.axvline(195, color=INK_2, linewidth=1.1, linestyle=(0, (4, 3)))
    a1.text(206, 2.0, "the dashed line:\nexpected, 195", color=INK_2, fontsize=8.5,
            va="center")
    for i, (name, v) in enumerate(zip(labels, vals)):
        a1.text(max(v, 4) + 4, i, f"{v}" if v else "in the tail — endowment still armed",
                va="center", fontsize=8.5, color=INK_2)
    a1.set_yticks(y)
    a1.set_yticklabels(labels, fontsize=8.5)
    a1.set_xlabel("transition epoch", color=INK_2, fontsize=9)
    a1.set_xlim(0, 385)
    _style(a1, "The phase ends when the money is spent, not when the clock says",
           "early or late surpluses stay armed at the nominal rate for whoever comes next")

    f.suptitle("The same field, five arrival shapes", color=INK, fontsize=12.5,
               x=0.008, ha="left", y=0.99)
    f.tight_layout(rect=(0, 0, 1, 0.90))
    p = out / "arrival_shapes.png"
    f.savefig(p, dpi=170, facecolor=SURFACE)
    plt.close(f)
    return p


def post_phase(d, r, r_sparse, out: Path) -> Path:
    cfg = d.cfg
    f, (a0, a1) = _fig()

    post = [q for q in r.rows if not q.bootstrap]
    xs = [q.epoch for q in post]
    sat = [q.saturation_block if q.saturation_block != engine.NOT_SET
           else cfg.blocks_per_epoch for q in post]
    a0.plot(xs, sat, color=BLUE, linewidth=2, zorder=4, label="reference traffic (600 txs)")
    posts = [q for q in r_sparse.rows if not q.bootstrap]
    a0.plot([q.epoch for q in posts],
            [q.saturation_block if q.saturation_block != engine.NOT_SET
             else cfg.blocks_per_epoch for q in posts],
            color=ORANGE, linewidth=2, zorder=4, label="sparse traffic (20 txs)")
    a0.axhline(cfg.blocks_per_epoch, color=INK_2, linewidth=1.0, linestyle=(0, (4, 3)))
    a0.text(xs[0] + 1, cfg.blocks_per_epoch * 1.005, "the epoch's end", color=INK_2,
            fontsize=8.5)
    a0.set_ylim(0, cfg.blocks_per_epoch * 1.09)
    a0.set_xlabel("epoch", color=INK_2, fontsize=9)
    a0.set_ylabel("saturation point, block index", color=INK_2, fontsize=9)
    _thousands(a0)
    a0.legend(frameon=False, fontsize=8.5, labelcolor=INK_2, loc="lower right")
    _style(a0, "The throttle steers the saturation point to the epoch end (R7b)",
           "at one claim per block the sparse case can only approach it from below")

    boot_tail = [q for q in r.rows if q.bootstrap][-6:]
    both = boot_tail + post[:30]
    xs2 = [q.epoch for q in both]
    a1.semilogy(xs2, [max(q.difficulty_target, 1) / cfg.genesis_difficulty_target
                      for q in both], color=GREEN, linewidth=2, zorder=4)
    a1.axhline(1.0, color=INK_2, linewidth=1.0, linestyle=(0, (4, 3)))
    a1.text(xs2[0], 1.7, "the bootstrap floor", color=INK_2, fontsize=8.5)
    a1.axvline(r.transition_epoch, color=INK_2, linewidth=1.1, linestyle=(0, (2, 2)))
    a1.set_xlabel("epoch", color=INK_2, fontsize=9)
    a1.set_ylabel("difficulty target over the floor (log)", color=INK_2, fontsize=9)
    _style(a1, "One retarget implementation, woken at the transition",
           "the EMA walks from the floor to the fee-budget equilibrium; no special case")

    f.suptitle("After the endowment: fees in, anchor out, claims spread", color=INK,
               fontsize=12.5, x=0.008, ha="left", y=0.99)
    f.tight_layout(rect=(0, 0, 1, 0.90))
    p = out / "post_phase.png"
    f.savefig(p, dpi=170, facecolor=SURFACE)
    plt.close(f)
    return p


def adversarial(d, out: Path) -> Path:
    f, (a0, a1) = _fig()

    mults = (1.0, 3.0, 10.0)
    capture, honest = [], []
    for m in mults:
        r = scenarios.whale_run(d, 130, whale_epoch=30, whale_multiple=m, epochs=220)
        capture.append(r.pop.balance.max() / d.endowment_genesis * 100)
        honest.append(r.rows[-1].bonds_total)
    x = np.arange(len(mults))
    a0.bar(x - 0.19, capture, 0.36, color=DANGER, zorder=4, label="endowment captured, %")
    a0.bar(x + 0.19, [h / 286 for h in honest], 0.36, color=BLUE, zorder=4,
           label="honest bonds, % of arrivals")
    for i, (c, h) in enumerate(zip(capture, honest)):
        a0.text(i - 0.19, c + 2, f"{c:.0f}%", ha="center", fontsize=8.5, color=INK_2)
        a0.text(i + 0.19, h / 286 + 2, f"{h:,}", ha="center", fontsize=8, color=INK_2)
    a0.set_xticks(x)
    a0.set_xticklabels([f"{m:g}×" for m in mults], fontsize=9)
    a0.set_xlabel("whale size, multiple of the field it meets", color=INK_2, fontsize=9)
    a0.set_ylabel("percent", color=INK_2, fontsize=9)
    a0.set_ylim(0, 108)
    a0.legend(frameon=False, fontsize=8.5, labelcolor=INK_2, loc="upper left")
    _style(a0, "The whale: what one large actor takes",
           "extraction is bounded per epoch by block space × reward, but the burst beats the index's one-epoch lag")

    r_stable = scenarios.elastic_run(d, 130, epochs=120,
                                     threshold_lepta=2_000_000_000, eta=0.5)
    r_cycle = scenarios.elastic_run(d, 130, epochs=120,
                                    threshold_lepta=4_500_000_000, eta=8.0)
    win = slice(90, 118)
    a1.semilogy([q.epoch for q in r_stable.rows[win]],
                [max(q.claims_paid, 1) for q in r_stable.rows[win]],
                color=BLUE, linewidth=2, zorder=4, label="threshold below the reward: stable")
    a1.semilogy([q.epoch for q in r_cycle.rows[win]],
                [max(q.claims_paid, 1) for q in r_cycle.rows[win]],
                color=ORANGE, linewidth=2, zorder=4, label="threshold at the reward: period-2")
    a1.set_xlabel("epoch", color=INK_2, fontsize=9)
    a1.set_ylabel("claims paid per epoch (log)", color=INK_2, fontsize=9)
    a1.text(117.6, 4.5e4, "threshold below\nthe reward: stable", color=BLUE, fontsize=8.5,
            va="center")
    a1.text(117.6, 30, "threshold at the\nreward: period-2", color=ORANGE, fontsize=8.5,
            va="center")
    a1.set_xlim(89, 126)
    _style(a1, "The demand index, and the participation cliff",
           "a sharp entry threshold at the running reward hard-cycles the field")

    f.suptitle("The two findings the matrix surfaced — both are the index's one-epoch lag",
               color=INK, fontsize=12.5, x=0.008, ha="left", y=0.99)
    f.tight_layout(rect=(0, 0, 1, 0.90))
    p = out / "adversarial.png"
    f.savefig(p, dpi=170, facecolor=SURFACE)
    plt.close(f)
    return p


def retirement_price(d, out: Path) -> Path:
    """The token price sets the regime: dearer sustains incumbent mining, onboards fewer.

    Backs adversarial-analysis §2.3 and SUMMARY §3.5. Both panels from
    `retirement.price_curve` — the same runs the gates pin at $1.00/$0.10/$0.01.
    """
    from . import retirement                                   # noqa: PLC0415

    prices = (10.0, 1.0, 0.50, 0.20, 0.10, 0.05, 0.02, 0.01)
    rows = retirement.price_curve(d, prices=prices)

    f, (a0, a1) = _fig()
    xs = [r["token_usd"] for r in rows]

    a0.plot(xs, [r["bonds"] for r in rows], color=BLUE, linewidth=2.0, zorder=5,
            marker="o", markersize=4.5)
    a0.set_xscale("log")
    a0.invert_xaxis()          # dearer on the LEFT: reading right means the token cheapens
    a0.axhline(24_707, color=INK_2, linewidth=1.0, linestyle=(0, (2, 2)))
    a0.text(xs[0], 24_707, "  the retiring headline (24,707)", color=INK_2, fontsize=8,
            va="bottom")
    _thousands(a0)
    a0.set_xlabel("token price, USD per LGO (log; dearer →← cheaper)", color=INK_2,
                  fontsize=9)
    a0.set_ylabel("nodes onboarded", color=INK_2, fontsize=9)
    _style(a0, "A dearer token onboards FEWER nodes",
           "mining income is in LGO, electricity in dollars — so price sustains incumbents")

    a1.plot(xs, [r["persists_until"] for r in rows], color=ORANGE, linewidth=2.0, zorder=5,
            marker="o", markersize=4.5)
    a1.set_xscale("log")
    a1.invert_xaxis()
    a1.axhline(d.bootstrap_epochs, color=INK_2, linewidth=1.0, linestyle=(0, (2, 2)))
    a1.text(xs[-1], d.bootstrap_epochs, "the whole scheduled phase  ", color=INK_2,
            fontsize=8, va="bottom", ha="right")
    a1.set_xlabel("token price, USD per LGO (log; dearer →← cheaper)", color=INK_2,
                  fontsize=9)
    a1.set_ylabel("incumbents keep mining until epoch", color=INK_2, fontsize=9)
    _style(a1, "Above about $0.20 they mine the whole phase",
           "each bonded miner re-decides every epoch; this is the decided outcome")

    f.suptitle("Retirement is decided by the token price — and dearer is worse", color=INK,
               fontsize=12.5, x=0.008, ha="left", y=0.99)
    f.tight_layout(rect=(0, 0, 1, 0.90))
    p = out / "retirement_price.png"
    f.savefig(p, dpi=170, facecolor=SURFACE)
    plt.close(f)
    return p


def flood_denial(d, out: Path) -> Path:
    """The fake-identity flood, all three designs, measured in this figure's own runs.

    Backs adversarial-analysis §4 and SUMMARY §3.4. The de-novo bars come from
    `adversary.sybil_denial` (the gated measurement); the current-design bars are computed
    HERE from `empowering_sim.elevation` at the same honest rate and window, so the figure
    carries no transcribed numbers at all.
    """
    from empowering_sim import elevation as el                 # noqa: PLC0415

    from . import adversary as adv                             # noqa: PLC0415
    from . import variant                                      # noqa: PLC0415

    cfg = d.cfg
    multiples = (2, 5, 10)

    base = el.run(cfg, el.ElevationConfig(miners_per_epoch=100, epochs=400,
                                          retire_on_bond=True)).elevated
    current = []
    for k in multiples:
        total = el.run(cfg, el.ElevationConfig(miners_per_epoch=100 * k, epochs=400,
                                               retire_on_bond=True)).elevated
        current.append(1.0 - (total / k) / base)
    dn = [r["denied"] for r in adv.sybil_denial(d, multiples=multiples)[1:]]
    dns = [r["denied"] for r in adv.sybil_denial(d, multiples=multiples,
                                                 cap=variant.DEFAULT_CAP)[1:]]

    f, ax = _fig(n=1, w=7.6, h=4.4)
    x = np.arange(len(multiples))
    w = 0.26
    for off, vals, colour, label in ((-w, current, DANGER, "current"),
                                     (0.0, dn, BLUE, "de novo"),
                                     (w, dns, GREEN, "de novo*")):
        bars = ax.bar(x + off, [v * 100 for v in vals], width=w * 0.92, color=colour,
                      zorder=5, label=label)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, v * 100 + 1.2, f"{v:.0%}",
                    ha="center", color=INK_2, fontsize=8)
    ax.set_xticks(x, [f"{k}× the honest crowd" for k in multiples])
    ax.set_ylim(0, 108)
    ax.set_ylabel("honest joiners denied", color=INK_2, fontsize=9)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left", labelcolor=INK_2)
    _style(ax, "", "100 honest arrivals an epoch, 400 epochs, retirement on — every bar "
                   "from a run in this figure's own code")
    f.suptitle("Flooded with fake identities: who gets crowded out", color=INK,
               fontsize=12.5, x=0.008, ha="left", y=0.985)
    f.tight_layout(rect=(0, 0, 1, 0.92))
    p = out / "flood_denial.png"
    f.savefig(p, dpi=170, facecolor=SURFACE)
    plt.close(f)
    return p


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="empowering_denovo_sim.plots")
    ap.add_argument("--out", default="../../../../reports/empowering/denovo/figures")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    d = Triple().derived().check()
    runs = study.run_shapes(d)
    r_uniform = runs["uniform"]
    r_sparse = engine.run(d, arrivals.uniform(240, 130), study.hashrate_draw(d.cfg),
                          epochs=240, txs_per_block=20)

    for p in (two_regimes(d, r_uniform, out),
              spike_absorption(d, runs, out),
              arrival_shapes_fig(d, runs, out),
              post_phase(d, r_uniform, r_sparse, out),
              adversarial(d, out),
              retirement_price(d, out),
              flood_denial(d, out)):
        print(f"  wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
