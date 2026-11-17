"""Item 4: can the attack (lower bound) at depth K exceed the code's upper curve at 2K?
If lb(K) > ub_code(2K) anywhere, 'paper's count = code's curve at 2n' is refuted."""
import renv, math
import numpy as np
from finality_sim.lcbounds import slot_pdf, ub_curve, error_lb
worst = (9e9, None)
for adv in (0.02, 0.05, 0.1, 0.2, 0.25, 0.3, 1/3, 0.4, 0.45):
    for D in (0.001, 0.01, 1/30, 0.1, 0.25, 1/3, 0.5, 1.0):
        g = math.exp(-(1-adv)*D)
        A = max(10, math.ceil(math.log(1e-10)/math.log(1-g))+1)
        A = min(A, 24)
        S = max(30, A+1)
        sp = slot_pdf(1-adv, D, A)
        ub = ub_curve(64, sp, A, S)
        row = []
        for K in (1, 2, 3, 5, 8, 12, 16, 24, 32):
            lb = error_lb(K, sp, A, S)
            r2 = ub[2*K-1]/lb if lb > 0 else float('inf')
            r1 = ub[K-1]/lb if lb > 0 else float('inf')
            row.append((K, r1, r2))
            if r2 < worst[0]:
                worst = (r2, (adv, D, K, lb, ub[2*K-1], ub[K-1]))
        print(f"adv {adv:.3f} D {D:.3f} A {A}: " + " ".join(f"K{K}:{r1:.3g}/{r2:.3g}" for K, r1, r2 in row), flush=True)
print("smallest ub_code(2K)/lb(K):", worst)
