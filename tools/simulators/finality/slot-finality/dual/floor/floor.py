"""The finality floor as its own question: #532's rule (age >= K and phi occupied slots) with a
higher floor n. Model: the specification's Finality Floor (a gap between blocks = a delay D plus a
geometric wait at p = 1 - (1 - f)^share). Occupied slots are taken as blocks of the chain, which
is the cautious side for liveness (uncles only add). Exact in the model.

Usage: python floor.py [K]     K = 64800 (default, #532) or 36000 (#533)
"""
import sys

sys.path.insert(0, "..")
from timing import BLEND, H, cdf, mean, p_of, quantile  # noqa: E402

K = int(sys.argv[1]) if len(sys.argv) > 1 else 64800
EPS = 1e-9
CANDS = (1019, 1131, 1250, 1400, 1440, 1500, 1600) if K == 64800 else (560, 620, 700, 780, 800, 833, 890)
TH = 1 / 3


def bisect(fn, lo, hi, it=60):
    """Largest x in [lo, hi] with fn(x) true, fn true at lo and monotone."""
    for _ in range(it):
        mid = (lo + hi) / 2
        if fn(mid):
            lo = mid
        else:
            hi = mid
    return lo


def miss(n, share, D, k_slots=None):
    """Chance that fewer than n blocks follow a block within K slots."""
    return 1 - cdf(n, K if k_slots is None else k_slots, p_of(share), D)


def floor_for(alpha, D, eps):
    """The specification's derivation: the largest n with miss <= eps while alpha withholds."""
    n = 0
    while miss(n + 1, 1 - alpha, D) <= eps:
        n += 1
    return n


print(f"K = {K} slots ({K / H:.0f} h). Blend fit delay = {BLEND:.3f} slots.\n")
print("1. The floor the specification's derivation gives, by its targets (share that withholds, delay, chance)")
print(f"{'withholds':>10s} | " + " | ".join(f"D={d:<5} eps={e:g}" for d in ("Blend", 10, 15) for e in (1e-9, 1e-3)))
for a in (0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, TH):
    print(f"{a:10.3f} | " + " | ".join(f"{floor_for(a, D, e):18d}" for D in (BLEND, 10, 15) for e in (1e-9, 1e-3)))
print("   mean blocks in K: " + ", ".join(
    f"{a:.2f}@{dn}: {p_of(1 - a) / (1 + p_of(1 - a) * D) * K:.0f}" for a in (0, 0.1, TH) for dn, D in (("Blend", BLEND), ("10s", 10))))

print("\n2. Cost: who can delay finality past K, and by how much")
for n in CANDS:
    print(f"\n floor n = {n}")
    for dn, D in (("Blend", BLEND), ("10 s", 10), ("15 s", 15)):
        if miss(n, 1.0, D) > EPS:
            s9 = None
        else:
            s9 = 1 - bisect(lambda b: miss(n, b, D) > EPS, 0.0, 1.0)   # building share at the edge
            s9 = bisect(lambda a: miss(n, 1 - a, D) <= EPS, 0.0, 1.0)
        s3 = bisect(lambda a: miss(n, 1 - a, D) <= 1e-3, 0.0, 1.0) if miss(n, 1.0, D) <= 1e-3 else None
        s5 = bisect(lambda a: miss(n, 1 - a, D) <= 0.5, 0.0, 1.0) if miss(n, 1.0, D) <= 0.5 else None
        f = lambda v: "none" if v is None else f"{100 * v:5.1f} %"
        print(f"   {dn:5s}: stake that can be missing before finality is late with chance 1e-9: {f(s9)}, 1e-3: {f(s3)}, half the time: {f(s5)}")
    for a in (0.1, 0.2, 0.25, 0.3, TH):
        cells = []
        for dn, D in (("Blend", BLEND), ("10 s", 10)):
            p = p_of(1 - a)
            q = [max(K, quantile(n, x, p, D)) / H for x in (0.5, 1 - EPS)]
            cells.append(f"{dn}: median {q[0]:5.2f} h, latest {q[1]:5.2f} h")
        print(f"   {a:.3f} withholds or is offline -> " + " | ".join(cells))
    for ph in (54, 72):
        out = []
        for dn, D in (("no delay", 0), ("Blend", BLEND)):
            u = bisect(lambda x: cdf(n, ph * H, p_of(x), D) < 1 - EPS, 0.0, 3.0)
            out.append(f"{dn} {100 * u:.1f} %")
        print(f"   {ph} h phase needs (chance 1 - 1e-9): " + ", ".join(out))
    g = p_of(0.5) / (1 + p_of(0.5) * BLEND)
    print(f"   a block made as the building stake halves is final after {n / g / 86400:.2f} days on average (Blend)")

print("\n3. Benefit: a side cut off from the rest, an eclipse, a split")
for n in CANDS:
    print(f"\n floor n = {n}  (a side needs n + 1 = {n + 1} blocks of its own, no delay inside the side)")
    s9 = bisect(lambda s: cdf(n + 1, K, p_of(s), 0) <= EPS, 0.0, 1.0)
    s5 = bisect(lambda s: cdf(n + 1, K, p_of(s), 0) <= 0.5, 0.0, 1.0)
    print(f"   held back past K with chance 1 - 1e-9: a side of at most {s9:.3f}; a side of {s5:.3f} passes at K half the time")
    print(f"   with a third signing on both sides: a side with at most {max(0.0, s9 - TH):.3f} of honest stake is held back")
    print("   days for a side alone, mean / earliest at 1e-9: " + ", ".join(
        f"{s:.2f}: {mean(n + 1, p_of(s), 0) / 86400:.2f} / {quantile(n + 1, EPS, p_of(s), 0) / 86400:.2f}"
        for s in (0.1, 0.2, 0.25, 0.3, TH, 0.4, 0.5)))
    q = [max(K, quantile(n, x, p_of(0.5), BLEND)) / H for x in (EPS, 0.5, 1 - EPS)]
    print(f"   split in halves (Blend): each half fixes its chain after {q[0]:.1f} / {q[1]:.1f} / {q[2]:.1f} h")
    for a in (0.3, TH):
        pa, ph = p_of(a), p_of(1 - a)
        cells = []
        for dn, D in (("no delay", 0), ("Blend", BLEND), ("10 s", 10)):
            te = n * (1 / ph + D)                 # latest start: the node holds n blocks, not yet final
            te = min(te, max(te, 0))
            # the node's chain is not final while it has fewer than n blocks OR is younger than K
            # so the eclipse can also start as late as K if the fork then beats the node's chain
            best = None
            for start in (te, float(K)):
                hb = start / (1 / ph + D)
                need = max(n + 1, hb + 1)
                if start > te and hb >= n and start >= K:
                    continue
                for label, tf in (("mean", need / pa), ("lucky 1e-3", quantile(int(need) + 0, 1e-3, pa, 0))):
                    d = max(tf, K) - start
                    best = best or {}
                    best[label] = min(best.get(label, 1e18), d)
            cells.append(f"{dn}: {best['mean'] / H:5.1f} h (lucky 1e-3: {best['lucky 1e-3'] / H:5.1f} h)")
        print(f"   eclipse a prepared fork of {a:.3f} needs -> " + " | ".join(cells))
