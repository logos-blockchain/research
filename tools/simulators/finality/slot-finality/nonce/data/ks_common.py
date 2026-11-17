# Shared settings for the shorter-K study runs. The study's code is that of fast-finalization-slots
# at 741dc0b (its waitbound, grinding, slots modules are unchanged since b2ff076).
# Usage: imported by ks_curves.py, ../repro/recheck.py and ../repro/accept_bias.py.
import math
import sys

import numpy as np

F = 1 / 30
EPS = 1e-9
HOURS = (8, 9, 10, 11, 12, 12.5, 18)
KS = {h: int(round(h * 3600)) for h in HOURS}          # slots of 1 s
GRID = np.append(np.round(np.arange(0.05, 1 / 3, 0.005), 4), 1 / 3)   # B5's grid (b5_what_k_holds)
WGRID = np.append(np.round(np.arange(0.05, 1 / 3, 0.01), 4), 1 / 3)   # B6's worst-case grid (k2_holds)
G_SPEC = 0.845        # A1's growth per f on the specification's Blend (SETTLEMENT.md B5; K.9)
T_OFF = 1200          # T_offline, 20 minutes


def add_src(path):
    if path not in sys.path:
        sys.path.insert(0, path)


def held_worst(logs, eps, ln_r=0.0):
    """b5_what_k_holds.held_worst: the largest share of GRID at which logs + ln_r stays at or below
    ln eps, linear between grid points: nan if none does, inf if a third does."""
    y = np.asarray(logs) + ln_r - math.log(eps)
    if y[0] > 0:
        return math.nan
    if y[-1] <= 0:
        return math.inf
    i = int(np.nonzero(y > 0)[0][0])
    return float(GRID[i - 1] - y[i - 1] * (GRID[i] - GRID[i - 1]) / (y[i] - y[i - 1]))


def fmt_share(v):
    if v == math.inf:
        return ">= 1/3"
    if v != v:
        return "< 0.05"
    return f"{v:.3f}"
