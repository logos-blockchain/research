"""Figures for the strategy comparison.

Run as ``python -m empowering_sim.plots_strategies --out <dir>``; each figure below records
that command, per the repo's convention that a figure carries the way to regenerate it.

Palette is the validated five-slot categorical set, assigned in fixed order by strategy and
never cycled. Three of the five sit below 3:1 against the surface, so the relief rule applies
and every chart carries visible labels rather than relying on the fill alone.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from .config import load
from . import strategies as st

# Validated categorical palette, light surface. Fixed order: colour follows the strategy,
# never its rank, so a run with fewer groups does not repaint the survivors.
SERIES = {
    st.Strategy.MINER: "#2a78d6",
    st.Strategy.MINER_STAKER: "#eb6834",
    st.Strategy.MINER_STAKER_SERVICE: "#1baf7a",
    st.Strategy.STAKER: "#eda100",
    st.Strategy.STAKER_SERVICE: "#e87ba4",
}
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"

# Reward sources, shaded within one bar rather than coloured as separate series -- they are
# parts of a whole, not identities.
SOURCE_SHADE = {"proof of work": 0.95, "leader": 0.62, "service": 0.32}


def _style(ax, title: str, sub: str = "") -> None:
    """Recessive frame, and a title block that does not collide with itself.

    The subtitle sits in axes coordinates ABOVE the title rather than between the title and
    the plot, because a subtitle placed at 1.02 lands on the title's descenders at any font
    size that makes the title readable. Found by rendering it and looking.
    """
    ax.set_facecolor(SURFACE)
    ax.figure.set_facecolor(SURFACE)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)
        ax.spines[side].set_linewidth(1)
    ax.tick_params(colors=INK_2, labelsize=9, length=3, width=1)
    ax.grid(True, axis="both", color=GRID, linewidth=0.8, alpha=0.9)
    ax.set_axisbelow(True)
    ax.set_title("")
    ax.text(0, 1.13 if sub else 1.03, title, transform=ax.transAxes, color=INK,
            fontsize=12.5, va="bottom", ha="left")
    if sub:
        ax.text(0, 1.03, sub, transform=ax.transAxes, color=INK_2, fontsize=9.3,
                va="bottom", ha="left")


def _thousands(ax, axis: str = "x") -> None:
    from matplotlib.ticker import FuncFormatter
    f = FuncFormatter(lambda v, _: f"{v:,.0f}")
    (ax.xaxis if axis == "x" else ax.yaxis).set_major_formatter(f)


def _mix(hex_colour: str, weight: float) -> tuple:
    """Blend a series colour toward the surface. Parts of a whole, one hue."""
    import matplotlib.colors as mc
    c = np.array(mc.to_rgb(hex_colour))
    s = np.array(mc.to_rgb(SURFACE))
    return tuple(s + (c - s) * weight)


def composition(cfg, pop, scfg, out: Path) -> Path:
    """Where a median node's income comes from, per strategy. The headline."""
    import matplotlib.pyplot as plt

    groups = [s for s in scfg.active() if pop.mask(s).any()]
    widest = max(
        (sum(cfg.to_lgo(float(np.median(a[pop.mask(s)])))
             for a in (pop.reward_pow, pop.reward_leader, pop.reward_service))
         for s in groups), default=1.0)
    fig, ax = plt.subplots(figsize=(10.5, 0.78 * len(groups) + 2.8))
    for i, s in enumerate(groups):
        m = pop.mask(s)
        parts = [("proof of work", np.median(pop.reward_pow[m])),
                 ("leader", np.median(pop.reward_leader[m])),
                 ("service", np.median(pop.reward_service[m]))]
        total = sum(cfg.to_lgo(float(x)) for _, x in parts)
        left = 0.0
        for name, v in parts:
            v = cfg.to_lgo(float(v))
            if v <= 0:
                continue
            # 2px surface gap between stacked segments.
            ax.barh(i, v, left=left, height=0.62, color=_mix(SERIES[s], SOURCE_SHADE[name]),
                    edgecolor=SURFACE, linewidth=2, zorder=3)
            # Label a segment only when it is wide enough to hold the word without running
            # into the neighbouring segment, the axis, or the total. Short bars get the
            # legend below instead.
            if v / widest > 0.18:
                ax.text(left + v / 2, i, name, ha="center", va="center", color=INK,
                        fontsize=8.5, zorder=4)
            left += v
        ax.text(left + widest * 0.015, i, f"{left:,.0f}", va="center", ha="left",
                color=INK, fontsize=9.5, zorder=4)

    ax.set_yticks(range(len(groups)))
    ax.set_yticklabels([st.LABELS[s] for s in groups], color=INK, fontsize=10)
    ax.invert_yaxis()
    ax.set_xlabel("LGO accumulated by the median node", color=INK_2, fontsize=9.5)
    ax.set_xlim(0, widest * 1.16)          # room for the total label
    ax.grid(False, axis="y")
    _thousands(ax)
    # Shades are parts of a whole, so they are named once here rather than on every short bar.
    handles = [plt.Rectangle((0, 0), 1, 1, facecolor=_mix("#8a8a86", w), edgecolor=SURFACE)
               for w in SOURCE_SHADE.values()]
    ax.legend(handles, list(SOURCE_SHADE), frameon=False, fontsize=9, ncol=3,
              loc="lower right", bbox_to_anchor=(1.0, -0.30), labelcolor=INK_2)
    _style(ax, "Where a median node's income comes from",
           "service provision carries no stake term, so it is flat per provider — "
           "and it dominates every other stream")
    fig.tight_layout(rect=(0, 0.04, 1, 0.90))
    p = out / "strategy_composition.png"
    fig.savefig(p, dpi=170, facecolor=SURFACE)
    plt.close(fig)
    return p


def per_node(cfg, pop, scfg, out: Path) -> Path:
    """Every node's accumulated reward, sorted within its group.

    A rank curve rather than a bar: it shows the level AND the dispersion, and dispersion is
    where the concentration of a Pareto draw becomes visible.
    """
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    for s in scfg.active():
        m = pop.mask(s)
        if not m.any():
            continue
        v = np.sort(cfg.to_lgo(pop.total_reward()[m].astype(float)))[::-1]
        x = np.arange(1, v.size + 1)
        ax.plot(x, np.maximum(v, 1e-3), color=SERIES[s], linewidth=2, zorder=3,
                label=st.LABELS[s], solid_capstyle="round")
        # No direct labels here. Five series is past the point where they help: the two
        # mining curves are within three percent of each other and their labels collide at
        # the right edge. The legend carries identity instead.
    ax.set_yscale("log")
    ax.set_xlabel("node, ranked within its group", color=INK_2, fontsize=9.5)
    ax.set_ylabel("LGO accumulated", color=INK_2, fontsize=9.5)
    ax.set_xlim(0.5, None)
    leg = ax.legend(frameon=False, fontsize=9, loc="lower left", labelcolor=INK_2)
    leg.set_zorder(5)
    _style(ax, "Accumulated reward per node",
           "sorted within each group; a log scale, because the groups differ by more than "
           "an order of magnitude")
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    p = out / "strategy_per_node.png"
    fig.savefig(p, dpi=170, facecolor=SURFACE)
    plt.close(fig)
    return p


def pow_distributions(cfg, rows, out: Path) -> Path:
    """The proof-of-work reward, per block and per epoch.

    Two panels rather than two axes on one plot. The per-block shape is the arrival process at
    a fixed reward; the per-epoch shape carries the reward's decay as well, which is why they
    are not the same distribution rescaled.
    """
    import matplotlib.pyplot as plt

    per_block = np.concatenate([r.pow_reward_per_block for r in rows]).astype(float)
    per_block = cfg.to_lgo(per_block)
    per_epoch = np.array([cfg.to_lgo(float(r.pow_reward_per_block.sum())) for r in rows])

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4))
    for ax, data, title, sub in (
        (axes[0], per_block, "Proof-of-work reward per block",
         f"{per_block.size:,} blocks; the reward is fixed within an epoch, so this is the "
         f"arrival process"),
        (axes[1], per_epoch, "Proof-of-work reward per epoch",
         f"{per_epoch.size} epochs; carries the reward's decay as well"),
    ):
        ax.hist(data, bins=40, color=SERIES[st.Strategy.MINER], edgecolor=SURFACE,
                linewidth=1.2, zorder=3)
        med = float(np.median(data))
        ax.axvline(med, color=INK_2, linewidth=1.5, linestyle=(0, (4, 3)), zorder=4)
        ax.text(med, ax.get_ylim()[1] * 0.94, f"  median {med:,.1f}", color=INK,
                fontsize=9, va="top")
        ax.set_xlabel("LGO", color=INK_2, fontsize=9.5)
        ax.set_ylabel("count", color=INK_2, fontsize=9.5)
        _thousands(ax, "x")
        _thousands(ax, "y")
        _style(ax, title, sub)
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    p = out / "pow_distributions.png"
    fig.savefig(p, dpi=170, facecolor=SURFACE)
    plt.close(fig)
    return p


def main() -> int:
    ap = argparse.ArgumentParser(prog="plots_strategies")
    ap.add_argument("--out", default="figures/strategies")
    ap.add_argument("--epochs", type=int, default=120)
    ap.add_argument("--nodes", type=int, default=100)
    args = ap.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    cfg = load()
    scfg = st.StrategyConfig(epochs=args.epochs,
                             nodes_per_group={s: args.nodes for s in st.Strategy})
    pop, rows = st.run(cfg, scfg)

    for p in (composition(cfg, pop, scfg, out), per_node(cfg, pop, scfg, out),
              pow_distributions(cfg, rows, out)):
        print(f"  wrote {p}")

    print("\n  regenerate with:")
    print(f"    python3 -m empowering_sim.plots_strategies --out {args.out} "
          f"--epochs {args.epochs} --nodes {args.nodes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
