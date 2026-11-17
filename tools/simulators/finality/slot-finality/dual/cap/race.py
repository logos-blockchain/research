"""Mean-rate picture of the deflation attack (floor model: a gap is the delay plus a geometric wait).
The coalition (share a) builds in private with no delay; the honest stake builds the public chain.
Normal: inferred stake D = 1. Deflated: D = 1 - a, every threshold 1 / (1 - a) times higher.
Usage: python race.py > out/race.txt
"""
F, K = 1 / 30, 64800


def p(share, scale=1.0):
    return 1 - (1 - F) ** (share * scale)


for name, a in (("a third", 1 / 3), ("30 %", 0.30)):
    for d in (10, 12, 15):
        for state, sc in (("normal", 1.0), ("deflated", 1 / (1 - a))):
            ph, pa = p(1 - a, sc), p(a, sc)
            honest = K / (d + 1 / ph)
            adv = K * pa
            print(f"{name:8s} {d:2d} s {state:9s}: honest slots/slot {ph:.5f} ({ph / F:.3f} f), public chain blocks in 18 h {honest:7.0f}, "
                  f"coalition wins in 18 h {adv:6.0f}, honest lead {honest / adv - 1:6.1%}, hours to 2,160 public blocks {2160 * (d + 1 / ph) / 3600:5.1f}")
print()
print("hours for the honest chain (deflated: slots at f) to make n blocks, gap = d + 30 s")
for d, ns in ((10, (2935, 1468)), (12, (4193, 2097)), (15, (7829, 3915))):
    print(f"  {d} s: " + ", ".join(f"{n}: {n * (d + 30) / 3600:.1f} h" for n in ns))
print("healthy chain, Blend fit 5.507 s: 2,160 blocks in %.1f h" % (2160 * (5.507 + 30) / 3600))
