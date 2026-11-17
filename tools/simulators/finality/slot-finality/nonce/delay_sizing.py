# Sizing the delay of design D1 against a finality window: the shortest delay T (on the coalition's
# fastest machine, steps of 0.1 h) whose two-nonce factor the window still absorbs at 1e-9, by the
# number E of the coalition's delay machines; and the honest computing time R * T for a speed
# ratio R (how much slower an honest node's machine is), against the 72 h (4K) from the cut-off to
# the next epoch.
# Usage: python delay_sizing.py > delay_sizing.out   (after delayed_chain.py)
import numpy as np
from delayed_chain import D1, largest_factor, name

CASES = [(1 / 3, 15, 18), (1 / 3, 10, 18), (0.30, 15, 18), (0.30, 15, 10), (0.30, 10, 10)]
ES = (1, 100, 1e4, 1e6, 1e8)
print("share | delay | window K (h) | per-nonce factor K absorbs | shortest T (h) for E = 1 | 100 | 1e4 | 1e6 | 1e8")
best = {}
for a, d, k in CASES:
    lim = largest_factor(a, d, k) ** 0.5
    m = D1(a, d)
    row = []
    for e in ES:
        t = next((h / 10 for h in range(2, 139) if m.factor(h / 10, e) <= lim), float("nan"))
        row.append(t)
        best[(a, d, k, e)] = t
    print(f"{name(a):8s} | {d:2d} s | {k:2d} | {lim:9.4g} | " + " | ".join(f"{t:4.1f}" for t in row))
print("\nhonest computing time R * T (hours); the phase from the cut-off to the next epoch is 72 h")
print("T (h) | R = 3 | 5 | 10 | largest R that fits 72 h | largest R leaving 12 h for a late change of the cut-off block and for inclusion")
for t in (3, 4.5, 6, 7.8, 9, 12):
    print(f"{t:4.1f} | {3 * t:5.1f} | {5 * t:5.1f} | {10 * t:5.1f} | {72 / t:4.1f} | {60 / t:4.1f}")
