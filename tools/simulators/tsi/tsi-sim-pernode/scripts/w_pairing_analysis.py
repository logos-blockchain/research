"""Where does the parent-anchored window reach parity with today's recipe? (§6.12)

Reads a `pref-window-anchor*` sweep and answers one question: the smallest `W` at which the
parent-anchored rule is no longer resolvably worse than what the spec does today (uncle-anchored,
`W` = 10).

Everything here is PAIRED. The sweep runs under `paired_streams`, so at a given replicate every
cell shares the stake vector, the peering graph and the lottery — the window rule is the only
difference — and the statistic is the per-replicate difference against the reference cell, not a
difference of two independently-noisy means. Unpaired, none of these differences resolve.

Two things are reported that a bare mean would hide:

  * **the crossing, with its uncertainty** — the smallest `W` whose paired difference is not
    resolvably negative (`t > -2`), plus a linear interpolation of where the difference actually
    reaches zero, so "12" can be read as a grid point rather than a physical constant;
  * **how many replicates ran an off-label adversary** — a Pareto draw can leave `adversary_frac`
    unreachable (one holder above the target), which `engine._adversary_mask` warns about. Those
    replicates run a WEAKER adversary than the label, which biases an attacked arm toward the
    honest baseline. It is conservative, but a sweep quoting levels has to say how many.

Run:  python scripts/w_pairing_analysis.py [run-label-glob]
"""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from tsi_sim.config import SimConfig  # noqa: E402
from tsi_sim.engine import _adversary_mask  # noqa: E402
from tsi_sim.stake import stake_for  # noqa: E402

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"
REFERENCE = ("uncle", 10.0)      # today's recipe: the thing a change has to not cost against


def load(pattern: str) -> tuple[pd.DataFrame, str]:
    src = sorted(RUNS.glob(f"*_{pattern}/results.parquet"))
    if not src:
        raise SystemExit(f"no run matching *_{pattern}/results.parquet under {RUNS}")
    df = pd.read_parquet(src[-1])
    return df[df.epoch >= df.epochs.iloc[0] // 2], src[-1].parent.name


def off_label_replicates(df: pd.DataFrame) -> tuple[list[int], dict[int, float]]:
    """Replicates whose stake draw cannot realise `adversary_frac` (see module docstring)."""
    row = df.iloc[0]
    off, got = [], {}
    for rep in sorted(df.replicate.unique()):
        cfg = SimConfig(n_nodes=int(row.n_nodes), stake_dist=str(row.stake_dist),
                        topology=str(row.topology), degree=int(row.degree),
                        link_latency_mean=float(row.link_latency_mean),
                        link_latency_dist=str(row.link_latency_dist),
                        blend_hops=int(row.blend_hops), blend_delay_max=float(row.blend_delay_max),
                        max_uncles=int(row.max_uncles), uncle_strategy=str(row.uncle_strategy),
                        init_dest=str(row.init_dest), k=int(row.k), epochs=int(row.epochs),
                        f=float(row.f), genesis_d_factor=float(row.genesis_d_factor),
                        adversary_frac=float(row.adversary_frac),
                        adversary_strategy=str(row.adversary_strategy), paired_streams=True,
                        window_absorption=float(row.window_absorption), replicate=int(rep))
        stake = stake_for(cfg)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            mask = _adversary_mask(cfg, stake)
            if any("not reachable" in str(c.message) for c in caught):
                off.append(int(rep))
        got[int(rep)] = float(stake[mask].sum() / stake.sum())
    return off, got


def main() -> None:
    pattern = sys.argv[1] if len(sys.argv) > 1 else "pref-window-anchor-fine"
    t, label = load(pattern)
    cell = t.groupby(["uncle_window_anchor", "window_absorption", "replicate"]).agg(
        r=("mean_ratio", "mean"), p=("p_ref", "mean"))
    base = cell.loc[REFERENCE[0]].loc[REFERENCE[1]]
    windows = sorted(t.window_absorption.unique())
    reps = t.replicate.nunique()

    print(f"=== {label} ===")
    print(f"{reps} replicates, {len(windows)} windows, {int(t.epochs.iloc[0])} epochs, "
          f"paired against {REFERENCE[0]}-anchored W = {REFERENCE[1]:.0f}\n")

    off, got = off_label_replicates(t)
    if off:
        print(f"!! {len(off)}/{reps} replicates ran an OFF-LABEL adversary (unreachable on their "
              f"stake draw): {off}")
        print(f"   realised {[round(got[r], 3) for r in off]} against a "
              f"{t.adversary_frac.iloc[0]:.2f} label — weaker, so the attacked arms are "
              f"conservative.\n")
    else:
        print(f"all {reps} replicates on-label "
              f"(realised {min(got.values()):.4f}–{max(got.values()):.4f})\n")

    def table(keep: set[int] | None, title: str) -> pd.DataFrame:
        """Paired table over a replicate subset; `keep=None` means all of them."""
        rows = []
        print(f"\n--- {title} ---")
        print(f"{'anchor':>7} {'W':>6} | {'D_hat/D':>17} | {'paired diff vs today':>24} "
              f"{'t':>7} | {'p_ref':>7}")
        for anchor in ("uncle", "parent"):
            for w in windows:
                g = cell.loc[anchor].loc[w]
                i = g.index.intersection(base.index)
                if keep is not None:
                    i = i[[r in keep for r in i]]
                d = g.r[i] - base.r[i]
                tt = d.mean() / d.sem() if d.std(ddof=1) > 0 else float("nan")
                rows.append(dict(anchor=anchor, W=float(w), gap=d.mean(), stderr=d.sem(),
                                 tstat=tt, ratio=g.r[i].mean(), p_ref=g.p[i].mean()))
                tag = " <- today" if (anchor, w) == REFERENCE else ""
                print(f"{anchor:>7} {w:6.1f} | {g.r[i].mean():10.5f}+-{g.r[i].sem():.5f} | "
                      f"{d.mean():+15.5f}+-{d.sem():.5f} {tt:7.2f} | {g.p[i].mean():7.4f}{tag}")
        return pd.DataFrame(rows)

    def parity(res: pd.DataFrame, base_p: float) -> float | None:
        """Smallest W not resolvably worse than today, with the interpolated zero crossing.

        Deliberately asymmetric: the claim is "adopting the anchor costs nothing against today",
        so the burden is on ruling out a LOSS, not on proving equality.
        """
        par = res[res.anchor == "parent"].sort_values("W")
        ok = par[par.tstat > -2.0]
        if ok.empty:
            print("  no window in this grid reaches parity — widen W past the grid.")
            return None
        first = ok.iloc[0]
        print(f"  PARITY at W = {first.W:g}: {first.gap:+.5f} +- {first.stderr:.5f} "
              f"(t = {first.tstat:.2f}), p_ref {first.p_ref:.4f} vs {base_p:.4f} today.")
        below = par[par.W < first.W]
        if not below.empty:
            last = below.iloc[-1]
            print(f"  W = {last.W:g} is still resolvably worse: {last.gap:+.5f} +- "
                  f"{last.stderr:.5f} (t = {last.tstat:.2f}).")
            if first.gap != last.gap:
                cross = last.W + (0 - last.gap) * (first.W - last.W) / (first.gap - last.gap)
                print(f"  interpolated zero crossing: W = {cross:.2f}")
        return float(first.W)

    all_reps = set(int(r) for r in t.replicate.unique())
    res_all = table(None, f"all {len(all_reps)} replicates")
    w_all = parity(res_all, base.p.mean())

    if off:
        # Off-label replicates ran a WEAKER adversary, so their paired difference sits near zero
        # and drags every cell toward parity — which would make the crossing look SMALLER than it
        # is. The clean subset is the headline; the full set is the robustness check.
        keep = all_reps - set(off)
        res_clean = table(keep, f"on-label replicates only ({len(keep)} of {len(all_reps)})")
        base_clean = base.p[[r in keep for r in base.p.index]].mean()
        w_clean = parity(res_clean, base_clean)
        if w_all is not None and w_clean is not None and w_clean != w_all:
            print(f"\n!! the crossing MOVES when the off-label replicates are dropped: "
                  f"W = {w_all:g} -> W = {w_clean:g}. Quote the on-label figure.")
        else:
            print("\n  the crossing is unchanged by dropping the off-label replicates.")

    print("\nNote: the uncle-anchored column moves too — widening today's own rule helps it. The "
          "parity above is against TODAY'S recipe, which is the decision on the table, not "
          "against the same W under both anchors.")


if __name__ == "__main__":
    main()
