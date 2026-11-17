# Multi-epoch figures (2026-11-17).
# 1. How long a race lasts under the floor when stake does not build, against the 72 hours from a
#    cut-off to the next epoch (4K at K = 64,800; 4 floor(k/f) on the ten-hour branch).
# 2. The share of targets whose race reaches the next epoch, so that the attack meets two nonces.
# 3. The building stake below which the floor is not met within 72 hours, so that a race can reach
#    an epoch whose nonce its private chain set.
# 4. The union bound over an epoch and a year of the chance per block.
# Model: the specification's Finality Floor. P(T_n <= t) = P(Binomial(t - n*D, p) >= n).
from scipy.stats import binom

f, H = 1 / 30, 3600.0
U = 64800            # floor(k/f), the unit of the epoch schedule
EPOCH = 10 * U       # 648,000 slots, 180 hours
CUT_TO_END = 4 * U   # from the cut-off (6U into the epoch) to the next epoch's first slot: 72 hours


def p_of(share):
    return 1 - (1 - f) ** share


def cdf(n, t, p, D):
    s = int(t - n * D)
    return 0.0 if s < n else float(binom.sf(n - 1, s, p))


def quantile(n, q, p, D):
    lo, hi = 0, int(50 * (n / p + n * D)) + 10
    while lo < hi:
        mid = (lo + hi) // 2
        if cdf(n, mid, p, D) >= q:
            hi = mid
        else:
            lo = mid + 1
    return lo


for K, phi in ((64800, 1291), (36000, 689), (64800, 1019), (36000, 560)):
    print(f"\nK = {K}, floor {phi}")
    for share_out, name in ((0.0, "all of the stake builds"), (0.1, "a tenth does not build"), (0.2, "a fifth"),
                            (0.3, "30 %"), (1 / 3, "a third"), (0.5, "a half")):
        for D in (10, 15):
            p = p_of(1 - share_out)
            med = max(K, quantile(phi, 0.5, p, D))
            late = max(K, quantile(phi, 1 - 1e-9, p, D))
            print(f"  {name:26s} {D:2d} s: a race lasts {med / H:5.1f} h at the median, {late / H:5.1f} h at the latest; "
                  f"targets whose race reaches the next epoch: {100 * med / EPOCH:4.1f} % (median), {100 * late / EPOCH:4.1f} % (latest)")
    # the building stake below which phi blocks do not fit in the 72 hours, at mean rates and with chance 1e-9
    for D in (0, 10, 15):
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if p_of(mid) * (CUT_TO_END - phi * D) >= phi else (mid, hi)
        mean_share = hi
        lo, hi = 0.0, 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if cdf(phi, CUT_TO_END, p_of(mid), D) >= 1 - 1e-9 else (mid, hi)
        print(f"  the floor is met within 72 h at {D} s when at least {100 * mean_share:.1f} % of the inferred stake builds (mean rates), "
              f"{100 * hi:.1f} % (with chance 1 - 1e-9)")

print("\nunion bound of a chance per block over the blocks of an epoch and of a year (every win counted, f = 1/30)")
blocks_epoch = EPOCH * f
blocks_year = 365.25 * 86400 * f
for name, c in (("1e-9, the target of the K row", 1e-9),
                ("a third at 15 s after 18 h, nonce unbiased (5.7e-10 / 1.21)", 5.7e-10 / 1.21),
                ("a third at 10 s after 18 h, nonce unbiased (1.2e-16)", 1.2e-16),
                ("a third at 10 s after 18 h, after a deflated inference (8.4e-14)", 8.4e-14),
                ("30 % at 15 s after 10 h, nonce unbiased (2.5e-10)", 2.5e-10),
                ("a third at 15 s after 10 h, nonce unbiased (6.1e-6)", 6.1e-6)):
    print(f"  {name}: per epoch {blocks_epoch * c:.2g}, per year {blocks_year * c:.2g}")
print(f"  blocks per epoch {blocks_epoch:.0f}, per year {blocks_year:.0f}, epochs per year {365.25 * 86400 / EPOCH:.1f}")
