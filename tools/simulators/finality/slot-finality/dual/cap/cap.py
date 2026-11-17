"""A cap on how far the inferred stake D may fall from one epoch to the next: D' >= (1 - c) D.
Mean rates, beta = 1 (D' = stake that built through the observation window, before the cap).
A coalition of a third withholds through every observation window (the first 6 of an epoch's
10 parts) and builds otherwise. After n windows D = max(2/3, (1 - c)^n) and the lottery runs
1 / D times fast whenever all of the stake builds.
Reads out/speed_limit.csv (the lottery speed up to which 18 h and 36 h hold a third).
Usage: python cap.py > out/cap.txt
"""
import csv
import math

EPOCH_DAYS = 7.5
ALPHA = 1 / 3
F = 1 / 30
CAPS = [0.01, 0.02, 0.03, 0.05, 0.10, 0.20, None]
MISS = 0.850          # floor 1,291 is missed at mean rates while building / D < 0.850 (15 s, chain blocks)

rows = list(csv.DictReader(open("out/speed_limit.csv")))


def limit(d, col):
    if d == 15 and col == "chance_18h":
        return 1.037      # three decimals, from blind/out/blind.txt (the grid of 0.01 gives 1.03)
    ok = [float(r["scale"]) for r in rows if int(r["delay"]) == d and float(r[col]) <= 1e-9]
    return max(ok) if ok else None


def epochs_to(target_d, c):
    """Windows of withholding until D < target_d (D starts at 1)."""
    if c is None:
        return 1
    return math.floor(math.log(target_d) / math.log(1 - c)) + 1


print("Lottery speed up to which the window holds a third (chance 1e-9, nonce unbiased; grid 0.01, up to 1.60)")
for d in range(10, 16):
    print(f"  {d} s: 18 h up to {limit(d, 'chance_18h')}, 36 h up to {limit(d, 'chance_36h')}")
print("  A third reaches 1.49 after one withheld window (D = 0.670) and 1.50 after two (0.667). At 12 s the first already fails 18 h by a hair (1.0016e-9, reviewer).")

print("\nEpochs of withholding (days) until the lottery passes the speed that 18 h holds, by cap and delay")
print("  cap/epoch | " + " | ".join(f"{d} s" for d in range(12, 16)) + " | full deflation (1.5)")
for c in CAPS:
    cells = []
    for d in range(12, 16):
        s = limit(d, "chance_18h")
        if s is None:
            cells.append("fails at 1.00")
        elif s >= 1.5:
            cells.append("never")
        else:
            n = epochs_to(1 / s, c) if (c is not None) else 1
            # the speed must exceed s: D < 1/s
            cells.append(f"{n} ({n * EPOCH_DAYS:.0f} d)")
    full = 1 if c is None else math.ceil(math.log(1 - ALPHA) / math.log(1 - c))
    print(f"  {'none' if c is None else f'{c:.0%}':9s} | " + " | ".join(cells) + f" | {full} ({full * EPOCH_DAYS:.0f} d)")

print("\nLargest cap that keeps the lottery within the 18 h limit for N epochs of withholding: c = 1 - s^(-1/N)")
for d in (13, 14, 15):
    s = limit(d, "chance_18h")
    print(f"  {d} s (limit {s}): " + ", ".join(f"N={n}: {1 - s ** (-1 / n):.2%}" for n in (1, 4, 12, 49)))

print("\nWhat the cap costs when stake leaves for good (share x of the stake stops building)")
print("  epochs until D reaches the building stake | epochs the floor of 1,291 is late (15 s, mean rates) | block rate in the first epoch")
for c in CAPS:
    cells = []
    for x in (0.1, 0.2, 1 / 3, 0.5):
        if c is None:
            n_track, n_late = 1, (1 if (1 - x) < MISS else 0)
        else:
            n_track = math.ceil(math.log(1 - x) / math.log(1 - c))
            # late while (1 - x) / D_n < MISS, D_n = max(1 - x, (1 - c)^n)
            n_late = 0 if (1 - x) >= MISS else math.ceil(math.log((1 - x) / MISS) / math.log(1 - c))
        cells.append(f"x={x:.2f}: {n_track} ep to track, floor late {n_late} ep ({n_late * EPOCH_DAYS:.0f} d)")
    print(f"  {'none' if c is None else f'{c:.0%}':5s} " + "; ".join(cells))

print("\nRule A in the deflated state (lottery 1.49 times fast, all stake builds): mean time to 2,160 chain blocks")
p = 1 - (1 - F) ** 1.49
for d in (0, 5.507, 10, 15):
    print(f"  every block {d} s late: {2160 * (d + 1 / p) / 3600:.1f} h")
print("  normal lottery:")
for d in (0, 5.507, 10, 15):
    print(f"  every block {d} s late: {2160 * (d + 1 / F) / 3600:.1f} h")
