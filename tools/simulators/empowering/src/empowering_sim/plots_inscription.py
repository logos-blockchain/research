"""Figures for the inscription target: what a claim must be worth, and what it costs to make.

Two questions, two panels each, because the storage price answers one of them and cancels out
of the other.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

from . import economics, inscription
from .config import Config

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
TRANSFER = "#2a78d6"      # the transfer's own encoding -- the floor
INSCRIPT = "#1baf7a"      # what the inscription itself adds
REWARD = "#eda100"
DANGER = "#e34948"


def _style(ax):
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK_2, labelsize=8.5)


def _fig(w, h):
    f, axes = plt.subplots(1, 2, figsize=(w, h))
    f.patch.set_facecolor(SURFACE)
    for a in axes:
        _style(a)
    return f, axes


def bundle_cost(cfg: Config, out: Path) -> Path:
    """What the bundle costs, and how much of it the inscription is actually responsible for."""
    rows = inscription.sweep(cfg)
    n = np.array([r.inscription_bytes for r in rows])
    x = np.arange(len(n))
    floor = cfg.to_lgo(cfg.tx_fee(cfg.transfer_tx_bytes, cfg.transfer_tx_gas + cfg.inscribe_gas))
    insc = np.array([cfg.to_lgo(r.bundle) - floor for r in rows])

    f, (a0, a1) = _fig(11.4, 4.3)
    a0.bar(x, [floor] * len(n), 0.62, color=TRANSFER, zorder=3, label="the transfer itself")
    a0.bar(x, insc, 0.62, bottom=[floor + 2] * len(n), color=INSCRIPT, zorder=3,
           label="the inscription")
    a0.set_xticks(x); a0.set_xticklabels([f"{v}" for v in n])
    a0.set_xlabel("inscription, bytes", color=INK_2, fontsize=9)
    a0.set_ylabel(f"bundle cost, LGO at {cfg.storage_price_lgo:g} LGO/byte", color=INK_2,
                  fontsize=9)
    a0.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    a0.set_title("A transfer's own encoding is the floor", color=INK, fontsize=10.5,
                 loc="left", pad=8)
    a0.legend(frameon=False, fontsize=8.5, labelcolor=INK_2, loc="upper left")
    for i, r in enumerate(rows):
        if r.inscription_bytes in (4, 256, 1024):
            a0.text(i, cfg.to_lgo(r.bundle) + floor * 0.06, f"{r.inscription_share:.0%}",
                    ha="center", fontsize=8, color=INK_2)

    margin = np.array([r.margin for r in rows])
    a1.axhline(1.0, color=DANGER, linewidth=1.4, zorder=4)
    a1.text(-0.35, 1.10, "below this line the steady claim no longer covers the bundle",
            color=DANGER, fontsize=8, ha="left", va="bottom")
    a1.plot(x, margin, color=REWARD, linewidth=2.0, marker="o", markersize=6, zorder=5)
    a1.set_xticks(x); a1.set_xticklabels([f"{v}" for v in n])
    a1.set_xlabel("inscription, bytes", color=INK_2, fontsize=9)
    a1.set_ylabel("steady claim / bundle", color=INK_2, fontsize=9)
    a1.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.1f}x"))
    a1.set_ylim(0, max(margin) * 1.18)
    a1.set_title(f"Every swept size is covered — 1 kB by {margin[-1]:.2f}x",
                 color=INK, fontsize=10.5, loc="left", pad=8)
    for i, dx, dy, ha in ((0, 0, 11, "center"), (len(n) - 1, -8, 13, "right")):
        a1.annotate(f"{margin[i]:.2f}x", (x[i], margin[i]), textcoords="offset points",
                    xytext=(dx, dy), ha=ha, fontsize=8.5, color=INK_2)

    f.suptitle(
        f"The fee multiple, not the storage price, sets the ceiling: "
        f"{inscription.max_inscription_bytes(cfg):,.0f} bytes",
        color=INK, fontsize=12, x=0.008, ha="left", y=0.985)
    f.tight_layout(rect=(0, 0, 1, 0.93))
    f.savefig(out, dpi=180, facecolor=SURFACE)
    plt.close(f)
    return out


def affordability(cfg: Config, out: Path) -> Path:
    """The question the storage price DOES decide: can a miner afford to claim at genesis."""
    prices = np.logspace(-9, 0.3, 260)
    data = inscription.price_sweep(cfg, prices, sizes=(1024,))
    net = np.array([cfg.to_lgo(d["genesis_net"]) for d in data])
    burn = np.array([d["burn_per_year_lgo"] / cfg.launch_supply for d in data])
    limit = inscription.affordable_storage_price(cfg)
    opening = cfg.to_lgo(economics.reward_per_claim(cfg.genesis_pool, cfg))

    f, (a0, a1) = _fig(11.4, 4.3)
    a0.axhline(0, color=INK_2, linewidth=0.9, zorder=2)
    a0.axvspan(prices[0], limit, color=INSCRIPT, alpha=0.10, zorder=1)
    a0.plot(prices, net, color=TRANSFER, linewidth=2.0, zorder=5)
    a0.axvline(limit, color=INK_2, linewidth=1.1, linestyle=(0, (4, 3)), zorder=4)
    a0.axvline(cfg.storage_price_lgo, color=DANGER, linewidth=1.6, zorder=4)
    a0.set_xscale("log"); a0.set_yscale("symlog", linthresh=0.1)
    a0.set_xlabel("storage price, LGO per byte", color=INK_2, fontsize=9)
    a0.set_ylabel("genesis claim, net of its own fee (LGO)", color=INK_2, fontsize=9)
    a0.set_title("A claim pays only below the dashed price", color=INK, fontsize=10.5,
                 loc="left", pad=8)
    a0.text(limit * 0.6, -40, f"{limit:.1e}", color=INK_2, fontsize=8, ha="right")
    a0.text(cfg.storage_price_lgo * 0.8, 3.0, "specified\n1 LGO/byte", color=DANGER,
            fontsize=8, ha="right", va="bottom")
    a0.text(prices[0] * 3, opening * 0.55, f"reward {opening:.2f} LGO", color=INK_2, fontsize=8)

    a1.axvspan(prices[0], limit, color=INSCRIPT, alpha=0.10, zorder=1)
    a1.plot(prices, burn, color=REWARD, linewidth=2.0, zorder=5)
    a1.axhline(1.0, color=DANGER, linewidth=1.4, zorder=4)
    a1.text(prices[0] * 3, 1.5, "the whole supply, every year", color=DANGER, fontsize=8)
    a1.axvline(cfg.storage_price_lgo, color=DANGER, linewidth=1.6, zorder=4)
    a1.axvline(limit, color=INK_2, linewidth=1.1, linestyle=(0, (4, 3)), zorder=4)
    a1.set_xscale("log"); a1.set_yscale("log")
    a1.set_xlabel("storage price, LGO per byte", color=INK_2, fontsize=9)
    a1.set_ylabel("fees burnt per year, as a multiple of supply", color=INK_2, fontsize=9)
    at_spec = cfg.to_lgo(cfg.blocks_per_year * cfg.txs_per_block * cfg.avg_tx_fee) \
        / cfg.launch_supply
    a1.set_title(f"At the specified price the network burns {at_spec:,.0f}x its supply a year",
                 color=INK, fontsize=10.5, loc="left", pad=8)

    f.suptitle("The storage price does not touch the steady-state margin — it decides whether "
               "bootstrap mining is affordable at all",
               color=INK, fontsize=12, x=0.008, ha="left", y=0.985)
    f.tight_layout(rect=(0, 0, 1, 0.93))
    f.savefig(out, dpi=180, facecolor=SURFACE)
    plt.close(f)
    return out


def render(cfg: Config, outdir: Path) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    return [bundle_cost(cfg, outdir / "inscription_bundle.png"),
            affordability(cfg, outdir / "inscription_affordability.png")]
