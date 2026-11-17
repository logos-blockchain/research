# How grinding the epoch nonce moves a coalition's share of the stake over time.
# Every staker restakes its leader rewards; a block pays the same reward whoever makes it. With the
# coalition winning (1 + g) times the blocks of its share, one epoch moves its share s to
#   s' = s (1 + rho (1 + g(s))) / (1 + rho (1 + s g(s))),   rho = leader yield a year / epochs a year.
# g(s): "mean" = the rechecked mean gain over all epochs without feedback (mean_gain.py, budget 2^16);
#       "ceiling" = the best of 2^16 nonces in every epoch (practice.py), which no coalition below
#       about 30 % can hold (compound.py) and which trades off against keeping the nonces coming.
# Usage: python stake_growth.py > stake_growth.out
import numpy as np
EPY = 365.25 * 86400 / 648_000                        # epochs a year, 48.7
S = np.array([0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 1 / 3])
MEAN = {10: np.array([0.039, 0.098, 0.159, 0.229, 0.322, 0.461, 0.698, 0.962]) / 100,
        15: np.array([0.041, 0.103, 0.168, 0.245, 0.352, 0.520, 0.821, 1.173]) / 100}
CEIL = np.array([30.2, 13.2, 9.3, 7.6, 6.5, 5.8, 5.3, 5.0]) / 100
BLOCKS = np.array([220, 1098, 2193, 3287, 4379, 5469, 6557, 7282.0])

def g(s, tab):
    return float(np.interp(s, S, tab))                # held flat above a third

def run(s0, y, tab, years):
    s, rho, out = s0, y / EPY, {}
    for e in range(1, int(round(max(years) * EPY)) + 1):
        gg = g(s, tab)
        s = s * (1 + rho * (1 + gg)) / (1 + rho * (1 + s * gg))
        for yr in years:
            if e == int(round(yr * EPY)):
                out[yr] = s
    return out

YEARS = (1, 5, 10, 20, 50)
print(f"epochs a year {EPY:.1f}; years {YEARS} are epochs {[int(round(v * EPY)) for v in YEARS]}")
print("extra blocks a year (mean gain 10 s / 15 s; ceiling):")
for i, s in enumerate(S):
    print(f"  {100 * s:5.1f} % | {BLOCKS[i] * EPY:9.0f} by share | +{BLOCKS[i] * MEAN[10][i] * EPY:6.0f} / +{BLOCKS[i] * MEAN[15][i] * EPY:6.0f} | +{BLOCKS[i] * CEIL[i] * EPY:7.0f}")
for y in (0.0133, 0.04, 0.10):
    for name, tab in (("mean 10 s", MEAN[10]), ("mean 15 s", MEAN[15]), ("ceiling 2^16", CEIL)):
        print(f"leader yield {100 * y:.2f} % a year, gain: {name}")
        for s0 in (0.10, 0.20, 0.25, 0.30, 1 / 3):
            r = run(s0, y, tab, YEARS)
            print(f"  start {100 * s0:5.2f} % | " + " | ".join(f"{yr} y: {100 * r[yr]:.3f} %" for yr in YEARS)
                  + f" | first year: {100 * (r[1] - s0):+.4f} points")
