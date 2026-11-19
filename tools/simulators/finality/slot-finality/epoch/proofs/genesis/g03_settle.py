"""GENESIS.md, sections 6.3, 6.4 and 7: the settlement bound U(w) of the finality study at the waits
that the proofs read.

U(w) is finality_sim.waitbound.wait_curve: the study's bound on P(mu_l >= 0 at some time >= l + w) in
the model of Gazi, Ren and Russell (ePrint 2022/1571), in slots. U_(Delta + 1) is the same curve at a
delay of Delta + 1 slots.
Prints, per share and delay: U(s_gen - 1) (statement 6.3), U(K - 2) and U_(Delta + 1)(K - 1) for both K
(statement 7.2), the least window s with U(s - 1) <= 1e-9 beside the study's stored wait, and the
estimate of section 6.4: the study's lower-bound depths of GRR's section 4.7 attack at 1e-6 and 1e-9
(runs/k1/worst.csv, columns lb_depth, lb_extrapolated, clock_s and lb_h_estimate; copied to
runs/k7/worst.csv), a log-linear line through the two points read at s_gen, and U(s_gen - 1) over it.
Usage: python g03_settle.py > out_03_settle.txt   (first run computes and caches the curves)
"""
import csv
import os

from common_g import ALPHAS, DELTAS, EPS, H, K_CASES, S_GEN, U_at, pct, settle_cached

T_MAX = 160_000
RUNS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "runs", "")   # tools/simulators/finality/runs/


def least(curve, eps):
    for w in range(1, len(curve) + 1):
        if curve[w - 1] <= eps:
            return w
    return None


if __name__ == "__main__":
    k7, k1 = {}, {}
    with open(RUNS + "k7/worst.csv") as fh:
        for r in csv.DictReader(fh):
            k7[(round(float(r["alpha"]), 6), int(float(r["delta_s"])))] = r
    with open(RUNS + "k1/worst.csv") as fh:
        for r in csv.DictReader(fh):
            k1[(round(float(r["alpha"]), 6), int(float(r["delay_s"])), float(r["eps"]))] = r
    print(f"U(w): the study's bound on a wait of w slots (waitbound.wait_curve, slots), t_max = {T_MAX}")
    for a in ALPHAS:
        for d in DELTAS:
            c = settle_cached(a, d, T_MAX)
            c1 = settle_cached(a, d + 1, T_MAX)
            lw = least(c, EPS)
            print(f"\n{pct(a)}, Delta = {d}")
            print("  U(w): " + "; ".join(f"w = {w}: {U_at(c, w):.3e}" for w in
                                         (8_000, 12_000, S_GEN, 20_000, 30_000, 36_000 - 1,
                                          50_000, 64_800 - 1)))
            print(f"  U(s_gen - 1) = U({S_GEN - 1}) = {U_at(c, S_GEN - 1):.3e}; U(s_gen) = {U_at(c, S_GEN):.3e}")
            for name, K in K_CASES.items():
                print(f"  {name}: U(K - 2) = U({K - 2}) = {U_at(c, K - 2):.3e}; "
                      f"U_(Delta + 1)(K - 1) = U_{d + 1}({K - 1}) = {U_at(c1, K - 1):.3e}")
            r = k7.get((round(a, 6), d))
            print(f"  least s with U(s - 1) <= 1e-9: {lw + 1} slots = {(lw + 1) / H:.2f} h; the study's stored wait at 1e-9 "
                  f"(runs/k7/worst.csv, wait_1e-09): {int(r['wait_1e-09'])} slots, the least w with U(w) <= 1e-9: {lw}")
            pts = {}
            for eps in (1e-6, 1e-9):
                q = k1[(round(a, 6), d, eps)]
                pts[eps] = float(q["lb_h_estimate"])
                print(f"  attack of GRR 4.7 at {eps:g} (runs/k1/worst.csv): lower-bound depth {float(q['lb_depth']):.1f} blocks, "
                      f"extended: {q['lb_extrapolated']}; at {float(q['clock_s']):.2f} s a block: {pts[eps]:.2f} h "
                      f"(runs/k7/worst.csv attack_h_{eps:g} = {float(r[f'attack_h_{eps:g}']):.2f} h)")
            h6, h9 = pts[1e-6], pts[1e-9]
            lg = -6 - 3 * (S_GEN / H - h6) / (h9 - h6)
            inside = "inside" if min(h6, h9) <= S_GEN / H <= max(h6, h9) else "outside"
            print(f"  the line through the two points at s_gen = {S_GEN / H:g} h ({inside} them): about 10^{lg:.2f} = "
                  f"{10 ** lg:.1e}; U(s_gen - 1) / estimate = {U_at(c, S_GEN - 1) / 10 ** lg:.0f}")
