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
from . import services, strategies as st

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


def provider_ramp(cfg, out: Path, cohort_sizes=(16, 32, 64, 100), epochs: int = 40) -> Path:
    """How many nodes become service providers, and when.

    Two panels. On the left, who crosses at the fixed 1,000 LGO bond: the endowed group is
    bonded from the moment its declaration clears the two-epoch snapshot lag, while the miners
    must earn theirs first.

    On the right, the question the left panel raises. Both curves there sit above the floor
    throughout -- but only because the endowed group alone is a hundred nodes. **With the bond
    fixed, whether the stream exists at all comes down to how many nodes turn up.** A network
    of miners with no already-endowed cohort has to reach thirty-two bonded providers on its
    own, and a cohort smaller than that never does, at any bond and after any amount of work.

    The floor is drawn on both, because below it the stream does not pay at all and a ramp
    toward it is not merely slow but pointless.
    """
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))

    # -- left: who crosses, at the settled threshold
    _, rows = st.run(cfg, st.StrategyConfig(epochs=epochs))
    x = [r.epoch for r in rows]
    for k, sgroup in ((st.Strategy.STAKER_SERVICE, "stakeholder"),
                      (st.Strategy.MINER_STAKER_SERVICE, "miner")):
        y = [r.providers_by_strategy[int(k)] for r in rows]
        axes[0].plot(x, y, color=SERIES[k], linewidth=2, zorder=3, label=st.LABELS[k],
                     solid_capstyle="round")
    axes[0].plot(x, [r.providers for r in rows], color=INK_2, linewidth=1.4, zorder=2,
                 linestyle=(0, (5, 3)), label="total")
    # Below the axes: both curves flatten at the same height, so any in-plot legend lands on
    # one of them.
    axes[0].legend(frameon=False, fontsize=9, ncol=3, loc="upper center",
                   bbox_to_anchor=(0.5, -0.22), labelcolor=INK_2)
    axes[0].set_xlabel("epoch", color=INK_2, fontsize=9.5)
    axes[0].set_ylabel("service providers", color=INK_2, fontsize=9.5)
    _style(axes[0], "Who becomes a provider, and when",
           f"at the settled {cfg.min_stake_lgo:,.0f} LGO bond")

    # -- right: miners alone, with no endowed cohort to carry the floor.
    # The bond is fixed, so it is no longer a question. What is left is who turns up.
    miners_only = {x: x in st.MINING for x in st.Strategy}
    for i, k in enumerate(cohort_sizes):
        _, r2 = st.run(cfg, st.StrategyConfig(
            epochs=epochs, enabled=miners_only,
            nodes_per_group={x: k for x in st.Strategy}))
        axes[1].plot([r.epoch for r in r2], [r.providers for r in r2],
                     color=list(SERIES.values())[i], linewidth=2, zorder=3,
                     label=f"{k} nodes", solid_capstyle="round")
    axes[1].legend(frameon=False, fontsize=9, ncol=4, loc="upper center",
                   bbox_to_anchor=(0.5, -0.22), labelcolor=INK_2,
                   title="miner cohort, nobody already inside", title_fontsize=9)
    axes[1].set_xlabel("epoch", color=INK_2, fontsize=9.5)
    axes[1].set_ylabel("service providers", color=INK_2, fontsize=9.5)
    _style(axes[1], "Miners alone, with nobody already inside",
           "a cohort under 32 never turns the stream on, however long it mines")

    for ax in axes:
        ax.axhline(services.MIN_PROVIDERS, color="#e34948", linewidth=1.4, zorder=4,
                   linestyle=(0, (2, 2)))
        # Left-aligned and above the line: the legends sit on the right of both panels, and
        # a right-aligned annotation landed on top of them.
        ax.text(ax.get_xlim()[0], services.MIN_PROVIDERS * 1.06,
                "  32 — below this the stream pays nothing",
                color="#e34948", fontsize=8, va="bottom", ha="left")
        _thousands(ax, "y")
    fig.tight_layout(rect=(0, 0.10, 1, 0.88))
    p = out / "provider_ramp.png"
    fig.savefig(p, dpi=170, facecolor=SURFACE)
    plt.close(fig)
    return p


def elevation_and_depletion(cfg, out: Path, epochs: int = 400) -> Path:
    """What the pool spends, and what that spending buys.

    Left: the pool drains on a fixed clock. The three curves are three miner populations
    differing fiftyfold and they lie on top of one another, because the difficulty controller
    holds the claim count at target -- so the payout is a property of the POOL and not of
    demand. Nothing anyone does makes it drain faster or slower.

    Right: what that identical spend converts into. Bonded miners who keep mining take claims
    from miners still trying to cross, and retiring them is worth more than four times as many
    elevations out of exactly the same money.
    """
    import matplotlib.pyplot as plt
    from . import elevation as el

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))
    R0 = cfg.to_lgo(cfg.genesis_pool)

    for i, rate in enumerate((1, 50, 250)):
        r = el.run(cfg, el.ElevationConfig(miners_per_epoch=rate, epochs=epochs))
        axes[0].plot([x.epoch for x in r.rows], [x.pool_lgo / R0 * 100 for x in r.rows],
                     color=list(SERIES.values())[i], linewidth=2.4 - i * 0.6, zorder=3 + i,
                     label=f"{rate} miners/epoch", solid_capstyle="round")
    axes[0].set_xlabel("epoch", color=INK_2, fontsize=9.5)
    axes[0].set_ylabel("pool remaining, % of genesis", color=INK_2, fontsize=9.5)
    axes[0].legend(frameon=False, fontsize=9, ncol=3, loc="upper center",
                   bbox_to_anchor=(0.5, -0.22), labelcolor=INK_2)
    _style(axes[0], "The pool drains on a fixed clock",
           "three populations, fiftyfold apart — one curve")

    for i, retire in enumerate((False, True)):
        r = el.run(cfg, el.ElevationConfig(miners_per_epoch=100, epochs=epochs,
                                           retire_on_bond=retire))
        axes[1].plot([x.epoch for x in r.rows], [x.miners_elevated for x in r.rows],
                     color=list(SERIES.values())[i + 3], linewidth=2, zorder=3,
                     label="bonded miners retire" if retire else "bonded miners keep mining",
                     solid_capstyle="round")
    axes[1].axhline(cfg.genesis_pool / cfg.min_stake, color="#e34948", linewidth=1.4,
                    linestyle=(0, (2, 2)), zorder=4)
    axes[1].text(0, cfg.genesis_pool / cfg.min_stake * 0.94,
                 "  50,000 — the pool over the bond, the arithmetic ceiling",
                 color="#e34948", fontsize=8, va="top", ha="left")
    axes[1].set_xlabel("epoch", color=INK_2, fontsize=9.5)
    axes[1].set_ylabel("miners elevated to the bond", color=INK_2, fontsize=9.5)
    axes[1].legend(frameon=False, fontsize=9, ncol=2, loc="upper center",
                   bbox_to_anchor=(0.5, -0.22), labelcolor=INK_2)
    _thousands(axes[1], "y")
    _style(axes[1], "What the same spend buys",
           "identical money, four times the elevations")

    fig.tight_layout(rect=(0, 0.10, 1, 0.88), w_pad=4.0)
    p = out / "elevation_depletion.png"
    fig.savefig(p, dpi=170, facecolor=SURFACE)
    plt.close(fig)
    return p


def difficulty_control(cfg, out: Path, epochs: int = 200) -> Path:
    """The difficulty controller, and why it makes the pool's drain unstoppable.

    This is the causal link the other figures leave implicit. Left: the field's search power
    and the work one claim costs, rising together over three orders of magnitude — the
    controller tracking the load. Right: the consequence, which is that the claim count does
    not move at all.

    Because the pool pays a fixed reward per claim and the controller fixes the number of
    claims, the pool's outflow is fixed too. That is the whole reason depletion turned out to
    be independent of demand: the difficulty absorbs every bit of the load variation before it
    can reach the pool.
    """
    import matplotlib.pyplot as plt
    from . import elevation as el
    from .config import FIELD_MODULUS

    r = el.run(cfg, el.ElevationConfig(miners_per_epoch=50, epochs=epochs))
    x = [q.epoch for q in r.rows]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6))

    axes[0].plot(x, [q.hashrate for q in r.rows], color=SERIES[st.Strategy.MINER],
                 linewidth=2, zorder=3, label="search power of the field", solid_capstyle="round")
    axes[0].plot(x, [FIELD_MODULUS / q.difficulty_target for q in r.rows],
                 color=SERIES[st.Strategy.MINER_STAKER], linewidth=2, zorder=3,
                 label="candidates one claim costs", solid_capstyle="round")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("epoch", color=INK_2, fontsize=9.5)
    axes[0].set_ylabel("candidates", color=INK_2, fontsize=9.5)
    axes[0].legend(frameon=False, fontsize=9, ncol=1, loc="upper center",
                   bbox_to_anchor=(0.5, -0.22), labelcolor=INK_2)
    _style(axes[0], "The difficulty follows the load",
           "as miners arrive, the work a claim costs rises to match")

    claims = [q.claims_paid for q in r.rows]
    axes[1].plot(x, claims, color=SERIES[st.Strategy.MINER_STAKER_SERVICE], linewidth=2,
                 zorder=3, label="claims actually paid", solid_capstyle="round")
    tgt = cfg.target_claims_per_block * cfg.blocks_per_epoch
    axes[1].axhline(tgt, color=INK_2, linewidth=1.4, linestyle=(0, (4, 3)), zorder=4)
    axes[1].text(x[len(x) // 2], tgt * 1.001, "target: 10 claims a block", color=INK_2,
                 fontsize=8.5, va="bottom", ha="center")
    axes[1].set_ylim(tgt * 0.99, tgt * 1.01)
    axes[1].set_xlabel("epoch", color=INK_2, fontsize=9.5)
    axes[1].set_ylabel("claims paid per epoch", color=INK_2, fontsize=9.5)
    axes[1].legend(frameon=False, fontsize=9, loc="upper center",
                   bbox_to_anchor=(0.5, -0.22), labelcolor=INK_2)
    _thousands(axes[1], "y")
    _style(axes[1], "So the payout does not move",
           f"a {r.rows[-1].hashrate / r.rows[0].hashrate:,.0f}-fold change in load, "
           f"and the claim count is flat")

    fig.tight_layout(rect=(0, 0.10, 1, 0.88), w_pad=4.0)
    p = out / "difficulty_control.png"
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
              provider_ramp(cfg, out), difficulty_control(cfg, out),
              elevation_and_depletion(cfg, out),
              pow_distributions(cfg, rows, out)):
        print(f"  wrote {p}")

    print("\n  regenerate with:")
    print(f"    python3 -m empowering_sim.plots_strategies --out {args.out} "
          f"--epochs {args.epochs} --nodes {args.nodes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
