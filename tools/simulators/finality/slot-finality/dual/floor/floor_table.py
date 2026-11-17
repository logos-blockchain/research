"""The floor study's summary table, at the floors the specification's derivation gives
(Delta = 10, eps = 1e-9) for a share that withholds of: a third, 0.3, a quarter, a fifth, a tenth,
none; plus 1,500. Two ends for the count of occupied slots on the cost side:
  'blocks'  only blocks of the chain count, every block 10 s late (the worst case: an adversary can
            orphan honest blocks down to one countable uncle);
  'wins'    every lottery win of the building stake counts (blocks lost to delay return as uncles).
Benefit side: 'worst' pairs the 10 s honest chain, 'wins' pairs no delay.
Usage: python floor_table.py [K]
"""
import sys

sys.path.insert(0, "..")
from timing import H, cdf, mean, p_of, quantile  # noqa: E402

K = int(sys.argv[1]) if len(sys.argv) > 1 else 64800
EPS, TH = 1e-9, 1 / 3


def bis(fn, lo, hi):
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if fn(mid) else (lo, mid)
    return lo


def miss(n, share, D):
    return 1 - cdf(n, K, p_of(share), D)


def floor_for(alpha, D=10, eps=EPS):
    n = 0
    while miss(n + 1, 1 - alpha, D) <= eps:
        n += 1
    return n


rows = [("a third", TH), ("0.3", 0.3), ("a quarter", 0.25), ("a fifth", 0.2), ("a tenth", 0.1), ("none", 0.0)]
floors = [(name, floor_for(a)) for name, a in rows] + [("(1,500)", 1500 if K == 64800 else 833)]
print(f"K = {K}")
for name, n in floors:
    print(f"\nfloor {n}  (withholding share it is sized for: {name})")
    for end, D in (("blocks, 10 s", 10), ("wins", 0)):
        m = [bis(lambda a: miss(n, 1 - a, D) <= e, 0.0, 1.0) if miss(n, 1.0, D) <= e else None for e in (EPS, 1e-3, 0.5)]
        f = lambda v: "none" if v is None else f"{100 * v:.1f} %"
        tw = []
        for a in (0.2, 0.3, TH):
            p = p_of(1 - a)
            tw.append(f"{a:.2f}: " + " / ".join(f"{max(K, quantile(n, x, p, D)) / H:.1f}" for x in (0.5, 1 - EPS)))
        ph = [100 * bis(lambda x: cdf(n, hh * H, p_of(x), D) < 1 - EPS, 0.0, 3.0) for hh in (54, 72)]
        print(f"  cost [{end:12s}] stake missing before finality is late (1e-9 / 1e-3 / half): {f(m[0])} / {f(m[1])} / {f(m[2])};"
              f" wait median / latest h while withheld -> {'; '.join(tw)}; 54 h / 72 h phase need {ph[0]:.1f} % / {ph[1]:.1f} %")
    s9 = bis(lambda s: cdf(n + 1, K, p_of(s), 0) <= EPS, 0.0, 1.0)
    half = [max(K, quantile(n + 1, x, p_of(0.5), D)) / H for D in (10, 0) for x in (0.5,)]
    ecl = []
    for a in (0.3, TH):
        pa, ph_ = p_of(a), p_of(1 - a)
        ecl.append(f"{a:.2f}: " + " / ".join(f"{(max((n + 1) / pa, K) - n * (1 / ph_ + D)) / H:.1f}" for D in (10, 0)))
    print(f"  gain: side held back past K (1 - 1e-9) up to {s9:.3f}; with a third on both sides honest up to {max(0, s9 - TH):.3f};"
          f" split in halves median {half[0]:.1f} h (10 s) / {half[1]:.1f} h (no delay);"
          f" a third alone {mean(n + 1, p_of(TH), 0) / 86400:.2f} days mean, {quantile(n + 1, EPS, p_of(TH), 0) / 86400:.2f} earliest;"
          f" a tenth alone {mean(n + 1, p_of(0.1), 0) / 86400:.2f} days;"
          f" eclipse h, mean, per attempt (10 s / no delay) -> {'; '.join(ecl)}")
