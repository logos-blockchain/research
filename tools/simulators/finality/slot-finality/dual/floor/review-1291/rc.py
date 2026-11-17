# Independent recheck. Own code: mpmath exact sums for the spec formula, scipy betainc for tails.
from math import floor as fl, log, exp, lgamma
from decimal import Decimal as Dc, getcontext
from math import comb
getcontext().prec = 50
from scipy.special import betainc
from scipy.optimize import brentq
class mp:
    nstr = staticmethod(lambda x, n: f'{float(x):.{n}g}')
f = 1/30; H = 3600.0; E = 1e-9
def ps(share): return 1 - (1 - f)**share
def short_mp(n, K, D, share=1.0):          # spec formula, 50-digit decimals, exact binomials
    p = Dc(1) - (Dc(29)/Dc(30))**Dc(str(share)) if share != 1.0 else Dc(1)/Dc(30); s = K - n*D
    if s < n: return Dc(1)
    return sum(Dc(comb(s, i)) * p**i * (1-p)**(s-i) for i in range(n))
def atleast(n, slots, p):                   # P(Bin(slots,p) >= n) via regularized beta
    slots = int(slots)
    if slots < n: return 0.0
    return float(betainc(n, slots - n + 1, p))
def less(n, slots, p):
    slots = int(slots)
    if slots < n: return 1.0
    return float(betainc(slots - n + 1, n, 1 - p))
def Tcdf(n, t, p, D): return atleast(n, t - n*D, p)
def q(n, qq, p, D):                         # least t with P(T_n<=t) >= qq, linear refine after bisection
    lo, hi = 0, int(100*(n/p + n*D))
    while lo < hi:
        m = (lo+hi)//2
        if (Tcdf(n, m, p, D) >= qq) if qq < 0.9 else (less(n, m - n*D, p) <= 1-qq): hi = m
        else: lo = m+1
    return lo
def spec_floor(K, D, share=1.0):
    lo, hi = 0, K//(D+1)
    while lo < hi:
        m = (lo+hi+1)//2
        if less(m, K - m*D, ps(share)) <= E: lo = m
        else: hi = m-1
    return lo
BL = brentq(lambda d: f/(1+f*d)*64800 - 1825, 0, 30)
print("Blend D", BL)
for K, phi in ((64800, 1291), (36000, 689)):
    print(f"\n=== K={K}")
    for D in (10, 15):
        n = spec_floor(K, D); print(f" floor D={D}: {n}  P(<n)={mp.nstr(short_mp(n,K,D),5)} P(<n+1)={mp.nstr(short_mp(n+1,K,D),5)}")
    print(" phi at D=10:", mp.nstr(short_mp(phi, K, 10), 4), " mean blocks 15s:", f/(1+15*f)*K, " 1443@15s:", mp.nstr(short_mp(1443, K, 15), 4) if K == 64800 else "")
    print(" table miss / median h")
    for a in (0, .1, .2, .3, 1/3):
        row = []
        for D in (10, 12, 15, 20):
            p = ps(1-a); row.append(f"{less(phi, K-phi*D, p):.2g}, {max(K, q(phi, .5, p, D))/H:.2f}")
        print(f"  {a:.3f}: " + " | ".join(row))
    print(" missing stake before late (1e-9/1e-3/half), median/latest at a third and 0.3, phases 1-1e-9")
    for nm, D in (("15s", 15), ("10s", 10), ("blend", BL), ("wins", 0)):
        ms = []
        for e in (E, 1e-3, .5):
            g = lambda a: less(phi, K - phi*D, ps(1-a)) - e
            ms.append("none" if g(0) > 0 else f"{100*brentq(g, 0, .99, xtol=1e-12):.3f}")
        tl = [f"{a:.2f}: {max(K, q(phi, .5, ps(1-a), D))/H:.2f}/{max(K, q(phi, 1-E, ps(1-a), D))/H:.2f}" for a in (.3, 1/3)]
        ph = [100*brentq(lambda x: less(phi, hh*H - phi*D, ps(x)) - E, 0.01, 3, xtol=1e-12) for hh in (54, 72)]
        print(f"  {nm}: {ms} {tl} phases {ph[0]:.2f} {ph[1]:.2f}")
    n1 = phi + 1
    print(" cut-off side: mean days / earliest 1e-9")
    for s in (.1, .2, .25, .3, 1/3):
        print(f"  {s:.3f}: {n1/ps(s)/86400:.3f} / {q(n1, E, ps(s), 0)/86400:.3f}")
    s9 = brentq(lambda s: atleast(n1, K, ps(s)) - E, .05, .99, xtol=1e-13)
    print(f" held back side <= {s9:.6f}; minus third {s9-1/3:.6f}; minus 0.3 {s9-.3:.6f}; P at s=0.5: {atleast(n1, K, ps(.5)):.3g}; with phi (not phi+1): {brentq(lambda s: atleast(phi, K, ps(s)) - E, .05, .99):.6f}")
    print(f" side 0.6 mean days {n1/ps(.6)/86400:.3f}")
    print(f" halves: {phi/ps(.5)/H:.2f} h none, {phi*(1/ps(.5)+BL)/H:.2f} h blend; with phi+1: {n1/ps(.5)/H:.2f}, {n1*(1/ps(.5)+BL)/H:.2f}; days blend {phi*(1/ps(.5)+BL)/86400:.3f}")
    # eclipse, full minimisation over the start, mean rates
    for a in (.3, 1/3):
        pa, ph_ = ps(a), ps(1-a); out = []
        for D in (0, BL, 10, 15):
            best = None
            for te in range(0, 6*K, 10):
                hb = te/(1/ph_ + D)
                if te >= K and hb >= phi: break       # divergence child immutable
                need = max(n1, fl(hb) + 1)
                tf = max(need/pa, K)
                d = tf - te
                if best is None or d < best[0]: best = (d, te)
            out.append(f"D={D:.3g}: {best[0]/H:.2f} h (start {best[1]/H:.1f} h)")
        print(f" eclipse a={a:.3f}: " + "; ".join(out))
    for hh in (54, 72):
        x = brentq(lambda x: ps(x)*hh*H - phi, 0.001, 3); print(f" {hh} h phase mean rates: {100*x:.2f} %  (k=2160: {100*brentq(lambda x: ps(x)*hh*H - 2160, 0.001, 3):.2f} %)")
    print(f" 2160 blocks eclipse (a third, no delay): {(2161/ps(1/3) - 2160/ps(2/3))/H:.1f} h")
    if K == 64800:
        g = lambda a: less(phi, K - phi*15, ps(1-a)) - E
        print(" coalition that makes 15 s late at 1e-9:", brentq(g, 0, .5, xtol=1e-14))
