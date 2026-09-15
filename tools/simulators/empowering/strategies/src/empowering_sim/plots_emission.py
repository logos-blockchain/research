"""The pending-rewards-pool boundary figure — the visual behind UPSTREAM-PENDING §1.

One figure, one claim: after a fee spike falls quiet, the windowed recycled term keeps
distributing history the pool never banked, so the unguarded balance goes negative — the
`P_t >= 0` regime lips PR 375 flags for "explicit boundary treatment" — while clipping the
distribution to what the pool holds floors it at zero and self-clears as the spike rolls out
of the look-back window. Both trajectories come from `emission.Stocks`, the same class the
gate suite exercises; this module only draws what the gates already assert.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from . import emission

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"
BLUE = "#2a78d6"
DANGER = "#e34948"


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


def _trajectory(guard: bool, spike: list[float]) -> list[float]:
    s = emission.Stocks(reserve_lgo=0.0, guard_pool=guard)
    balances = []
    for i in range(1, len(spike)):
        s.step(1e10, spike[max(0, i - emission.POOL_WINDOW + 1):i + 1])
        balances.append(s.pool_lgo)
    return balances


def pool_boundary(out: Path) -> Path:
    spike = [120.0] + [0.0] * 240
    loose = _trajectory(False, spike)
    tight = _trajectory(True, spike)

    f, ax = plt.subplots(1, 1, figsize=(8.4, 4.4))
    f.patch.set_facecolor(SURFACE)
    xs = range(1, len(spike))
    ax.plot(xs, loose, color=DANGER, linewidth=2.0, zorder=5,
            label="unguarded — the specification as written")
    ax.plot(xs, tight, color=BLUE, linewidth=2.0, zorder=6,
            label="guarded — pay what the pool holds")
    ax.axhline(0, color=INK_2, linewidth=1.0, linestyle=(0, (2, 2)))
    ax.axvspan(1, emission.POOL_WINDOW, color=GRID, alpha=0.45, zorder=1)
    lowest = min(loose)
    ax.set_ylim(lowest * 1.12, 30)          # headroom so labels never sit on the data
    ax.text(emission.POOL_WINDOW / 2, 20,
            "the look-back window still remembers the spike", color=INK_2, fontsize=8,
            ha="center")
    ax.annotate(f"{lowest:.0f} LGO — a balance the spec forbids",
                xy=(len(spike) - 2, lowest), xytext=(146, -48),
                color=DANGER, fontsize=8.5,
                arrowprops=dict(arrowstyle="-", color=DANGER, linewidth=0.8))
    ax.set_xlabel("blocks since the spike", color=INK_2, fontsize=9)
    ax.set_ylabel("pending-rewards-pool balance, LGO", color=INK_2, fontsize=9)
    ax.legend(frameon=False, fontsize=8.5, loc="upper right", labelcolor=INK_2)
    _style(ax, "", "one 120-LGO fee block, then silence, at A_t = 0 with the reserve empty "
                   "— both runs conserve; only one obeys P_t ≥ 0")
    f.suptitle("The P_t ≥ 0 boundary: real, not early-life-only, and one line to fix",
               color=INK, fontsize=12.5, x=0.008, ha="left", y=0.985)
    f.tight_layout(rect=(0, 0, 1, 0.92))
    p = out / "pool_boundary.png"
    f.savefig(p, dpi=170, facecolor=SURFACE)
    plt.close(f)
    return p


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="empowering_sim.plots_emission")
    ap.add_argument("--out", default="../../../../reports/empowering/figures")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    print(f"  wrote {pool_boundary(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
