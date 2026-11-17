"""The density test over one window: the chance that a private fork is at least as dense as the
honest chain over s_gen slots. Beside it, the same race over the 36,000 slots of ten hours.

The fork's count is Bin(n, a). The honest count is a renewal count: each gap is a delay of
delta slots and then a geometric wait, as in the Finality Floor. These are single-window
estimates, not the study's bound.

Usage: python3 single_window.py
"""
from math import exp, lgamma, log, sqrt

f = 1 / 30
S_GEN = 16200
DELTA = 10


def lottery(share):
    return 1 - (1 - f) ** share


def log_binom_pmf(n, i, p):
    return lgamma(n + 1) - lgamma(i + 1) - lgamma(n - i + 1) + i * log(p) + (n - i) * log(1 - p)


def binom_upper(n, m, p):
    """P(Bin(n, p) >= m)."""
    if m <= 0:
        return 1.0
    if m > n:
        return 0.0
    return sum(exp(log_binom_pmf(n, i, p)) for i in range(m, min(n, m + 6000) + 1))


def renewal_less(n, j, p, delta):
    """P(N(n) < j): fewer than j blocks in n slots, each gap delta + Geom(p) (the printed blocks_short)."""
    slots = n - j * delta
    if j <= 0:
        return 0.0
    if slots < j:
        return 1.0
    return sum(exp(log_binom_pmf(slots, i, p)) for i in range(j))


def race_tail(n_adv, n_hon, a, p_h, delta, head=0):
    """P(A(n_adv) >= H(n_hon) - head): A ~ Bin(n_adv, a), H a renewal count with gaps delta + Geom(p_h).
    head: honest blocks the adversary need not match (the restart path's head start)."""
    h_mean = n_hon / (delta + 1 / p_h)
    lo, hi = max(0, int(h_mean - 12 * sqrt(h_mean) - 5)), int(h_mean + 12 * sqrt(h_mean) + 5)
    total, prev = 0.0, renewal_less(n_hon, lo, p_h, delta)
    for j in range(lo, hi + 1):
        nxt = renewal_less(n_hon, j + 1, p_h, delta)
        pj = nxt - prev
        prev = nxt
        if pj > 0:
            total += pj * binom_upper(n_adv, j - head, a)
    return total + prev * 0.0 + renewal_less(n_hon, lo, p_h, delta)   # H < lo: the adversary wins


print("density test over s_gen = 16,200 against the length test over K (single-window estimates):")
for alpha in (0.3, 1 / 3):
    a, p_h = lottery(alpha), lottery(1 - alpha)
    for delta in (0, DELTA):
        dens = race_tail(S_GEN, S_GEN, a, p_h, delta)
        length = race_tail(36000, 36000, a, p_h, delta)
        print(f"  alpha {alpha:.3f}, delta {delta:>2}: density {dens:.1e}, length over 10 h {length:.1e}")
