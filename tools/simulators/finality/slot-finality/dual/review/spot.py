"""Spot-check rows of out/bounds_cases.csv by calling the study's functions directly,
written from the study's scripts (b2_settlement.upper, k7_wait.need), not from bounds.py."""
import renv, math, time
import numpy as np
from finality_sim.lcbounds import slot_pdf, ub_curve
from finality_sim.waitbound import wait_curve, wait_needed, alphabet_for
F = 1/30
def depth(adv, d, kmax=6000, floor=1e-14):
    a = alphabet_for(adv, d)
    return ub_curve(kmax, slot_pdf(1-adv, d, a), a, max(30, a+1), 1e-16, floor)
def first(c, eps):
    h = np.nonzero(c <= eps)[0]; return int(h[0])+1 if h.size else -1
for lab, adv, delta, scale in (("third 10 s", 1/3, 10, 1.0), ("third 13 s", 1/3, 13, 1.0), ("third 10 s deflated", 1/3, 10, 1.5),
                               ("third 20 s", 1/3, 20, 1.0)):
    t = time.time()
    c = depth(adv, F*scale*delta)
    s = depth(adv, -math.log(1-F)*scale*(delta+1))
    g = lambda cu, n: float(cu[n-1]) if n <= cu.size else 0.0
    print(f"{lab:22s} cont need {first(c,1e-9)} at2160 {g(c,2160):.3e} at4320 {g(c,4320):.3e} | slot need {first(s,1e-9)} at2160 {g(s,2160):.3e} at4320 {g(s,4320):.3e}  ({time.time()-t:.0f}s)", flush=True)
t = time.time()
w = wait_curve(70000, 1/3, 10, F, floor=1e-10)
print("wait third 10 s need", wait_needed(w, 1e-9), "at 36000", w[35999], f"({time.time()-t:.0f}s)", flush=True)
w = wait_curve(70000, 1/3, 10, F, floor=1e-15, scale=1.5)
print("wait third 10 s deflated need", wait_needed(w, 1e-9), "at 64800", w[64799] if w.size >= 64800 else "<floor", f"({time.time()-t:.0f}s)", flush=True)
