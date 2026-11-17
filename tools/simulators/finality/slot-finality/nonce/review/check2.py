# (1) multi-round correction to the D1 machine term; (2) lead>=0 (tie) variant of survival
import sys, numpy as np
sys.path.insert(0, "."); sys.path.insert(0, "review")
from model import clock
z = np.load("delayed_chain_curves.npz")
for tag, alpha, delta in (("30_10", .30, 10), ("30_15", .30, 15), ("33_10", 1/3, 10), ("33_15", 1/3, 15)):
    ts, s = z[tag+"_ts"], z[tag+"_s"]; rate = 1/clock(alpha, delta)
    S = lambda t: float(np.interp(t, ts, s)) if t <= ts[-1] else 0.0
    for hrs in (1, 2, 3, 4.5, 6):
        T = int(hrs*3600); i = T//60-1
        seen = rate*(T*s[i]+60*s[i+1:].sum())
        left = rate*(T*s[i]+60*s[i:-1].sum())
        # all rounds: fork point of age u, round k completes at fork+kT; usable if alive at max(kT,u)
        tot = 0.0
        for u in range(30, ts[-1], 60):            # midpoints, 60-s cells
            k = 1
            while k*T <= ts[-1]:
                tot += 60*S(max(k*T, u)); k += 1
        tot *= rate
        print(f"{tag} T={hrs}: printed seen {seen:.4e}; left-Riemann {left/seen:.4f}x; all rounds {tot/seen:.4f}x")
