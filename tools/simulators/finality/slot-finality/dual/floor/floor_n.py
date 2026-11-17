"""floor_table.py's rows for given floors. Usage: python floor_n.py K n [n ...]"""
import sys
sys.argv, args = sys.argv[:1], sys.argv[1:]
sys.path.insert(0, "..")
from timing import H, cdf, mean, p_of, quantile, BLEND
K = int(args[0]); EPS, TH = 1e-9, 1 / 3
def bis(fn, lo, hi):
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if fn(mid) else (lo, mid)
    return lo
def miss(n, share, D): return 1 - cdf(n, K, p_of(share), D)
for n in map(int, args[1:]):
    print(f"\nfloor {n}, K = {K}")
    for end, D in (("blocks, 15 s", 15), ("blocks, 10 s", 10), ("blocks, Blend fit", BLEND), ("wins", 0)):
        m = [bis(lambda a: miss(n, 1 - a, D) <= e, 0.0, 1.0) if miss(n, 1.0, D) <= e else None for e in (EPS, 1e-3, 0.5)]
        f = lambda v: "none" if v is None else f"{100 * v:.1f} %"
        tw = "; ".join(f"{a:.2f}: " + " / ".join(f"{max(K, quantile(n, x, p_of(1 - a), D)) / H:.1f}" for x in (0.5, 1 - EPS)) for a in (0.1, 0.2, 0.3, TH))
        ph = [100 * bis(lambda x: cdf(n, hh * H, p_of(x), D) < 1 - EPS, 0.0, 3.0) for hh in (54, 72)]
        print(f"  cost [{end:17s}] missing before late (1e-9 / 1e-3 / half): {f(m[0])} / {f(m[1])} / {f(m[2])}; median / latest h -> {tw}; 54/72 h phase {ph[0]:.1f} % / {ph[1]:.1f} %")
    s9 = bis(lambda s: cdf(n + 1, K, p_of(s), 0) <= EPS, 0.0, 1.0)
    print(f"  gain: side held back up to {s9:.3f}; honest with a third on both {max(0, s9 - TH):.3f}; split halves median "
          + " / ".join(f"{max(K, quantile(n + 1, 0.5, p_of(0.5), D)) / H:.1f}" for D in (15, 10, 0)) + " h (15 s / 10 s / none)")
