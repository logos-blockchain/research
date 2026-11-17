"""Reviewer's independent recomputation of timing.py / dial.py figures.
Model (from the description, not from timing.py): gap between chain blocks = D slots + Geometric(p)
(support 1,2,...), p = 1-(1-f)^share.  T_n = n*D + sum of n geometrics.
Methods: (a) scipy nbinom quantiles (sum of n geometrics = n + NegBin(n,p)), (b) direct Monte Carlo
with geometric draws, (c) normal approximation with skew correction (Cornish-Fisher) for 1e-9."""
import math, sys
import numpy as np
from scipy.stats import nbinom, norm
from scipy.optimize import brentq

f, k, K, PHI = 1/30, 2160, 64800, 1019
H = 3600.0
EPS = 1e-9
rng = np.random.default_rng(20261117)

def p_of(s): return 1-(1-f)**s

# Blend fit: K slots hold 1825 blocks at mean rate: K/(1/p + D) = 1825
p1 = p_of(1.0)
BLEND = K/1825 - 1/p1
print(f"BLEND fit D = {BLEND:.4f} slots (mine)")

def q_exact(n, q, p, D):
    """least integer t with P(n*D + n + NB <= t) >= q"""
    g = nbinom.ppf(q, n, p)          # least g with cdf >= q   (failures)
    return math.ceil(n*D + n + g - 1e-9)

def q_cf(n, q, p, D):
    """Cornish-Fisher (2 terms) quantile of n*D + sum geometrics."""
    mu = n/p; var = n*(1-p)/p**2; sk = (2-p)/math.sqrt(n*(1-p))
    z = norm.ppf(q) if q < 0.5 else -norm.ppf(1-q) if q > 0.5 else 0.0
    if q > 0.5: z = norm.isf(1-q)
    w = z + (z*z-1)*sk/6
    return n*D + mu + math.sqrt(var)*w

def q_mc(n, qs, p, D, N=20000):
    t = np.zeros(N)
    for i in range(0, N, 2000):
        t[i:i+2000] = rng.geometric(p, size=(2000, n)).sum(axis=1)
    t += n*D
    return [float(np.quantile(t, q)) for q in qs], t

def row(name, share, D, n=k, mc=True):
    p = p_of(share)
    ex = [q_exact(n, q, p, D)/H for q in (EPS, 0.5, 1-EPS)]
    cf = [q_cf(n, q, p, D)/H for q in (EPS, 0.5, 1-EPS)]
    s = f"{name:48s} n={n} exact {ex[0]:6.2f} {ex[1]:6.2f} {ex[2]:6.2f} | CF {cf[0]:6.2f} {cf[1]:6.2f} {cf[2]:6.2f}"
    if mc:
        (m1, m5, m9), t = q_mc(n, (1e-3, 0.5, 1-1e-3), p, D)
        e3 = [q_exact(n, q, p, D)/H for q in (1e-3, 1-1e-3)]
        s += f" | MC med {m5/H:6.2f} q1e-3 {m1/H:6.2f}/{m9/H:6.2f} (exact {e3[0]:6.2f}/{e3[1]:6.2f})"
    print(s, flush=True)
    return ex

print("\n== DEPTH quantiles (earliest 1e-9, median, latest 1-1e-9), hours ==")
row("normal: share 1, Blend fit", 1.0, BLEND)
row("a third withholds, 10 s", 2/3, 10)
row("a third withholds, Blend fit", 2/3, BLEND)
row("30 % withholds, Blend", 0.7, BLEND)
row("a third withholds, 15 s", 2/3, 15)
row("half, Blend", 0.5, BLEND)
row("whole stake, no delay", 1.0, 0)
row("lottery 1.5, no delay", 1.5, 0)
row("lottery 1.925, no delay", 1.925, 0)
row("lottery 1/0.7, no delay", 1/0.7, 0)
row("lottery 1.25, no delay", 1.25, 0)
row("lottery 1.5, Blend", 1.5, BLEND)
row("lottery 1.925, Blend", 1.925, BLEND)
print("\n== floor phi ==")
row("a third withholds, 15 s, phi", 2/3, 15, n=PHI)
row("half, Blend, phi", 0.5, BLEND, n=PHI)
row("a third withholds, 10 s, phi", 2/3, 10, n=PHI)

print("\n== A_occ (age>=K and k occupied; occupied = every winning slot, no delay), share 1 ==")
ex = [q_exact(k, q, p_of(1.0), 0) for q in (EPS, 0.5, 1-EPS)]
print("   T_k(no delay) h:", [round(x/H, 2) for x in ex], " -> max(K,.) :", [round(max(K, x)/H, 2) for x in ex])
# direct MC with Bernoulli slots for the median of max(K, T)
N = 4000
wins = rng.random((N, 80000)) < p_of(1.0)
cs = wins.cumsum(axis=1)
tk = (cs >= k).argmax(axis=1) + 1
print(f"   Bernoulli-slot MC: median T_k {np.median(tk)/H:.2f} h, mean {tk.mean()/H:.3f} h, P(T_k<=K) {np.mean(tk<=K):.3f}, median max(K,T) {np.median(np.maximum(K,tk))/H:.2f}")
del wins, cs

print("\n== P(floor missed at K) for a third at 10 s: P(T_phi > K) ==")
p = p_of(2/3)
for D in (10, 15, 20):
    s = int(K - PHI*D)
    from scipy.stats import binom
    print(f"   D={D}: {binom.cdf(PHI-1, s, p):.3e}")

print("\n== Epoch-phase participation (share s.t. P(T_n <= phase) >= q) ==")
def need_share(n, phase, q, D):
    def g(s):
        p = p_of(s)
        fails = phase - n*D - n
        return nbinom.cdf(math.floor(fails), n, p) - q
    return brentq(g, 0.01, 3.0, xtol=1e-9)
for phase_h in (54, 72):
    for lab, n in (("k", k), ("phi", PHI)):
        for D, dn in ((0, "no delay"), (BLEND, "Blend fit"), (10, "10 s")):
            a = need_share(n, phase_h*H, 0.5, D); b = need_share(n, phase_h*H, 1-EPS, D)
            print(f"   phase {phase_h} h, {lab:3s}, {dn:9s}: median {100*a:5.1f} %  at 1-1e-9 {100*b:5.1f} %")

print("\n== Eclipse (mean rates). te = start of eclipse after fork point; honest gap = 1/ph + Dh ==")
def eclipse(a, rule, Dh, step=10):
    pa, ph = p_of(a), p_of(1-a)
    best = None
    for te in range(0, 4*K, step):
        hb = te/(1/ph + Dh)
        final = {"DEPTH": hb >= k, "SLOT": te >= K and hb >= PHI, "A": te >= K and hb >= k,
                 "B": hb >= k or (te >= K and hb >= PHI)}[rule]
        if final: break
        # fork: needs > hb blocks and to pass the rule; time for n blocks = n/pa
        need_blocks = {"DEPTH": k+1, "SLOT": PHI+1, "A": k+1, "B": PHI+1}[rule]
        need_age = {"DEPTH": 0, "SLOT": K, "A": K, "B": K}[rule]
        cands = []
        t1 = max(max(math.floor(hb)+1, need_blocks)/pa, need_age)
        cands.append(t1)
        if rule == "B":   # or the depth leg alone
            cands.append(max(math.floor(hb)+1, k+1)/pa)
        t = min(cands)
        d = t - te
        if best is None or d < best[0]: best = (d, te, t)
    return best
for a in (0.3, 1/3):
    for Dh, dn in ((0, "no delay"), (BLEND, "Blend fit"), (10, "10 s")):
        print(f"   a={a:.3f} honest {dn:9s}: " + "  ".join(
            f"{r} {eclipse(a, r, Dh)[0]/H:5.1f} h (te {eclipse(a, r, Dh)[1]/H:5.1f})" for r in ("DEPTH", "SLOT", "A", "B")))

print("\n== dial rows spot check: age>=K and n blocks, a third withholds 10 s ==")
for n in (1019, 1250, 1510, 1825, 2160):
    p = p_of(2/3)
    ex = [max(K, q_exact(n, q, p, 10))/H for q in (EPS, 0.5, 1-EPS)]
    pa, ph = p_of(1/3), p_of(2/3)
    print(f"   n={n}: {ex[0]:6.2f} {ex[1]:6.2f} {ex[2]:6.2f}  eclipse formula {((n+1)/pa - n/ph)/H:5.1f} h; own fork {(n+1)/pa/86400:.2f} d")
