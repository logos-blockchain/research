"""Extra readings and self-checks, from the cache where it holds them.

    python extra.py

1. The pair (f, share) handed to pair_bounds reproduces the lottery of each state: the coalition's
   and the honest stake's chance of a slot, computed from the stakes and the inferred stake.
2. Tables A and B with more digits, the waits in slots.
3. Table A with the factor of the undisturbed state (F, s, 10 s) on every state's curve.
4. Table A with 2^63 evaluations a nonce (2^64 over the two nonces together).
5. Whether the chance falls with the wait and rises with the share, and the factor with the share.
"""

from __future__ import annotations

import math

import numpy as np

import common as c
from main import FLOOR, S_A, SHARES, T_A
from report import ENDS, WINDOWS, crossing, log_chance, the_curve, the_grind

from finality_sim.grinding import factors, pair_bounds  # noqa: E402
from finality_sim.recovery import occupancy  # noqa: E402


def lottery(state: int, s: float) -> tuple[float, float]:
    """The coalition's and the honest stake's chance of a slot, from the stakes themselves."""
    _, _, offline, deflated = c.STATES[state]
    honest = (1.0 - s) * (c.ONLINE if offline else 1.0)      # the honest stake online
    inferred = honest if deflated else honest + s
    return 1.0 - (1.0 - c.F) ** (s / inferred), 1.0 - (1.0 - c.F) ** (honest / inferred)


print("1. the lottery of each state against occupancy(f, share), occupancy(f, 1 - share)")
worst = 0.0
for st in range(len(c.STATES)):
    for s in SHARES:
        p = c.params(st, s)
        pa, ph = lottery(st, s)
        worst = max(worst, abs(occupancy(p["f_grind"], p["a"]) - pa),
                    abs(occupancy(p["f_grind"], 1.0 - p["a"]) - ph))
print(f"   largest difference over 7 states and 14 shares: {worst:.2e}\n")

print("2. Table A in slots, s = 0.30")
for st, (name, *_r) in enumerate(c.STATES):
    cv = the_curve(st, S_A)
    g = the_grind(st, S_A, "main")
    w = [c.wait_needed(cv, c.EPS)] + [c.wait_needed(cv, c.EPS / g[e]) for e in ENDS]
    print(f"   {name:28s} curve to {cv.size:6d}  waits {w}  hours {[round(x / 3600, 4) for x in w]}  "
          f"factor 2^{math.log2(g['two_lo']):.2f} - 2^{math.log2(g['two_hi']):.2f}")
print("\n   Table B with five decimals (lower end, upper end; 18 h then 10 h)")
for st, (name, *_r) in enumerate(c.STATES):
    cells = []
    for k, _label in WINDOWS:
        lc = [log_chance(st, s, k) for s in SHARES]
        for end in ENDS:
            lf = [math.log(the_grind(st, s, "main")[end]) for s in SHARES]
            x, note = crossing([a + b for a, b in zip(lc, lf)])
            cells.append(f"{x:.5f}{note}")
    print(f"   {name:28s} " + "  ".join(cells))

print("\n3. Table A with the undisturbed state's factor (F, s, 10 s) on every state's curve")
g0 = c.grind(c.F, S_A, 10)
for st, (name, *_r) in enumerate(c.STATES):
    cv = the_curve(st, S_A)
    w = [c.wait_needed(cv, c.EPS / g0[e]) / 3600 for e in ENDS]
    print(f"   {name:28s} {w[0]:6.2f} {w[1]:6.2f}")
print("   Table B likewise (18 h lo, hi; 10 h lo, hi)")
for st, (name, *_r) in enumerate(c.STATES):
    cells = []
    for k, _label in WINDOWS:
        lc = [log_chance(st, s, k) for s in SHARES]
        for end in ENDS:
            lf = [math.log(c.grind(c.F, s, 10)[end]) for s in SHARES]
            x, note = crossing([a + b for a, b in zip(lc, lf)])
            cells.append(f"{x:.3f}{note}")
    print(f"   {name:28s} " + "  ".join(cells))

print("\n4. Table A with 2^63 evaluations a nonce")
kw = dict(c.GRIND, budget_bits=63)
for st, (name, *_r) in enumerate(c.STATES):
    p = c.params(st, S_A)
    ts, lo1, up1, lo2, up2 = pair_bounds(p["f_grind"], p["a"], delta=p["delta"], **kw)
    lo, hi = factors(ts, lo2, up2, c.EPS)
    cv = the_curve(st, S_A)
    print(f"   {name:28s} factor {lo:.3e} - {hi:.3e}  waits {c.wait_needed(cv, c.EPS / lo) / 3600:6.2f} "
          f"{c.wait_needed(cv, c.EPS / hi) / 3600:6.2f}")

print("\n5. monotone?")
for st, (name, *_r) in enumerate(c.STATES):
    notes = []
    for s in SHARES:
        cv = the_curve(st, s)
        up = np.nonzero(np.diff(cv) > 0)[0]
        if up.size:
            notes.append(f"s={s}: the curve rises at {up.size} waits, first {up[0] + 2}, "
                         f"largest relative rise {np.max(np.diff(cv)[up] / cv[up]):.1e}")
    for k, label in WINDOWS:
        lc = [log_chance(st, s, k) for s in SHARES]
        if any(b < a for a, b in zip(lc, lc[1:])):
            notes.append(f"the chance after {label} falls with the share somewhere")
    for end in ENDS:
        v = [the_grind(st, s, "main")[end] for s in SHARES]
        if any(b < a for a, b in zip(v, v[1:])):
            notes.append(f"{end} falls with the share somewhere")
    print(f"   {name:28s} " + ("; ".join(notes) if notes else "yes"))
print(f"\n   (curves stop at the first wait whose bound is at most {FLOOR:g}; t_max {T_A} at s = {S_A})")
