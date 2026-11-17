"""Reviewer's own mean-rate arithmetic (items 1, 2)."""
import math
F, K, k = 1/30, 64800, 2160
def p(share): return 1 - (1 - F) ** share
print("ITEM 1")
for name, a in (("third", 1/3), ("30%", 0.3)):
    for d in (10, 12, 15):
        for st, sc in (("normal", 1.0), ("deflated", 1/(1-a))):
            ph, pa = p((1-a)*sc), p(a*sc)
            gap = d + 1/ph
            print(f"{name} {d}s {st}: occupied {ph/F:.3f}f honest {K/gap:.1f} coal {K*pa:.1f} lead {K/gap/(K*pa)-1:.1%} h_to_2160 {k*gap/3600:.2f}")
for d in (10, 15, 5.507):
    print(f"healthy all build {d}s: {K/(d+30):.1f} blocks, 2160 in {k*(d+30)/3600:.2f} h")
# deflation steps with beta = 1: D' = D * rate/f
D = 1.0
for n in range(1, 5):
    D = D * p((2/3)/D) / F
    print(f"D after {n} withheld windows (no cap) {D:.5f} speed {1/D:.4f}")
D = 1.0
for n in range(1, 4):
    D = D * p(0.7/D) / F
    print(f"30%: D after {n} {D:.5f} speed {1/D:.4f}")
print("cost of blocks: steady state vs normal earnings: third", 1-0.4*1.5, "30%", 1-0.4/0.7, "; vs possible 0.6")
print("\nITEM 2 epochs until 1/D_n > s")
lim = {15: 1.03, 14: 1.17, 13: 1.32, 12: 1.49}
for c in (None, 0.10, 0.05, 0.02, 0.01):
    row = []
    for d in (15, 14, 13, 12):
        n = 0; Dn = 1.0
        while True:
            n += 1
            Dn = 2/3 if c is None else max(2/3, (1-c)**n)
            if 1/Dn > lim[d]: break
            if n > 10000: n = None; break
        row.append(f"{d}s:{n} ({n*7.5:.0f} d)")
    print(c, row)
for d, s in lim.items():
    print(d, "cap for 49 epochs:", f"{1 - s**(-1/49):.4%}", " 48 epochs:", f"{1 - s**(-1/48):.4%}")
print("15 s with limit 1.037 (interpolated):", f"{1 - 1.037**(-1/49):.4%}")
# floor late
miss = math.log(1 - 1/(K/1291 - 15)) / math.log(1 - F)
print("share below which 1291 chain blocks are missed at 15 s:", miss)
for m in (0.850, miss):
    for c in (None, 0.10, 0.02, 0.01):
        row = []
        for x in (0.2, 1/3, 0.5):
            n = 0; late = 0
            while True:
                Dn = (1.0 if n == 0 else (1-x)) if c is None else max(1-x, (1-c)**n)
                if (1-x)/Dn < m: late += 1; n += 1
                else: break
            row.append(f"x={x:.2f}:{late} ({late*7.5:.1f} d)")
        print(f"miss {m:.4f} cap {c}: {row}")
print("\ndefl-need hours")
for d, ns in ((10, (1468, 2935, 722, 1443)), (12, (2097, 4193, 944, 1887)), (15, (3915, 7829, 1483, 2966))):
    print(d, [f"{n}:{n*(d+30)/3600:.2f}" for n in ns])
print("ratios", 3915/2160, 7829/2160)
print("mean hours whole stake to 2160 slots, scale 1.5:", 2160/p(1.5)/3600, " 1/0.7:", 2160/p(1/0.7)/3600)
