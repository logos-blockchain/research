"""Time to finality under each rule, as a distribution, in the model of the specification's
Finality Floor: a gap between blocks of the chain is a delay of D slots plus a geometric wait at
p = 1 - (1 - f)^share. So n blocks follow a block within t slots iff the t - n*D slots left hold at
least n wins: P(T_n <= t) = P(Binomial(t - n*D, p) >= n). Exact in that model, no simulation.

Rules, for a block and the chain above it (age = slots from the block to the tip):
  DEPTH   k blocks of the chain follow                      (master)
  SLOT    age >= K and phi occupied slots follow            (#532; occupied taken as chain blocks)
  A       DEPTH and SLOT   = age >= K and k blocks follow
  B       DEPTH or SLOT
  A_occ   age >= K and k OCCUPIED slots follow (the floor raised to k as #532 counts it). Occupied
          slots are taken here at their upper end: every lottery win of the building stake, with
          no delay cost. The truth lies between A and A_occ.
The gap from the K-th slot to the next block (about one block interval) is left out everywhere.

"share" is the stake that builds, as a multiple of the stake the lottery is normalised to.
BLEND is an effective delay fitted so that K slots hold 1,825 blocks with all stake building,
RFC-532's figure for the specification's Blend under random delay. It is a fit to a mean.
"""
import math

from scipy.stats import binom

f, k, K, PHI = 1 / 30, 2160, 64800, 1019
H = 3600.0
EPS = 1e-9


def p_of(share):
    return 1 - (1 - f) ** share


def cdf(n, t, p, D):
    """P(T_n <= t)."""
    s = int(t - n * D)
    if s < n:
        return 0.0
    return float(binom.sf(n - 1, s, p))


def quantile(n, q, p, D):
    """Least t with P(T_n <= t) >= q."""
    lo, hi = 0, int(50 * (n / p + n * D)) + 10
    while lo < hi:
        mid = (lo + hi) // 2
        if cdf(n, mid, p, D) >= q:
            hi = mid
        else:
            lo = mid + 1
    return lo


def mean(n, p, D):
    return n / p + n * D


def blend_delay():
    lo, hi = 0.0, 30.0
    for _ in range(80):
        mid = (lo + hi) / 2
        p = p_of(1.0)
        if p / (1 + p * mid) * K > 1825:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


BLEND = blend_delay()


def rule_quantiles(share, D):
    """For each rule: earliest (1e-9), median, latest (1 - 1e-9), in hours."""
    p = p_of(share)
    Di = D  # the binomial takes whole slots; a fractional delay enters through int(t - n*D)
    out = {}
    qs = (EPS, 0.5, 1 - EPS)
    tk = [quantile(k, q, p, Di) for q in qs]
    tphi = [quantile(PHI, q, p, Di) for q in qs]
    tk_occ = [quantile(k, q, p, 0) for q in qs]
    out["DEPTH"] = tk
    out["SLOT"] = [max(K, t) for t in tphi]
    out["A"] = [max(K, t) for t in tk]
    out["A_occ"] = [max(K, t) for t in tk_occ]
    # B: P(B <= t) = P(T_k <= t) below K, P(T_phi <= t) from K on.
    b = []
    for q, a, c in zip(qs, tk, tphi):
        b.append(a if a < K else max(K, c))
    out["B"] = b
    out["P(depth before K)"] = cdf(k, K - 1, p, Di)       # B: depth passes first; A: slot leg binds
    out["P(floor missed at K)"] = 1 - cdf(PHI, K, p, Di)
    out["blocks in K (mean)"] = p / (1 + p * D) * K
    out["mean T_k h"] = mean(k, p, D) / H
    return out


ROWS = [
    ("all stake builds, Blend (fit)", 1.0, BLEND),
    ("all stake builds, no delay", 1.0, 0),
    ("30 % withholds, Blend (fit)", 0.7, BLEND),
    ("a third withholds, Blend (fit)", 2 / 3, BLEND),
    ("a third withholds, worst case 10 s", 2 / 3, 10),
    ("a third withholds, worst case 15 s", 2 / 3, 15),
    ("a third withholds, worst case 20 s", 2 / 3, 20),
    ("90 % of all stake online, Blend (fit)", 0.9, BLEND),
    ("half of the stake builds (split in halves), Blend (fit)", 0.5, BLEND),
    ("lottery 1.25 times fast, all build, Blend (fit)", 1.25, BLEND),
    ("lottery 1.5 times fast, all build, Blend (fit)", 1.5, BLEND),
    ("lottery 1.925 times fast, all build, Blend (fit)", 1.925, BLEND),
    ("lottery 1.5 times fast, a third of it withholds, 10 s", 1.0, 10),
    ("lottery 1.925 times fast, a third of it withholds, 10 s", 1.925 * 2 / 3, 10),
]

if __name__ == "__main__":
    print(f"BLEND effective delay (fit): {BLEND:.3f} slots")
    hdr = f"{'case':58s} {'blk/K':>6s} | " + " | ".join(
        f"{r:>20s}" for r in ("DEPTH", "SLOT (#532)", "A (both)", "A_occ", "B (first)")) + " | P(depth<K)  P(miss floor)"
    print(hdr)
    print(f"{'':58s} {'':6s} | " + " | ".join(["  early  med   late "] * 5))
    for name, share, D in ROWS:
        r = rule_quantiles(share, D)
        cells = " | ".join(" ".join(f"{t / H:6.2f}" for t in r[x]) for x in ("DEPTH", "SLOT", "A", "A_occ", "B"))
        print(f"{name:58s} {r['blocks in K (mean)']:6.0f} | {cells} | {r['P(depth before K)']:.2e}   {r['P(floor missed at K)']:.2e}")

    # A side cut off from the rest (no delay inside the side): days to make n blocks.
    print("\nA side of share s, alone, days to make n blocks: mean, earliest at 1e-9")
    for s in (0.1, 0.2, 0.25, 0.3, 1 / 3, 0.4, 0.5):
        p = p_of(s)
        cells = []
        for n in (PHI + 1, k + 1):
            cells.append(f"n={n}: {mean(n, p, 0) / 86400:5.2f} / {quantile(n, EPS, p, 0) / 86400:5.2f}")
        print(f"  s={s:.3f}  " + "   ".join(cells))

    # Eclipse, at mean rates, no delay: the coalition (share a) builds a private fork from a
    # divergence block. The node follows the honest chain (share 1 - a) until the eclipse starts at
    # t_e, and must not have made the divergence block's child immutable by then. The fork must
    # then pass the rule and be longer than the node's chain. Eclipse length = t_fork - t_e,
    # minimised over t_e.
    print("\nEclipse a prepared fork needs, hours, mean rates, no delay")
    for a in (0.3, 1 / 3):
        pa, ph = p_of(a), p_of(1 - a)
        best = {}
        for rule in ("DEPTH", "SLOT", "A", "B"):
            m = None
            for te in range(0, 4 * K, 60):
                hb = ph * te                       # blocks of the node's chain above the divergence
                final = {"DEPTH": hb >= k, "SLOT": te >= K and hb >= PHI,
                         "A": te >= K and hb >= k, "B": hb >= k or (te >= K and hb >= PHI)}[rule]
                if final:
                    break
                # blocks the fork needs: more than the node's chain, and enough to pass the rule
                def passes(t):
                    fb = pa * t
                    if fb <= hb:
                        return False
                    return {"DEPTH": fb >= k + 1, "SLOT": t >= K and fb >= PHI + 1,
                            "A": t >= K and fb >= k + 1,
                            "B": fb >= k + 1 or (t >= K and fb >= PHI + 1)}[rule]
                lo, hi = 0, 40 * K
                while lo < hi:
                    mid = (lo + hi) // 2
                    if passes(mid):
                        hi = mid
                    else:
                        lo = mid + 1
                d = lo - te
                if m is None or d < m[0]:
                    m = (d, te, lo)
            best[rule] = m
        print(f"  a={a:.3f}: " + "   ".join(f"{r}: {v[0] / H:5.1f} h (starts {v[1] / H:5.1f} h after the fork point)"
                                            for r, v in best.items()))

    # The epoch's waits: the share of the inferred stake that must build for n blocks to follow a
    # value within a phase. Mean, and with chance 1 - 1e-9. No delay.
    print("\nShare of the inferred stake that must build so that a value is final when its phase ends")
    for phase_h in (54, 72):
        for label, n in (("depth k", k), ("floor phi", PHI)):
            res = []
            for q in (0.5, 1 - EPS):
                lo, hi = 0.0, 3.0
                for _ in range(50):
                    mid = (lo + hi) / 2
                    if cdf(n, phase_h * H, p_of(mid), 0) >= q:
                        hi = mid
                    else:
                        lo = mid
                res.append(hi)
            print(f"  phase {phase_h} h, {label:9s}: median {100 * res[0]:.1f} %, with chance 1 - 1e-9 {100 * res[1]:.1f} %")
