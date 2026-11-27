"""Reference parameters: when the estimate of an epoch is first used, can two chains that a running node holds differ in the counted blocks?
They can only if fewer than k blocks lie in the last 4*floor(k/f) - W/f slots, since step 8 admits no fork point further back."""
from math import lgamma, log, exp, log10
k, f_inv, W = 2160, 30, 240
kf = k * f_inv; n = 4 * kf - W * f_inv
def log_tail(n, p, m):                       # log10 P(Bin(n, p) < m)
    best = None; terms = []
    for x in range(m):
        terms.append(lgamma(n + 1) - lgamma(x + 1) - lgamma(n - x + 1) + x * log(p) + (n - x) * log(1 - p))
    mx = max(terms); return (mx + log(sum(exp(t - mx) for t in terms))) / log(10)
print(f"k/f = {kf} slots ({kf/3600:.0f} h); gap 4k/f = {4*kf} slots ({4*kf/3600:.0f} h); minus the window {n} slots")
for g in (1.0, 0.9, 0.75, 0.5, 0.35, 0.3, 0.28, 0.26, 0.25, 0.24):
    p = g / f_inv
    print(f"chain growth {g:4.2f} of the target: {n*p:7.0f} blocks expected, P(fewer than k) = 10^{log_tail(n, p, k):.1f}")
print(f"k blocks take {kf/3600:.0f} h at the full rate, {kf/0.5/3600:.0f} h at half of it, {kf/0.25/3600:.0f} h at a quarter")
E = 6 * kf / f_inv
print(f"expected count {E:.0f}; one reference is {100/E:.4f} % of it")
