"""Prototype of a table witness for the failed-check term, checked as Lean would check it.

The certificates bound a failed check with a two-term exponential potential in the reach and
margin bounds (`Cold2.lean`, `Fail3E.lean`), contracting by `lpi` per phase inside an epoch.
Here the potential is a table `V(ρ, μ)` on a box (`0 ≤ ρ ≤ R`, `μ` warm, i.e. `μ = ρ`, or cold
with `-M ≤ μ < 0`), extended geometrically outside it. Each box state must satisfy

    E[V(step(ρ, μ))] ≤ λ · V(ρ, μ)

for every kernel within the band, bounded exactly as the Lean proof bounds a phase:

* the phase from its start through the per-slot automaton (`Prob/Auto.lean`): one slot with no
  honest success ends the phase, an honest slot starts a burst, and every slot's expectation is
  bounded by `slot4` from the band's marginal bounds (`amax`/`alo`, `hhi`/`hlo`, `hahi`/`halo`);
  the terminal table is `g(a, B, U2)` with `a = min(A, 2)` and a factor `x^A`, so
  `g(a, B, ·) = max over A with min(A, 2) = a of V(step(ρ, μ; A, H = B, no crossing)) / x^A`
  (`H ≥ B` and `step` is monotone, so `H = B` only raises `V`); the automaton's table `v` is
  its least solution (`AutoSol`: `v ≥ g` and `v ≥ stepR v`), and the phase bound `autoBound`;
* the crossing's credit through the lower bound on one fixed pattern (`phase_lower`: one honest
  slot with one leader, no adversary, then `Δ` empty slots, probability at least `slo · elo^Δ`):
  `pat · (V(step without crossing) - V(step with crossing))`, both at `A = 0`, `H = 1`.

`V` comes from power iteration of this operator for one member, and `λ` is checked for every
member of the family. A failed check is a warm margin, so `V` is normalized to at least 1 on
warm states.

Usage: python3 proto.py BETA DELTA DEPTH [R] [M] [ITERS]
"""
import sys, os
import numpy as np
from fractions import Fraction as Fr

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "certgen"))
import certE  # noqa: E402

AX = 40  # adversarial slots tabulated per phase for the terminal table's a = 2 bucket


class Box:
    """box states and the geometric extension: past `ρ = R`, `V` grows by `cw` per unit of reach on
    warm states and by `cc` on cold ones; past `μ = -M` it shrinks by `zc` per unit of margin"""

    def __init__(self, R, M, cw, cc, zc):
        self.R, self.M, self.cw, self.cc, self.zc = R, M, cw, cc, zc
        rho = np.arange(R + 1)
        # state list: cold (ρ, μ) with -M ≤ μ ≤ -1, then warm (ρ, ρ)
        cold = [(r, m) for r in range(R + 1) for m in range(-M, 0)]
        warm = [(r, r) for r in range(R + 1)]
        self.states = np.array(cold + warm)
        self.n = len(self.states)
        self.nc = len(cold)

    def index(self, rho, mu):
        """index of the box state at `(min(ρ, R), max(μ, -M))` and the extension factor"""
        R, M = self.R, self.M
        warm = mu >= 0
        over = np.maximum(rho - R, 0).astype(float)
        fac = np.where(warm, self.cw ** over, self.cc ** over)
        fac = fac * np.where(mu < -M, self.zc ** (mu + M).astype(float), 1.0)
        r = np.minimum(rho, R)
        m = np.maximum(mu, -M)
        # a warm state past the box is (R, R) scaled; a warm state has μ = ρ
        idx = np.where(warm, self.nc + r, r * M + (m + M))
        return idx, fac


def step(rho, mu, A, H, X):
    rp = np.maximum(rho + A - H, A)
    mp = np.where(mu < -A, mu + A - H, (rho - H) if X else rp)
    mp = np.minimum(mp, rp)
    return rp, mp


def slot4(B, F00, F01, F10, F11):
    """`slot4` (`Prob/Auto.lean`): the band's bound on one slot's expectation of `F(h, a)`"""
    c1 = F01 - F00
    c2 = F10 - F00
    c3 = F11 - F10 - F01 + F00
    return (F00 + c1 * np.where(c1 >= 0, B['amax'], B['alo']) + c2 * np.where(c2 >= 0, B['hhi'], B['hlo'])
            + c3 * np.where(c3 >= 0, B['hahi'], B['halo']))


class Operator:
    def __init__(self, box, D, x):
        self.box, self.D, self.x = box, D, x
        rho, mu = box.states[:, 0], box.states[:, 1]
        # next-state indices for A = 0..AX, H in {0, 1}, crossing or not
        self.nxt = {}
        for A in range(AX + 1):
            for H in (0, 1):
                for X in (False, True):
                    if X and (A != 0 or H != 1):
                        continue
                    rp, mp = step(rho, mu, A, H, X)
                    self.nxt[(A, H, X)] = box.index(rp, mp)

    def apply(self, V, B):
        """the Lean bound on `E[V(next phase end)]` at every box state, for band `B`"""
        D, x = self.D, self.x
        Vn = lambda key: V[self.nxt[key][0]] * self.nxt[key][1]
        # terminal table g[a][b] (U2 does not enter the step)
        g = np.zeros((3, 2, self.box.n))
        for b in (0, 1):
            g[0, b] = Vn((0, b, False))
            g[1, b] = Vn((1, b, False)) / x
            g[2, b] = np.max([Vn((A, b, False)) / x ** A for A in range(2, AX + 1)], axis=0)
        # automaton: v[q, a] (u2 does not enter g, so it is dropped), least solution of
        # v ≥ g(a, true), v ≥ θ · slot4(next slot), θ = 1
        v = np.repeat(g[:, 1][None, :, :], D, axis=0)  # start at the terminal bound
        for _ in range(2000):
            vn = np.empty_like(v)
            for q in range(D):
                for a in range(3):
                    a1 = min(a + 1, 2)
                    # no honest success: q + 1 (or the end of the burst); honest: back to q = 0
                    nh0 = g[a, 1] if q + 1 == D else v[q + 1, a]
                    nh1 = g[a1, 1] if q + 1 == D else v[q + 1, a1]
                    F00, F01 = nh0, x * nh1
                    F10, F11 = v[0, a], x * v[0, a1]
                    vn[q, a] = np.maximum(g[a, 1], slot4(B, F00, F01, F10, F11))
            if np.max(np.abs(vn - v) / np.maximum(v, 1e-300)) < 1e-13:
                v = vn
                break
            v = vn
        # the phase from its start: no honest success ends it; an honest slot starts a burst
        F00, F01 = g[0, 0], x * g[1, 0]
        F10, F11 = v[0, 0], x * v[0, 1]
        bound = slot4(B, F00, F01, F10, F11)
        # the crossing's credit
        pat = B['slo'] * B['elo'] ** D
        diff = Vn((0, 1, False)) - Vn((0, 1, True))
        return bound - pat * np.maximum(diff, 0)


def fband(B):
    return {k: float(v) for k, v in B.items()}


def power(op, B, iters=400, V0=None):
    box = op.box
    V = np.ones(box.n) if V0 is None else V0.copy()
    lam = None
    for i in range(iters):
        TV = op.apply(V, B)
        lam = np.max(TV / V)
        V = TV / TV[box.nc + 0]  # normalize V(0, 0) = 1 (the smallest warm state)
        V = np.maximum(V, 1e-300)
    # make warm states at least 1 (a warm margin is a failed check)
    V = V / np.min(V[box.nc:])
    return V, np.max(op.apply(V, B) / V)


if __name__ == "__main__":
    beta, delta, k = float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3])
    R = int(sys.argv[4]) if len(sys.argv) > 4 else 40
    M = int(sys.argv[5]) if len(sys.argv) > 5 else 80
    iters = int(sys.argv[6]) if len(sys.argv) > 6 else 300
    certE.set_depth(k)
    T = certE.tband(beta, delta, mu=Fr(13, 100))
    fam = certE.epoch_members(T, 32)
    D = 11
    ce, ze = 1.1785, 1.7543   # the k = 1000 certificate's c and z
    x = ce * ze
    box = Box(R, M, ce, ze)
    op = Operator(box, D, x)
    worst = 0
    V, lam0 = power(op, fband(fam[worst]['B']), iters)
    print(f"member {worst}: λ = {lam0:.6f}")
    lams = [np.max(op.apply(V, fband(m['B'])) / V) for m in fam]
    print("all members with that V: max λ =", f"{max(lams):.6f}", "at member", int(np.argmax(lams)))
    w = V[box.nc:]
    print("V on warm states ρ = 0..10:", " ".join(f"{t:.3g}" for t in w[:11]))
    print("V(ρ, ρ) / ce^ρ, ρ = 0..R:", f"max {np.max(w / ce ** np.arange(R + 1)):.3g}")
