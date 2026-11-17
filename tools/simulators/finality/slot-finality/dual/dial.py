"""The floor as a dial: the rule "age >= K and n blocks follow" for n from phi to k, and the
variants C and D. Floor's model (timing.py). Times in hours: earliest (1e-9), median, latest."""
from timing import BLEND, EPS, H, K, PHI, cdf, k, mean, p_of, quantile

STATES = [("normal (all build, Blend fit)", 1.0, BLEND), ("a third withholds, Blend fit", 2 / 3, BLEND),
          ("a third withholds, 10 s", 2 / 3, 10), ("a third withholds, 15 s", 2 / 3, 15),
          ("90 % online, Blend fit", 0.9, BLEND), ("split in halves, Blend fit", 0.5, BLEND)]
QS = (EPS, 0.5, 1 - EPS)

print("Rule: age >= K (18 h) and n blocks of the chain follow")
for n in (PHI, 1250, 1510, 1825, k):
    print(f"\n n = {n}")
    for name, share, D in STATES:
        p = p_of(share)
        q = [max(K, quantile(n, x, p, D)) / H for x in QS]
        miss = 1 - cdf(n, K, p, D)
        print(f"   {name:34s} {q[0]:6.2f} {q[1]:6.2f} {q[2]:6.2f}   P(not final at K) {miss:.1e}")
    pa, ph = p_of(1 / 3), p_of(2 / 3)
    print(f"   eclipse a third's prepared fork needs (mean rates, no delay): {((n + 1) / pa - n / ph) / H:5.1f} h;"
          f" a side of a third fixes its own fork after {mean(n + 1, pa, 0) / 86400:4.2f} days (mean),"
          f" {quantile(n + 1, EPS, pa, 0) / 86400:4.2f} at the earliest")
    for phase_h in (54, 72):
        lo, hi = 0.0, 3.0
        for _ in range(50):
            mid = (lo + hi) / 2
            if cdf(n, phase_h * H, p_of(mid), 0) >= 1 - EPS:
                hi = mid
            else:
                lo = mid
        print(f"   {phase_h} h phase: {100 * hi:.1f} % of the inferred stake must build (chance 1 - 1e-9)")

print("\nC: k blocks, or age >= K_cap and phi blocks.   D: k blocks and age >= K_min")
for name, share, D in STATES + [("lottery 1.5 fast, all build, Blend fit", 1.5, BLEND),
                                ("lottery 1.925 fast, all build, Blend fit", 1.925, BLEND)]:
    p = p_of(share)
    tk = [quantile(k, x, p, D) for x in QS]
    tphi = [quantile(PHI, x, p, D) for x in QS]
    out = []
    for cap in (2 * K, 3 * K):
        out.append(" ".join(f"{(a if a < cap else max(cap, b)) / H:6.2f}" for a, b in zip(tk, tphi)))
    for kmin in (36000, 45000):
        out.append(" ".join(f"{max(kmin, a) / H:6.2f}" for a in tk))
    print(f"  {name:40s} C(36 h): {out[0]} | C(54 h): {out[1]} | D(10 h): {out[2]} | D(12.5 h): {out[3]}")
