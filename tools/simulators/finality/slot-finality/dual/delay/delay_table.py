"""From out/delay_range.csv: per delay, the wait needed in each case, the window in whole hours,
and the floor (no stake withholding, the same delay, chance 1e-9, the specification's formula).

Window rule (RFC-533's): the least whole number of hours that holds the share at 1e-9 with every
block up to the delay late, with a nonce that resists grinding (factor 1.21).
'both' adds the K row's second case at the same delay: a tenth of the honest stake offline.
"""
import math
import sys

sys.path.insert(0, "..")
import pandas as pd
from timing import cdf, p_of, quantile  # noqa: E402

EPS = 1e-9
t = pd.read_csv("out/delay_range.csv")


def floor_for(K, d, alpha=0.0):
    n = 0
    while 1 - cdf(n + 1, K, p_of(1 - alpha), d) <= EPS:
        n += 1
    return n


for share, a in (("third", 1 / 3), ("30 %", 0.30)):
    s = t[t.share == share].pivot(index="delay", columns="case", values="wait_h")
    print(f"\nAgainst {share}: wait needed, hours")
    print(f"{'delay':>5s} {'plain':>7s} {'nonce':>7s} {'offline':>8s} {'offl+n':>7s} {'deflated':>9s} | {'window':>6s} {'floor':>6s} | {'window, both cases':>18s} {'floor':>6s} | third withholds: median h at that floor")
    for d in s.index:
        r = s.loc[d]
        cells = " ".join(f"{r.get(c, float('nan')):{w}.2f}" for c, w in (("plain", 7), ("nonce", 7), ("offline", 8), ("offline+n", 7), ("deflated", 9)))
        out = []
        for need in (r.get("nonce"), max(r.get("nonce", float("nan")), r.get("offline+n", float("nan")))):
            if need != need:
                out.append((float("nan"), -1, float("nan")))
                continue
            Kh = math.ceil(need)
            K = Kh * 3600
            fl = floor_for(K, int(d))
            med = max(K, quantile(fl, 0.5, p_of(2 / 3), int(d))) / 3600
            out.append((Kh, fl, med))
        print(f"{int(d):5d} {cells} | {out[0][0]:5.0f}h {out[0][1]:6d} | {out[1][0]:17.0f}h {out[1][1]:6d} | {out[0][2]:.1f} / {out[1][2]:.1f}")

print("\nFloor with no stake withholding, by delay (chance 1e-9), and what a fixed window then gives")
print(f"{'delay':>5s} {'K=18h floor':>12s} {'mean blocks':>12s} {'K=10h floor':>12s} {'mean blocks':>12s}")
for d in range(5, 16):
    g = p_of(1) / (1 + p_of(1) * d)
    print(f"{d:5d} {floor_for(64800, d):12d} {g * 64800:12.0f} {floor_for(36000, d):12d} {g * 36000:12.0f}")
