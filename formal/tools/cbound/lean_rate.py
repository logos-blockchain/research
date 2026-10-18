"""The decay rate of a failed check under Lean's phase semantics, for a fixed slot law.

The phases are those of `Prob/Phases.lean`: a phase is one slot with no honest success, or a
burst that starts at an honest slot and ends after `Δ` slots with none. One phase moves the
reach and margin bounds by `step` (`Settle/Phases.lean`, `step_cases`):

    ρ' = max(ρ + A - H, A)
    μ' = μ + A - H         if μ < -A
         ρ - H             if the phase is a crossing (no adversarial slot, one honest slot, one leader)
         ρ'                otherwise

with `A` its adversarial slots and `H` its honest depth. A failed check is a margin that is not
cold (`μ ≥ 0`) `J` phases after an anchor where `μ = ρ`. This script iterates

    W_0(ρ, μ) = [μ ≥ 0],   W_{j+1}(ρ, μ) = E[W_j(step(ρ, μ))]

for one slot law `(h, p1, a)` (honest success, exactly one honest leader, adversarial win,
independent as in `prodLaw`), with `H = 1` in a burst (`H ≥ 1`, and the step is monotone, so
this only raises `W`), the margin clipped at `-M` and the reach at `R` (pessimistic: clipping
raises `μ`; the reach cap is checked by doubling it). The ratio `W_{j+1}/W_j` converges to the
decay per phase that any witness for this term can at best certify, to compare with a
certificate's in-epoch contraction `lpi`.

Usage: python3 lean_rate.py H P1 A [DELTA] [J] [R] [M]
"""
import sys
import numpy as np


def burst_law(h, p1, a, D, amax=80):
    """joint law of (A, X) over a burst: `A` adversarial slots (capped at `amax`, the overflow kept
    as `amax`, which only raises `W`), `X` a crossing"""
    # state: q (slots since the last honest success), A, nh (1 or 2+), single (first honest slot had one leader)
    cur = np.zeros((D, amax + 1, 2, 2))
    for adv, pa in ((0, 1 - a), (1, a)):
        cur[0, adv, 0, 1] += pa * p1 / h
        cur[0, adv, 0, 0] += pa * (1 - p1 / h)
    out = np.zeros((amax + 1, 2))  # [A, X]
    for _ in range(100000):
        if cur.sum() < 1e-18:
            break
        new = np.zeros_like(cur)
        for adv, pa in ((0, 1 - a), (1, a)):
            sh = np.zeros_like(cur)
            sh[:, adv:, :, :] = cur[:, :amax + 1 - adv, :, :]
            if adv:
                sh[:, amax, :, :] += cur[:, amax, :, :]
            # an honest success: back to q = 0, now two or more honest slots
            hs = pa * h * sh.sum(axis=0)          # [A, nh, single]
            new[0, :, 1, :] += hs.sum(axis=1)
            # no honest success: q + 1; at q + 1 = D the burst ends
            nq = pa * (1 - h) * sh
            new[1:, :, :, :] += nq[:-1]
            end = nq[D - 1]                        # [A, nh, single]
            out[:, 0] += end.sum(axis=(1, 2))
            # a crossing: one honest slot (nh = 1) with one leader (single), and no adversarial slot
            out[0, 1] += end[0, 0, 1]
            out[0, 0] -= end[0, 0, 1]
        cur = new
    return out


def rate(h, p1, a, D=11, J=4000, R=120, M=200, every=500):
    law = burst_law(h, p1, a, D)
    # states: rho in 0..R, mu in -M..R (only mu <= rho reachable); index mu + M
    nmu = M + R + 1
    W = np.zeros((R + 1, nmu))
    rho = np.arange(R + 1)[:, None]
    mu = np.arange(-M, R + 1)[None, :]
    valid = mu <= rho
    W[:] = (mu >= 0) & valid

    def stepped(Wj, A, H, X):
        """W_j at step(ρ, μ) for every state, for one phase outcome"""
        rp = np.minimum(np.maximum(rho + A - H, A), R)
        if X:
            mup = np.where(mu < -A, mu + A - H, rho - H)
        else:
            mup = np.where(mu < -A, mu + A - H, np.maximum(rho + A - H, A))
        mup = np.minimum(np.maximum(mup, -M), rp)
        return Wj[np.broadcast_to(rp, (R + 1, nmu)), np.broadcast_to(mup + M, (R + 1, nmu))]

    hist = []
    for j in range(J):
        Wn = (1 - h) * ((1 - a) * stepped(W, 0, 0, False) + a * stepped(W, 1, 0, False))
        for A in range(law.shape[0]):
            for X in (0, 1):
                p = law[A, X]
                if p > 1e-30:
                    Wn += h * p * stepped(W, A, 1, bool(X))
        Wn = np.where(valid, Wn, 0)
        r = Wn[0, M] / W[0, M] if W[0, M] > 0 else 0
        W = Wn
        if (j + 1) % every == 0:
            hist.append((j + 1, W[0, M], r))
    return hist


if __name__ == "__main__":
    a = [float(x) for x in sys.argv[1:4]]
    D = int(sys.argv[4]) if len(sys.argv) > 4 else 11
    J = int(sys.argv[5]) if len(sys.argv) > 5 else 4000
    R = int(sys.argv[6]) if len(sys.argv) > 6 else 120
    M = int(sys.argv[7]) if len(sys.argv) > 7 else 200
    for j, w, r in rate(*a, D=D, J=J, R=R, M=M):
        print(f"J={j}: W_J(0,0) = {w:.3e}, per-phase ratio {r:.6f}")
