"""Warm the numba cache and time one call of each kind."""

import time

import common as c

t0 = time.time()
from finality_sim.grinding import factors, pair_bounds  # noqa: E402
from finality_sim.waitbound import wait_curve  # noqa: E402

print(f"import {time.time() - t0:.1f} s", flush=True)

# a tiny call of each compiles everything
t0 = time.time()
w = wait_curve(2000, 0.10, 10, c.F, floor=1e-12)
print(f"small wait_curve {time.time() - t0:.1f} s, size {w.size}, c[1999]={w[min(w.size, 2000) - 1]:.3e}", flush=True)
t0 = time.time()
ts, lo1, up1, lo2, up2 = pair_bounds(c.F, 0.10, delta=10, **c.GRIND)
print(f"small pair_bounds {time.time() - t0:.1f} s", factors(ts, lo1, up1, 1e-9), factors(ts, lo2, up2, 1e-9), flush=True)

# the study's own point: worst 10 s, 0.30 (SETTLEMENT.md B6: one 3e11-2e12, two 2e15-1e19)
t0 = time.time()
ts, lo1, up1, lo2, up2 = pair_bounds(c.F, 0.30, delta=10, **c.GRIND)
print(f"pair_bounds(F, 0.30, delta=10) {time.time() - t0:.1f} s", factors(ts, lo1, up1, 1e-9), factors(ts, lo2, up2, 1e-9), flush=True)

# the study's own point: 0.30 at 10 s, chance after 64,800 slots 9.4e-28, wait 5.9 h
t0 = time.time()
w = wait_curve(64800, 0.30, 10, c.F, floor=1e-55)
print(f"wait_curve(64800, 0.30, 10) {time.time() - t0:.1f} s, size {w.size}, c[64799]={w[-1]:.3e}, "
      f"wait {c.wait_needed(w, 1e-9)} slots = {c.wait_needed(w, 1e-9) / 3600:.2f} h", flush=True)
