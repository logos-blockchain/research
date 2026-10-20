"""The settlement bound robust over a certificate's band (`cbound` with explicit slot laws).

In the Lean model (`Prob/Worst.lean`, `Prob/WorstE.lean`) each slot's law is `q ⊗ Bern(a)`: an
honest part `q` (no leader, one, two or more) in the band's honest polytope `HB`, chosen by the
adversary given the past, and independently an adversarial win with probability `a ≤ amax`. The
event is closed under adding adversarial slots, so `a = amax`. One band member holds per epoch.

`HB`, in `h = q1 + q2` and `p1 = q1`: `max(hlo, hnlo/(1-amax)) ≤ h ≤ min(hhi, 1 - elo/(1-amax))` and
`slo/(1-amax) ≤ p1 ≤ h`, a quadrilateral. This script runs `cbound` at its four vertices for every
member and keeps the worst. A fixed vertex is not the adaptive adversary of the Lean model, so the
result is a lower estimate of the robust value: what no witness for the current proof structure
can beat, not a bound itself.

The total adds the estimate's band term `Ne · bandEps` (`certE.band_eps_float`) and replaces
`cbound`'s fixed window term (1e-12) by the actual one at depth `k`: `N · P(Bin(w, occ) > k)` for
windows of `w` slots, `occ = 1 - (1 - h)(1 - a)` the vertex's chance of an occupied slot.

Usage: python3 band.py BETA DELTA K_MEMBERS DEPTH N [MU] [Δ]
"""
import sys, os, json, subprocess
from fractions import Fraction as Fr
from scipy.stats import binom

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certgen"))
import certE  # noqa: E402

CBOUND = os.path.join(os.path.dirname(os.path.abspath(__file__)), "target", "release", "cbound")


def vertices(B):
    """the honest polytope's vertices `(h, p1)` with the adversary at `amax`"""
    am = B['amax']
    hL = max(B['hlo'], B['hnlo'] / (1 - am))
    hU = min(B['hhi'], 1 - B['elo'] / (1 - am))
    pL = B['slo'] / (1 - am)
    assert hL <= hU and pL <= hL, ('empty polytope', float(hL), float(hU), float(pL))
    return [(hL, pL), (hL, hL), (hU, pL), (hU, hU)]


def robust(beta, delta, K, k, N, mu=0.13, D=11, cap=10):
    certE.set_depth(k)
    T = certE.tband(beta, delta, mu=Fr(mu).limit_denominator(1000))
    fam = certE.epoch_members(T, K)
    cfgs, tags = [], []
    for i, m in enumerate(fam):
        B = m['B']
        for j, (h, p1) in enumerate(vertices(B)):
            cfgs.append([1 / 30, beta, D, cap, N, 1, 0, 0, 0, float(h), float(p1), float(B['amax'])])
            tags.append((i, j))
    out = subprocess.run([CBOUND], input=json.dumps(cfgs), capture_output=True, text=True, check=True).stdout
    res = json.loads(out)
    worst = None
    for (i, j), r in zip(tags, res):
        h, p1, a = r['law']
        occ = 1 - (1 - h) * (1 - a)
        best = min((bv - 1e-12 + N * binom.sf(k, w, occ), w) for w, bv, _ in r['curve'])
        if worst is None or best[0] > worst[0]:
            worst = (best[0], best[1], i, j, (h, p1, a))
    Ne = (N + 3000) // certE.EL + 1
    band = Ne * certE.band_eps_float(T)
    return dict(beta=beta, delta=delta, k=k, N=N, settle=worst[0], window=worst[1], member=worst[2],
                vertex=worst[3], law=worst[4], band=band, total=worst[0] + band)


if __name__ == "__main__":
    a = sys.argv[1:]
    r = robust(float(a[0]), float(a[1]), int(a[2]), int(a[3]), int(a[4]),
               float(a[5]) if len(a) > 5 else 0.13, int(a[6]) if len(a) > 6 else 11)
    print(json.dumps(r))
