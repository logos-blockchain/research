"""SLOTS.md K.3's tables, read from runs/k3 (scripts/k3_splits.py); tables.py dispatches k3* here."""

from __future__ import annotations

import math
import pathlib

import pandas as pd

RUNS = pathlib.Path(__file__).resolve().parent.parent / "runs" / "k3"


def md(df: pd.DataFrame) -> str:
    cols = [str(c) for c in df.columns]
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(v) for v in r.to_list()) + " |")
    return "\n".join(out)


def share(v: float) -> str:
    return "a third" if abs(v - 1 / 3) < 1e-6 else f"{v:.3f}".rstrip("0").rstrip(".")


def h(v: float) -> str:
    return "–" if math.isnan(v) else f"{v:,.1f}"


def d(v: float) -> str:
    return "–" if math.isnan(v) else (f"{v:,.0f}" if v >= 100 else f"{v:,.1f}" if v >= 10
                                      else f"{v:.2f}")


def p10(v: float) -> str:
    if v == -math.inf or v < -99:
        return "< 1e-99"
    if v > -0.01:
        return "1"
    e = math.floor(v)
    m = round(10 ** (v - e))
    if m == 10:
        m, e = 1, e + 1
    return f"{m}e{e}"


def k3horizon() -> None:
    t = pd.read_csv(RUNS / "horizon.csv")
    print(md(pd.DataFrame({
        "k": t.k, "side's share": t.share.map(share),
        "in blocks, today (h)": t.blocks_h.map(h),
        "slots, K = ⌊k/f⌋ (h)": t.k_slots_h.map(h), "slots, K = 3⌊k/f⌋ (h)": t.k3_slots_h.map(h),
        "floor φ at 3⌊k/f⌋": t.phi_k3.map(lambda v: f"{v:,}"),
        "depth form (h)": t.depth_floor_k3_h.map(h),
        "density form (h)": t.density_floor_k3_h.map(h),
        "density form, the side at 0.80 (h)": t.density_floor_k3_engine_h.map(h)})))


def k3eclipse() -> None:
    t = pd.read_csv(RUNS / "eclipse.csv")
    print(md(pd.DataFrame({
        "σ": t.sigma.map(share),
        "in blocks, k = 2160 (days)": (t.blocks_corrected_h / 24).map(d),
        "slots, K = ⌊k/f⌋ (days)": (t.slots_k1_h / 24).map(d),
        "slots, K = 3⌊k/f⌋ (days)": (t.slots_k3_h / 24).map(d),
        "depth form at 3⌊k/f⌋ (days)": (t.floor_k3_corrected_h / 24).map(d),
        "density form at ⌊k/f⌋ (days)": (t.density_k1_h / 24).map(d),
        "density form at 3⌊k/f⌋ (days)": (t.density_k3_h / 24).map(d)})))


def k3early() -> None:
    t = pd.read_csv(RUNS / "eclipse.csv")
    print(md(pd.DataFrame({
        "σ": t.sigma.map(share),
        "k = 2160 blocks: mean (days)": (t.blocks_mean_h / 24).map(d),
        "k = 2160 blocks: at 1e-9 (days)": (t.blocks_early_h / 24).map(d),
        f"φ + 1 = {t.phi_k3.iloc[0] + 1:,} blocks at 3⌊k/f⌋: mean (days)": (t.floor_k3_mean_h / 24).map(d),
        "the same at 1e-9 (days)": (t.floor_k3_early_h / 24).map(d)})))


def k3floor() -> None:
    t = pd.read_csv(RUNS / "floor.csv")
    print(md(pd.DataFrame({
        "K": [f"{w}, {hh:.1f} h" for w, hh in zip(t.window, t.hours)],
        "α_max": t.alpha.map(share), "delay": t.model,
        "floor φ": t.phi.map(lambda v: f"{v:,}"),
        "withheld-from chain, mean": t.expected.map(lambda v: f"{v:,.0f}"),
        "nobody withholds: waits": t.log10_wait_full.map(p10),
        "withheld from: waits": t.log10_wait_attacked.map(p10),
        "largest side held at K": t.provisional_share.map(lambda v: f"{v:.3f}"),
        "its honest part, the coalition signing": t.provisional_honest.map(lambda v: f"{v:.3f}")})))


def k3quorum() -> None:
    t = pd.read_csv(RUNS / "quorum.csv")
    print(md(pd.DataFrame({
        "α": t.alpha.map(share), "model": t.variant,
        "honest chain withheld from, blocks per 1,000 slots": (1000 * t.live_rate).map(lambda v: f"{v:.2f}"),
        "side of (1 + α)/2, blocks per 1,000 slots": (1000 * t.side_rate).map(lambda v: f"{v:.2f}"),
        "least K (days)": [("none" if s < 0 else d(v)) for s, v in zip(t.least_slots, t.least_days)],
        "floor at it": [("–" if s < 0 else f"{v:,}") for s, v in zip(t.least_slots, t.phi_at_least)],
        "at 3⌊k/f⌋: honest tail / side tail": [f"{a:,} / {b:,}" for a, b in zip(t.phi_live_k3, t.phi_safe_k3)],
        "H.1's seats": t.h1_seats.map(lambda v: "none" if v < 0 else f"{v:,}")})))


def k3detector() -> None:
    t = pd.read_csv(RUNS / "detector.csv")
    sides = [c for c in t.columns if c.startswith("side_")]
    out = pd.DataFrame({"K": [f"{w}, {hh:.0f} h" for w, hh in zip(t.window, t.hours)],
                        "α": t.alpha.map(share),
                        "expected, honest alone": t.expected.map(lambda v: f"{v:,.0f}"),
                        "threshold": t.threshold.map(lambda v: f"{v:,}")})
    for c in sides:
        out[f"side {c[5:]}"] = t[c].map(lambda v: "1.0000" if v > 0.99995 else
                                        (f"{v:.4f}" if v >= 1e-3 else f"{v:.0e}"))
    out["the whole honest chain"] = t.whole_honest.map(lambda v: f"{v:.0e}")
    print(md(out))


def k3bootstrap() -> None:
    t = pd.read_csv(RUNS / "bootstrap.csv")
    print(md(pd.DataFrame({
        "k": t.k, "s_gen = ⌊k/4f⌋ (h)": t.s_gen_h.map(lambda v: f"{v:.2f}"),
        "window B5 needs against a third, random / worst 10 s (h)":
            [f"{a:.1f} / {b:.1f}" for a, b in zip(t.window_random_h, t.window_worst_h)],
        "K = ⌊k/f⌋ / 3⌊k/f⌋ (h)": [f"{a:.1f} / {b:.1f}" for a, b in zip(t.k1_h, t.k3_h)],
        "rule 5's cap (h)": t.rule5_cap_h.map(h),
        "K / T_offline": [f"{a:.1f} / {b:.1f}" for a, b in zip(t.margin_k1, t.margin_k3)]})))
