"""Phase K, K.3: splits and eclipses when finality is counted in slots (SLOTS.md).

    python scripts/k3_splits.py       # needs runs/a1 and runs/b2; writes runs/k3/*.csv; about a minute

With ``B_imm`` the latest block at least ``K`` slots old, a node fixes its chain once a block the
rest of the network lacks is ``K`` slots old. The candidates are ``K = ⌊k/f⌋`` and
``K = 3⌊k/f⌋``, and K.1's least ``K`` against a third under the worst case at 10 s. A density floor
``φ`` holds ``B_imm`` back until ``φ`` blocks of the local chain follow it (src/finality_sim/floor.py):

- horizon.csv: the self-healing horizon in blocks (MAPPING.md §5) beside ``K``; with the floor at
  ``3⌊k/f⌋``, the earliest a side fixes its chain at one block per occupied slot, under the depth
  form and under the density form, its inference corrected at the next epoch when that comes
  sooner; the density form also at the engine's growth of two even sides;
- eclipse.csv: when an eclipsed node fixes the chain it is shown, made by a share ``σ``: counted in
  blocks, in slots, and in slots with either form of the floor; mean, the ``ε``-early time, and
  the mean once the eclipsed chain's inference corrects at the next epoch;
- floor.csv: the floor for each ``K``, ``α_max`` and delay model; what it costs on a chain nobody
  withholds from; the largest side that stays provisional;
- quorum.csv: the least ``K`` at which a floor separates the sides of every partition while the
  honest chain the coalition withholds from still finalizes, beside H.1's seats;
- detector.csv: H.1's detector over a window of ``K``;
- bootstrap.csv: the Bootstrap rule's window, the offline grace margin and rule 5's cap against ``K``,
  with the epoch at today's length.
"""

from __future__ import annotations

import math
import pathlib

import numpy as np
import pandas as pd

from finality_sim.floor import (after_correction, blocks_time, chain_rate, density_fix,
                                floor_for, least_quorum_window, log_short, provisional_share,
                                quorum)
from finality_sim.further import attestation_seats, detector_power
from finality_sim.recovery import occupancy
from finality_sim.slots import worst_needed

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "k3"
F = 1 / 30
EPS = 1e-9
DELTA = 10
KS = (2160, 1620, 1080, 432, 216, 120)
SHARES = (0.5, 0.3, 0.2)
SIGMAS = (0.001, 0.01, 0.05, 0.10, 0.20, 0.25, 0.30, 1 / 3)
ALPHAS = (0.25, 0.30, 1 / 3)
T_OFFLINE = 20 * 60
SIDE_GROWTH = 0.863          # the fastest a side grew per occupied slot on the engine (I.3)
EVEN_GROWTH = 0.80           # two even sides grew at 0.80 per occupied slot on the engine (I.3)
SIDES = (0.35, 0.50, 0.57, 0.60, 0.65, 0.70)


def growth() -> float:
    s = pd.read_csv(HERE / "runs" / "a1" / "summary.csv")
    return float(s[(s.family == "rounds") & (s.link_latency_mean == 0.1) & (s.blend_hops == 3)
                   & (s.blend_delay_max == 3)].growth_per_f.iloc[0])


def least_k_third() -> int:
    u = pd.read_parquet(HERE / "runs" / "b2" / "ub.parquet")
    c = u[np.isclose(u.adv, 1 / 3) & (u.delay_s == DELTA)].sort_values("depth")
    return worst_needed(1 / 3, EPS, DELTA, np.log(np.minimum(c.ub.to_numpy(), 1.0)))


def models(g: float) -> dict[str, dict]:
    return {"random, specification": dict(growth=g), f"worst, {DELTA} s": dict(delta=DELTA)}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    g = growth()
    k1 = least_k_third()
    windows = {"⌊k/f⌋": int(2160 / F), "K.1's least against a third at 10 s": k1,
               "3⌊k/f⌋": 3 * int(2160 / F)}
    k_s = 3 * int(2160 / F)
    epoch = 10 * int(2160 / F)
    # the floor a protocol takes at K = 3⌊k/f⌋: live under the worst case against a third
    phi_s = floor_for(k_s, 1 / 3, EPS, F, delta=DELTA)
    phi_1 = floor_for(int(2160 / F), 1 / 3, EPS, F, delta=DELTA)

    rows = []
    for k in KS:
        kf = int(k / F)
        phi = floor_for(3 * kf, 1 / 3, EPS, F, delta=DELTA)
        for s in SHARES:
            lr, fix = density_fix(s, phi, 3 * kf, epoch, EPS)
            lr_engine, fix_engine = density_fix(s, phi, 3 * kf, epoch, EPS, growth=EVEN_GROWTH)
            rows.append(dict(k=k, share=s, blocks_h=k / occupancy(F, s) / 3600,
                             k_slots_h=kf / 3600, k3_slots_h=3 * kf / 3600, phi_k3=phi,
                             depth_floor_k3_h=max(3 * kf,
                                                  after_correction(phi + 1, s, epoch)) / 3600,
                             density_log10_reach=lr, density_floor_k3_h=fix / 3600,
                             density_log10_reach_engine=lr_engine,
                             density_floor_k3_engine_h=fix_engine / 3600))
    pd.DataFrame(rows).to_csv(OUT / "horizon.csv", index=False)

    rows = []
    for sig in SIGMAS:
        p = occupancy(F, sig)
        b_mean, b_early = blocks_time(2161, sig, EPS)
        f1_mean, f1_early = blocks_time(phi_1 + 1, sig, EPS)
        fs_mean, fs_early = blocks_time(phi_s + 1, sig, EPS)
        rows.append(dict(
            sigma=sig, first_block_h=1 / p / 3600,
            blocks_mean_h=b_mean / 3600, blocks_early_h=b_early / 3600,
            blocks_corrected_h=after_correction(2161, sig, epoch) / 3600,
            slots_k1_h=(int(2160 / F) + 1 / p) / 3600, slots_k3_h=(k_s + 1 / p) / 3600,
            floor_k1_mean_h=max(int(2160 / F) + 1 / p, f1_mean) / 3600,
            floor_k1_early_h=max(int(2160 / F), f1_early) / 3600,
            floor_k1_corrected_h=max(int(2160 / F) + 1 / p,
                                     after_correction(phi_1 + 1, sig, epoch)) / 3600,
            floor_k3_mean_h=max(k_s + 1 / p, fs_mean) / 3600,
            floor_k3_early_h=max(k_s, fs_early) / 3600,
            floor_k3_corrected_h=max(k_s + 1 / p, after_correction(phi_s + 1, sig, epoch)) / 3600,
            density_k1_log10_reach=density_fix(sig, phi_1, int(2160 / F), epoch, EPS)[0],
            density_k1_h=density_fix(sig, phi_1, int(2160 / F), epoch, EPS)[1] / 3600,
            density_k3_log10_reach=density_fix(sig, phi_s, k_s, epoch, EPS)[0],
            density_k3_h=density_fix(sig, phi_s, k_s, epoch, EPS)[1] / 3600,
            phi_k1=phi_1, phi_k3=phi_s))
    pd.DataFrame(rows).to_csv(OUT / "eclipse.csv", index=False)

    rows = []
    for name, w in windows.items():
        for a in ALPHAS:
            for mname, kw in models(g).items():
                phi = floor_for(w, a, EPS, F, **kw)
                full = log_short(w, phi, 1.0, F, **kw)
                attacked = log_short(w, phi, 1.0 - a, F, **kw)
                prov = provisional_share(w, phi, EPS)
                rows.append(dict(window=name, slots=w, hours=w / 3600, alpha=a, model=mname,
                                 phi=phi, expected=w * chain_rate(1.0 - a, F, **kw),
                                 log10_wait_full=full / math.log(10),
                                 log10_wait_attacked=attacked / math.log(10),
                                 provisional_share=prov, provisional_honest=prov - a))
    pd.DataFrame(rows).to_csv(OUT / "floor.csv", index=False)

    variants = {
        "random, the side at one block per occupied slot": dict(live_growth=g, side_growth=1.0),
        f"random, the side at {SIDE_GROWTH}": dict(live_growth=g, side_growth=SIDE_GROWTH),
        "worst, 1 s": dict(live_delta=1), "worst, 5 s": dict(live_delta=5),
        "worst, 10 s": dict(live_delta=10),
    }
    rows = []
    for a in (0.20, 0.25, 0.30, 1 / 3):
        seats, theta = attestation_seats(a, EPS, 1e-6)
        for vname, kw in variants.items():
            live_rate = chain_rate(1.0 - a, F, kw.get("live_growth"), kw.get("live_delta"))
            side_rate = chain_rate((1.0 + a) / 2, F, growth=kw["side_growth"]
                                   if "side_growth" in kw else 1.0)
            w = least_quorum_window(a, EPS, F, **kw)
            live_s, safe_s = quorum(k_s, a, EPS, F, **kw)
            rows.append(dict(alpha=a, variant=vname, live_rate=live_rate, side_rate=side_rate,
                             least_slots=w if w is not None else -1,
                             least_days=w / 86400 if w is not None else math.nan,
                             phi_at_least=quorum(w, a, EPS, F, **kw)[0] if w is not None else -1,
                             phi_live_k3=live_s, phi_safe_k3=safe_s, h1_seats=seats))
    pd.DataFrame(rows).to_csv(OUT / "quorum.csv", index=False)

    rows = []
    for name in ("⌊k/f⌋", "3⌊k/f⌋"):
        w = windows[name]
        for a in (0.30, 1 / 3):
            thr, powers = detector_power(a, g, w, EPS, SIDES)
            rows.append(dict(window=name, hours=w / 3600, alpha=a, threshold=thr,
                             expected=w * g * occupancy(F, 1.0 - a),
                             **{f"side_{s:.2f}": pw for s, pw in zip(SIDES, powers)},
                             whole_honest=detector_power(a, g, w, EPS, [1.0 - a])[1][0]))
    pd.DataFrame(rows).to_csv(OUT / "detector.csv", index=False)

    rw = pd.read_csv(HERE / "runs" / "b5" / "recovery_window.csv")
    third = rw[np.isclose(rw.alpha, 1 / 3, atol=4e-3)]
    rows = []
    for k in KS:
        kf = int(k / F)
        rows.append(dict(k=k, s_gen_h=int(k / (4 * F)) / 3600,
                         window_random_h=float(third[third.model == "random, specification"]
                                               ["window_h_1e-09"].iloc[0]),
                         window_worst_h=float(third[third.model == "worst, 10 s"]
                                              ["window_h_1e-09"].iloc[0]),
                         k1_h=kf / 3600, k3_h=3 * kf / 3600, rule5_cap_h=4 * int(2160 / F) / 3600,
                         margin_k1=kf / T_OFFLINE, margin_k3=3 * kf / T_OFFLINE))
    pd.DataFrame(rows).to_csv(OUT / "bootstrap.csv", index=False)
    print(f"floor at 3⌊k/f⌋ against a third, worst case at {DELTA} s: {phi_s}; K.1's least: {k1}")


if __name__ == "__main__":
    main()
