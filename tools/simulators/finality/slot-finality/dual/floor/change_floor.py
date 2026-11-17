"""Figures a specification change to 'the floor sized with no stake withholding' would need.
Uses the specification's own formula (Finality Floor, blocks_short) with ALPHA = 0, and the
models of RFC-532's floor section (mean rates; negative binomial tails)."""
import sys
from math import exp, lgamma, log

sys.path.insert(0, "..")
from timing import BLEND, H, cdf, mean, p_of, quantile  # noqa: E402

f, EPS = 1 / 30, 1e-9
DELTA = int(sys.argv[1]) if len(sys.argv) > 1 else 10


def blocks_short(n, K, alpha, delta=DELTA):
    p_h = 1 - (1 - f) ** (1 - alpha)
    slots = K - n * delta
    if slots < n:
        return 1.0
    return sum(exp(lgamma(slots + 1) - lgamma(i + 1) - lgamma(slots - i + 1) + i * log(p_h) + (slots - i) * log(1 - p_h))
               for i in range(n))


def floor(K, alpha, delta=DELTA):
    n = 0
    while blocks_short(n + 1, K, alpha, delta) <= EPS:
        n += 1
    return n


for K in (64800, 36000):
    phi = floor(K, 0.0)
    print(f"\nK = {K}: floor with no stake withholding = {phi}; P(N < {phi}) = {blocks_short(phi, K, 0):.2e}, "
          f"P(N < {phi + 1}) = {blocks_short(phi + 1, K, 0):.2e}; with ALPHA_MAX it was {floor(K, 1/3 if K == 64800 else 0.3)}")
    print("  sizing table (share that withholds, mean blocks in K at DELTA, floor, P(N < floor)):")
    for a in (0.0, 0.1, 0.25, 0.3, 1 / 3):
        p = p_of(1 - a)
        n = floor(K, a)
        print(f"    {a:.3f}  mean {p / (1 + p * DELTA) * K:7.1f}  floor {n}  P {blocks_short(n, K, a):.1e}")
    print(f"  chance that the floor {phi} is missed at K, and mean extra wait, by delay and withholding share:")
    for a in (0.0, 0.1, 0.2, 0.3, 1 / 3):
        cells = []
        for d in (10, 12, 15, 20):
            p = p_of(1 - a)
            pm = blocks_short(phi, K, a, d)
            med = max(K, quantile(phi, 0.5, p, d))
            cells.append(f"{d} s: P {pm:.1e}, median final {med / H:.1f} h")
        print(f"    {a:.3f} withholds -> " + " | ".join(cells))
    n1 = phi + 1
    print(f"  a side cut off needs {n1} blocks: days mean / earliest at 1e-9")
    for s in (0.1, 0.2, 0.25, 0.3, 1 / 3):
        print(f"    {s:.3f}: {mean(n1, p_of(s), 0) / 86400:.2f} / {quantile(n1, EPS, p_of(s), 0) / 86400:.2f}")
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if cdf(n1, K, p_of(mid), 0) <= EPS else (lo, mid)
    print(f"  held back past K with chance 1 - 1e-9: a side of at most {lo:.3f}; honest part when a third signs on both: {lo - 1/3:.3f}")
    for s in (0.6, 0.65, 0.7):
        print(f"    a side of {s} makes {n1} blocks after {mean(n1, p_of(s), 0) / 86400:.2f} days on average")
    for a in (0.3, 1 / 3):
        pa, ph = p_of(a), p_of(1 - a)
        print(f"  eclipse a prepared fork of {a:.3f} needs (mean rates): no delay {(max(n1 / pa, K) - phi / ph) / H:.1f} h, "
              f"Blend {(max(n1 / pa, K) - phi * (1 / ph + BLEND)) / H:.1f} h, 10 s {(max(n1 / pa, K) - phi * (1 / ph + 10)) / H:.1f} h")
    for ph_h in (54, 72):
        lo, hi = 0.0, 3.0
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if p_of(mid) * ph_h * H >= phi else (mid, hi)
        print(f"  {ph_h} h phase at mean rates needs {100 * hi:.1f} % of the inferred stake building (was: phi blocks)")
    print(f"  split in halves: {phi} blocks take a half {phi / p_of(0.5) / H:.1f} h (no delay), {phi * (1 / p_of(0.5) + BLEND) / H:.1f} h (Blend)")
    g = p_of(0.5) / (1 + p_of(0.5) * BLEND)
    print(f"  a block made as the active stake halves is fixed after {phi / g / 86400:.2f} days on average (Blend)")
    print(f"  blocks above B_imm on the specification's Blend stay at about {p_of(1) / (1 + p_of(1) * BLEND) * K:.0f} (K slots hold fewer than the floor only when stake is missing)")
