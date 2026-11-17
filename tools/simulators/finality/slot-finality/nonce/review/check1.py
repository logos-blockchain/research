# Independent check of survival(T) and open_after(T): (A) forward DP with absorption (no value iteration,
# own code), (B) slot-level Monte Carlo in numba.
import sys, math, numpy as np
from numba import njit, prange

F = 1/30
def rates(alpha): return 1-(1-F)**alpha, 1-(1-F)**(1-alpha)

def fwd(alpha, delta, T, mode, H=120000, LO=900, HI=120):
    """P(lead>=1 at some slot in [T, T+H]). State arrays p[c][x], x index = lead+LO. mode 'block' or 'cutoff'."""
    a, h = rates(alpha)
    n = LO+HI+1
    p = np.zeros((delta+1, n))
    if mode == 'block':
        p[delta, LO] = 1.0
    else:
        # burn in the "best lead over fork points" chain: best -> max(best+win-1,0) at a block slot
        p[delta, LO] = 1.0
        for _ in range(60000):
            p = one(p, a, h, delta, LO, True)
    for t in range(T):
        p = one(p, a, h, delta, LO, False)
    hit = p[:, LO+1:].sum(); p[:, LO+1:] = 0
    for t in range(H):
        p = one(p, a, h, delta, LO, False)
        m = p[:, LO+1:].sum(); hit += m; p[:, LO+1:] = 0
        if p.sum() < 1e-25 or (t > 2000 and m < 1e-22*max(hit,1e-300)): break
    return hit

def one(p, a, h, delta, LO, floor0):
    q = np.zeros_like(p)
    for c in range(delta+1):
        row = p[c]
        w = np.zeros_like(row); w[1:] = a*row[:-1]; w += (1-a)*row      # after coalition draw (top edge mass dropped)
        if c > 0:
            q[c-1] += w
        else:
            q[0] += (1-h)*w
            d = np.zeros_like(row); d[:-1] = h*w[1:]
            if floor0:
                d[LO] += d[:LO].sum(); d[:LO] = 0     # new block is a fork point with lead 0
            q[delta] += d
    return q

@njit(parallel=True)
def mc(n, a, h, delta, T, burn, seed):
    sv = 0; op = 0
    for s in prange(n):
        np.random.seed(seed+s)
        # --- survival: start right after a canonical block
        dead = delta; lead = 0; t = 0; ok = False
        while True:
            t += 1
            if np.random.random() < a: lead += 1
            hon = np.random.random() < h
            if dead > 0: dead -= 1
            elif hon: lead -= 1; dead = delta
            if t >= T:
                if lead >= 1: ok = True; break
                if lead < -70: break
        if ok: sv += 1
        # --- open: burn in from a block, best lead over fork points, then forward
        dead = delta; best = 0
        for i in range(burn):
            w = 1 if np.random.random() < a else 0
            hon = np.random.random() < h
            best += w
            if dead > 0: dead -= 1
            elif hon:
                best = max(best-1, 0); dead = delta
        lead = best; t = 0; ok = False
        while True:
            t += 1
            if np.random.random() < a: lead += 1
            hon = np.random.random() < h
            if dead > 0: dead -= 1
            elif hon: lead -= 1; dead = delta
            if t >= T:
                if lead >= 1: ok = True; break
                if lead < -70: break
        if ok: op += 1
    return sv, op

if __name__ == "__main__":
    what = sys.argv[1]
    ref = {(10,3600):(4.903e-3,7.907e-3),(10,7200):(8.620e-5,1.423e-4),(15,3600):(1.913e-2,3.056e-2),(15,7200):(1.094e-3,1.802e-3)}
    alpha = 1/3
    for delta in (10, 15):
        for T in (3600, 7200):
            if what == 'dp':
                s = fwd(alpha, delta, T, 'block'); o = fwd(alpha, delta, T, 'cutoff')
                print(f"DP  delta={delta} T={T}: survival {s:.4e} (table {ref[(delta,T)][0]:.3e})  open {o:.4e} (table {ref[(delta,T)][1]:.3e})", flush=True)
            else:
                a, h = rates(alpha)
                n = 20_000_000 if T == 3600 else 60_000_000
                sv, op = mc(n, a, h, delta, T, 40000, 777)
                print(f"MC  delta={delta} T={T} n={n}: survival {sv/n:.4e} +- {math.sqrt(sv)/n:.1e} (table {ref[(delta,T)][0]:.3e})  open {op/n:.4e} +- {math.sqrt(op)/n:.1e} (table {ref[(delta,T)][1]:.3e})", flush=True)
