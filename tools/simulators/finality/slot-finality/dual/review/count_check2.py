"""Quick part of count_check: small delays, all shares, depths to 40; plus B2's own cells where
runs/b2/lower.csv has the attack at depth (0.25 at 10 s: 140, 150, 216)."""
import renv, math
from finality_sim.lcbounds import slot_pdf, ub_curve, error_lb
worst = (9e9, None)
for adv in (0.1, 0.2, 0.25, 0.3, 1/3, 0.4, 0.45):
    for D in (0.001, 1/30, 1/3):
        g = math.exp(-(1-adv)*D)
        A = min(max(10, math.ceil(math.log(1e-10)/math.log(1-g))+1), 16)
        S = 30
        sp = slot_pdf(1-adv, D, A)
        ub = ub_curve(90, sp, A, S)
        out = []
        for K in (1, 2, 3, 4, 6, 10, 20, 40):
            lb = error_lb(K, sp, A, S)
            r = ub[2*K-1]/lb
            out.append(f"K{K}:{ub[K-1]/lb:.3g}/{r:.3g}")
            if r < worst[0]: worst = (r, adv, D, K, lb, ub[2*K-1])
        print(f"adv {adv:.3f} D {D:.3f}: " + " ".join(out), flush=True)
print("smallest ub_code(2K)/lb(K):", worst)
