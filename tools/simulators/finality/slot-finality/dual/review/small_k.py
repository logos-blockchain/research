import renv
from finality_sim.lcbounds import slot_pdf, ub_curve, error_lb
for adv in (0.005, 0.01, 0.02, 0.04):
    sp = slot_pdf(1-adv, 1e-4, 10)
    ub = ub_curve(12, sp, 10, 30)
    lbs = [error_lb(K, sp, 10, 30) for K in (1, 2, 3, 4)]
    print(f"adv {adv}: ub1..8 " + " ".join(f"{x:.4g}" for x in ub[:8]) + " | lb1..4 " + " ".join(f"{x:.4g}" for x in lbs)
          + " | lb/adv^j: " + " ".join(f"{lbs[j]/adv**(j+1):.3g}" for j in range(4)))
