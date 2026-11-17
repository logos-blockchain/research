# Figures of RFC-532 v3 and RFC-533 v3:
# the lucky attempt of the eclipse, the depth rule's medians while a third withholds, the days a
# smaller side needs, the wins of a 1 % attacker in the part of a shifted range that reaches the
# floor, and the floor in blocks on the specification's Blend.
# Model: that of the specification's Finality Floor. A gap between blocks is a delay of D slots
# plus a geometric wait at p = 1 - (1 - f)^share, so P(T_n <= t) = P(Binomial(t - n*D, p) >= n).
import math

from scipy.stats import binom

f, H, DAY = 1 / 30, 3600.0, 86400.0


def p_of(share):
    return 1 - (1 - f) ** share


def cdf(n, t, p, D):
    s = int(t - n * D)
    return 0.0 if s < n else float(binom.sf(n - 1, s, p))


def quantile(n, q, p, D):
    lo, hi = 0, int(50 * (n / p + n * D)) + 10
    while lo < hi:
        mid = (lo + hi) // 2
        if cdf(n, mid, p, D) >= q:
            hi = mid
        else:
            lo = mid + 1
    return lo


def blend_delay(K=64800):
    # one delay per block, fitted so that K slots hold 1,825 blocks with all of the stake building
    lo, hi = 0.0, 30.0
    for _ in range(80):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if p_of(1.0) / (1 + p_of(1.0) * mid) * K > 1825 else (lo, mid)
    return (lo + hi) / 2


B = blend_delay()


def eclipse(n, a, D, K, fork_time=None):
    """Least eclipse at mean rates: the node holds the honest chain up to te, the fork needs
    n + 1 blocks, more than the node holds, and its first block K old."""
    pa, ph = p_of(a), p_of(1 - a)
    g = 1 / ph + D
    best = (1e18, None)
    for te in range(0, 4 * K, 10):
        hb = te / g
        if te >= K and hb >= n:
            break
        need = max(n + 1, math.floor(hb) + 1)
        tf = need / pa if fork_time is None else fork_time(need)
        d = max(tf, K) - te
        if d < best[0]:
            best = (d, te)
    return best


def lucky(a, q=1e-3):
    memo = {}

    def ft(need):
        if need not in memo:
            memo[need] = quantile(need, q, p_of(a), 0)
        return memo[need]
    return ft


def needed_share(blocks, hours):
    lo, hi = 0.0, 3.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if p_of(mid) * hours * H >= blocks else (mid, hi)
    return hi


print(f"Blend fit: {B:.4f} slots per block")
for K, phi, a in ((64800, 1291, 1 / 3), (64800, 1019, 1 / 3), (36000, 689, 0.3), (36000, 560, 0.3)):
    row = []
    for name, D in (("no delay", 0), ("Blend fit", B), ("10 s", 10), ("15 s", 15)):
        d, te = eclipse(phi, a, D, K)
        dl, tel = eclipse(phi, a, D, K, lucky(a))
        row.append(f"{name}: {d / H:.2f} h, lucky 1 in 1,000: {dl / H:.2f} h")
    print(f"eclipse, K = {K}, floor {phi}, fork of {a:.3f}: " + "; ".join(row))
for a in (1 / 3, 0.3):
    pa, ph = p_of(a), p_of(1 - a)
    print(f"depth rule, 2,161 blocks against 2,160, fork of {a:.3f}: no delay {(2161 / pa - 2160 / ph) / H:.2f} h, "
          f"Blend fit {(2161 / pa - 2160 * (1 / ph + B)) / H:.2f} h, 10 s {(2161 / pa - 2160 * (1 / ph + 10)) / H:.2f} h, "
          f"growth factor 0.845 {(2161 / pa - 2160 / (ph * 0.845)) / H:.2f} h")
for a, name in ((1 / 3, "a third"), (0.3, "0.3")):
    for D in (0, 10, 15):
        p = p_of(1 - a)
        qs = [quantile(2160, q, p, D) / H for q in (0.5, 1 - 1e-9)]
        print(f"depth rule while {name} withholds, {D} s: 2,160 blocks take median {qs[0]:.2f} h, latest {qs[1]:.2f} h")
print("depth rule, all stake: 2,160 blocks take median "
      + ", ".join(f"{quantile(2160, 0.5, p_of(1), D) / H:.2f} h at {D} s" for D in (0, 10, 15)))
for phi in (1291, 689):
    n1 = phi + 1
    for s in (0.1, 0.12, 0.15, 0.2, 0.25, 0.3, 1 / 3, 0.4, 0.45, 0.5, 0.6):
        print(f"floor {phi}: a side of {s:.3f} makes {n1} blocks after {n1 / p_of(s) / DAY:.3f} days on average, "
              f"{quantile(n1, 1e-9, p_of(s), 0) / DAY:.3f} at the earliest")
print(f"depth rule: 2,161 blocks take a third {2161 / p_of(1 / 3) / DAY:.2f} days, a tenth {2161 / p_of(0.1) / DAY:.2f}, "
      f"0.3 {2161 / p_of(0.3) / DAY:.2f}; a half {2160 / p_of(0.5) / H:.2f} h")
p1 = p_of(0.01)
print(f"1 % of stake: first win after {1 / p1 / 60:.1f} minutes on average")
for phi in (1291, 689, 1019, 560):
    part = (phi - 1) * 30
    print(f"floor {phi}: the part of a shifted range that reaches the floor is the last {part} slots at mean rates; "
          f"1 % of stake wins {part * p1:.1f} times in it; the floor is {phi * 30 / H:.2f} h of slots at f, "
          f"{phi * 1825 / 2160:.0f} blocks on the specification's Blend")
for K, phi in ((64800, 1291), (36000, 689)):
    for hh in (54, 72):
        print(f"K = {K}, floor {phi}: the {hh} h phase at mean rates needs {100 * needed_share(phi, hh):.2f} % of the "
              f"inferred stake building (2,160 blocks: {100 * needed_share(2160, hh):.2f} %)")
for K, phi in ((64800, 1291), (36000, 689)):
    print(f"K = {K}: with all of the stake building, K slots hold {K / (30 + B):.0f} blocks on the Blend fit, "
          f"{K / 45:.0f} at 15 s, {K / 40:.0f} at 10 s; a half makes {phi} blocks after {phi / p_of(0.5) / H:.2f} h (no delay), "
          f"{phi * (1 / p_of(0.5) + B) / H:.2f} h (Blend fit); medians {quantile(phi, 0.5, p_of(0.5), 0) / H:.2f}, "
          f"{quantile(phi, 0.5, p_of(0.5), B) / H:.2f} h; correction read (mean days of a tenth - 3)/4.5 = "
          f"{((phi + 1) / p_of(0.1) / DAY - 3) / 4.5:.3f}")
