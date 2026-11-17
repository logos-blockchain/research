# Check 2: is a constant 6-bit shift conservative? Two-nonce factor from paired samples, three ways.
import sys, math, numpy as np
sys.path.insert(0, "..")
from delayed_chain import wait_hours
EPS = 1e-9

def factor(l, bits, m=200_000):
    x = np.sort(2.0 ** np.minimum(l.astype(np.float64), bits)); n = len(x)
    cs = np.concatenate(([0.0], np.cumsum(x)))
    T = x[n - m:]; csT = np.concatenate(([0.0], np.cumsum(T))); sL = cs[n - m]; xLmax = x[n - m - 1]
    def phi(u):
        # pairs (top, anyone) twice, minus (top, top), plus (low, low); low-low products stay below 1
        assert u * xLmax * xLmax < 1.0
        k = np.searchsorted(x, 1.0 / (u * T), side="left")
        ta = (u * T * cs[k] + (n - k)).sum()
        kt = np.searchsorted(T, 1.0 / (u * T), side="left")
        tt = (u * T * csT[kt] + (m - kt)).sum()
        return (2 * ta - tt + u * sL * sL) / n / n
    lo, hi = -170.0, -20.0
    for _ in range(36):
        mid = (lo + hi) / 2
        if phi(2.0 ** mid) > EPS: hi = mid
        else: lo = mid
    return EPS / 2.0 ** lo

for an, alpha in (("30", 0.30), ("33", 1/3)):
    for delta in (10, 15):
        lg, lg2 = np.load(f"review2/pair_{an}_{delta}.npy")
        n = len(lg)
        qs = [1e-2, 1e-3, 1e-4, 1e-5]
        sh = [np.quantile(lg, 1 - q) - np.quantile(lg2, 1 - q) for q in qs]
        print(f"== {an} % / {delta} s, {n} cut-offs. shift at equal tail chance 1e-2..1e-5: " + ", ".join(f"{v:.2f}" for v in sh)
              + f"; share of top-1% cut-offs with shift < 6: {np.mean((lg - lg2)[lg > np.quantile(lg, .99)] < 6):.2f}; with shift < 1 (fork empties the sub-window): {np.mean((lg - lg2)[lg > np.quantile(lg, .99)] < 1):.4f}")
        for bits in (40, 64):
            res = []
            for part in (slice(None), slice(0, n // 2), slice(n // 2, n)):
                ft = factor(lg[part], bits); fd = factor(lg2[part], bits)
                fc = max(1.0, factor(lg[part], bits + 6) / 4.0 ** 6)
                # effective constant shift: b with factor_today(B + b) / 4^b = direct D2 factor
                bs = np.arange(0, 9.01, 1.0)
                ff = np.array([factor(lg[part], bits + b) / 4.0 ** b for b in bs])
                be = float(np.interp(-math.log(fd), -np.log(ff), bs))
                res.append((ft, fd, fc, be))
            ft, fd, fc, be = res[0]
            tail = np.mean(lg >= bits - 8)
            print(f"   B 2^{bits}: today {ft:.3g} ({wait_hours(alpha, delta, ft):.2f} h) | D2 direct {fd:.3g} ({wait_hours(alpha, delta, fd):.2f} h) | D2 by constant 6 {fc:.3g} ({wait_hours(alpha, delta, fc):.2f} h)"
                  f" | effective shift {be:.2f} bits (halves {res[1][3]:.2f}, {res[2][3]:.2f}) | D2 direct/const {fd / fc:.2f} (halves {res[1][1]/res[1][2]:.2f}, {res[2][1]/res[2][2]:.2f}) | samples with G >= 2^{bits-8}: {int(tail * n)}")
