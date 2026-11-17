"""The epoch's own waits with the new floors: the building stake, as a share of the inferred
stake D, below which a value is not final in time. Times: 54 h (the snapshot's phase, 3 U),
72 h (from the nonce's and D's cut-off to the first slot of the next epoch, 4 U), 180 h (from
the snapshot to its first use, 10 U). 'median' = half of the time; 'sure' = chance 1 - 1e-9.
Counts: every win (delay 0) and chain blocks only at 15 s."""
import sys

sys.path.insert(0, "..")
from timing import H, cdf, p_of  # noqa: E402

EPS = 1e-9


def need(n, hours, D, q):
    lo, hi = 0.0, 3.0
    for _ in range(60):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if cdf(n, hours * H, p_of(mid), D) >= q else (mid, hi)
    return 100 * hi


for K, phi in ((64800, 1291), (36000, 689), (64800, 1019), (36000, 560)):
    print(f"\nfloor {phi} (K = {K}); depth 2,160 for comparison")
    for hours in (54, 72, 180):
        row = []
        for n, name in ((phi, "floor"), (2160, "depth")):
            row.append(f"{name}: median {need(n, hours, 0, 0.5):4.1f} to {need(n, hours, 15, 0.5):4.1f} %, sure {need(n, hours, 0, 1 - EPS):4.1f} to {need(n, hours, 15, 1 - EPS):4.1f} %")
        print(f"  within {hours:3d} h -> " + " | ".join(row))
