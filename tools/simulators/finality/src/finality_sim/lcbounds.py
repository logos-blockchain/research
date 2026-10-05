"""Settlement bounds for longest-chain proof of stake (PLAN.md B1).

A line-for-line port of the proof-of-stake routines of LCanalysis
(github.com/renling/LCanalysis @ 35cfc83), the code of Gaži, Ren and Russell, "Practical
Settlement Bounds for Longest-Chain Consensus" (ePrint 2022/1571, revision 2025-05-02):
``PoSSlotPdf``, ``PoWMCWarmupUB``, ``PoWMCWarmupLB``, ``PoWMCFinalUB``, ``PoSMCConfirmUB`` and
``PoSMCConfirmLB``. Time is measured in expected block intervals: the honest and adversarial
block processes are Poisson with rates ``alpha`` and ``1 - alpha``, and ``delta`` is the
network delay bound in block intervals (``D = f * Delta`` for a slot lottery at rate ``f``).

The MATLAB loops are kept, with indices shifted to zero-based; the heavy Markov-chain steps
are compiled with numba. ``tests/test_lcbounds.py`` gates the port against Table 1 of the
revision, which the original code produced.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numba import njit
from scipy import stats

N_STEPS = 1001          # PoSSlotPdf: time discretisation of one delay
WARMUP_STEPS = 200      # PoWMCWarmupUB / LB
FINAL_STEPS = 200       # PoWMCFinalUB
LB_STEPS = 80           # PoSMCConfirmLB


@dataclass
class SlotPdf:
    """The symbol distribution of ``PoSSlotPdf``.

    ``ph[h-1]`` = Pr(H = h); ``pd[h-1, d-1]`` = Pr(D = d | H = h); ``pa[h-1, d-1, a]`` =
    Pr(A = a | H = h, D = d); ``pad[a, d]`` = Pr(A = a, D = d); ``pa_only`` = Pr(A = 1, H = 0).
    """

    pa_only: float
    ph: np.ndarray
    pd: np.ndarray
    pa: np.ndarray
    pad: np.ndarray


def slot_pdf(alpha: float, delta: float, n: int) -> SlotPdf:
    """Port of ``PoSSlotPdf(alpha, Delta, N)``."""
    beta = 1.0 - alpha
    g = np.exp(-alpha * delta)
    step = delta / N_STEPS
    t = (np.arange(1, N_STEPS + 1) - 0.5) * step                  # dt, both definitions agree
    pt_exp = np.zeros(N_STEPS + 1)
    pt_exp[:N_STEPS] = alpha * np.exp(-alpha * t) * step / (1.0 - g)

    ph = alpha * g * (1.0 - g) ** np.arange(n)
    pd = np.zeros((n, n))
    pa = np.zeros((n, n, n))
    pd[0, 0] = 1.0
    pa[0, 0, :] = stats.poisson.pmf(np.arange(n), beta * delta)

    pois = stats.poisson.pmf(np.arange(n)[:, None], beta * t[None, :])   # (a, m)
    pt_jump = np.zeros(N_STEPS + 1)
    pt_jump[0] = 1.0
    for i in range(2, n + 1):                                     # MATLAB i
        pt_jump_new = np.convolve(pt_jump, pt_exp)
        pd_diff0 = 1.0 if i == 2 else pt_jump_new[:N_STEPS].sum()
        pd[i - 1, :i] = np.convolve(pd[i - 2, :i - 1], [pd_diff0, 1.0 - pd_diff0])

        # Tailgater time: PTG0(m) sums PTjump(ds) over ds <= NSteps-1-m, PTG1 over the rest.
        cs = np.cumsum(pt_jump)
        m = np.arange(N_STEPS)
        ptg0 = pt_exp[:N_STEPS] * cs[N_STEPS - 1 - m]
        ptg1 = pt_exp[:N_STEPS] * (cs[N_STEPS] - cs[N_STEPS - 1 - m])
        pa_tmp0 = pois @ ptg0
        pa_tmp1 = pois @ ptg1

        for d in range(1, i):                                     # MATLAB d = 1..i-1
            acc = np.zeros(2 * n - 1)
            if d == 1 or d <= i - 2:
                acc += np.convolve(pa[i - 2, d - 1, :], pa_tmp0)
            if d > 1:
                acc += np.convolve(pa[i - 2, d - 2, :], pa_tmp1)
            pa[i - 1, d - 1, :] = acc[:n]

        pt_jump = pt_jump_new[:N_STEPS + 1].copy()
        pt_jump[0] = pt_jump_new[N_STEPS:].sum()
        pt_jump /= pt_jump.sum()

    for i in range(1, n + 1):
        for d in range(1, i):
            pa[i - 1, d - 1, :] /= pd[i - 1, d - 1]

    pad = np.zeros((n, n))
    for h in range(1, n + 1):
        for j in range(1, max(1, h - 1) + 1):
            pad[:, j] += ph[h - 1] * pd[h - 1, j - 1] * pa[h - 1, j - 1, :]
    pad[1, 0] = beta
    return SlotPdf(pa_only=beta, ph=ph, pd=pd, pa=pa, pad=pad)


def _warmup_matrix(pad: np.ndarray, alphabet: int, states: int, upper: bool) -> np.ndarray:
    z = states
    q = np.zeros((2 * states + 1, 2 * states + 1))
    for i in range(alphabet):
        for j in range(alphabet):
            for k in range(states + 1):
                if abs(k + i - j) > states:
                    continue
                if upper:
                    dst = k + i - j if (k < -i or k > j) else i
                else:
                    dst = max(0, k + i - j)
                q[z + dst, z + k] += pad[i, j]
    return q


def warmup(pad: np.ndarray, alphabet: int, states: int, upper: bool) -> np.ndarray:
    """Port of ``PoWMCWarmupUB`` (``upper``) and ``PoWMCWarmupLB``."""
    q = _warmup_matrix(pad, alphabet, states, upper)
    st0 = np.zeros(2 * states + 1)
    st0[states] = 1.0
    return np.linalg.matrix_power(q, WARMUP_STEPS) @ st0


def final_ub(pad: np.ndarray, st2: np.ndarray, alphabet: int, states: int) -> float:
    """Port of ``PoWMCFinalUB``: the chance the adversary is ever ahead after confirmation."""
    z = states
    q = np.zeros((2 * states + 1, 2 * states + 1))
    for i in range(alphabet):
        for j in range(alphabet):
            for k in range(-states, states + 1):
                if abs(k + i - j) > states:
                    continue
                dst = k + i - j if (k < -i or k > j) else min(0, k) + i
                q[z + dst, z + k] += pad[i, j]
    st = np.linalg.matrix_power(q, FINAL_STEPS) @ st2
    return float(st[z:].sum())


@njit(cache=True)
def _confirm_ub(K, pa_only, ph, pd, pa, st0, alphabet, states, min_prob):
    """Port of ``PoSMCConfirmUB``; returns St2, the adversary's lead at confirmation."""
    z = states
    w = 2 * states + 1
    st1 = np.zeros((w, w, 2 * K))
    st2 = np.zeros(w)
    for i in range(states + 1):
        lmin = K - i
        if lmin > 0:
            st1[z + i, z + i, lmin - 1] = st0[z + i]
        else:
            st2[z + i] = st0[z + i]

    for _ in range(2 * K):
        st1n = np.zeros((w, w, 2 * K))
        # (a=1, h=0): lead k -> k+1; each adversarial block counts down by 2
        for k in range(states):
            for l in range(3, 2 * K + 1):
                st1n[z + k + 1, z + k + 1, l - 3] += st1[z + k, z + k, l - 1] * pa_only
            st2[z + k + 1] += (st1[z + k, z + k, 0] + st1[z + k, z + k, 1]) * pa_only
        for y in range(states):                                   # x from -1 to 0, teleport
            for l in range(3, 2 * K + 1):
                st1n[z + y + 1, z + y + 1, l - 3] += st1[z - 1, z + y, l - 1] * pa_only
            st2[z + y + 1] += (st1[z - 1, z + y, 0] + st1[z - 1, z + y, 1]) * pa_only
        for x in range(-states, -1):
            for y in range(states):
                for l in range(3, 2 * K + 1):
                    st1n[z + x + 1, z + y + 1, l - 3] += st1[z + x, z + y, l - 1] * pa_only
                st2[z + x + 1] += (st1[z + x, z + y, 0] + st1[z + x, z + y, 1]) * pa_only

        # (a=0, h=1) from 0 to -1; each honest block counts down by 1
        p_h = ph[0] * pa[0, 0, 0]
        for l in range(2, 2 * K + 1):
            st1n[z - 1, z, l - 2] += st1[z, z, l - 1] * p_h
        st2[z - 1] += st1[z, z, 0] * p_h

        # general symbols (H = h, D = j, A = i)
        for h in range(1, alphabet + 1):
            for j in range(1, max(1, h - 1) + 1):
                for i in range(alphabet):
                    prob = ph[h - 1] * pd[h - 1, j - 1] * pa[h - 1, j - 1, i]
                    if prob <= min_prob:
                        continue
                    n_blks = h + 2 * i
                    lmin = min(n_blks, 2 * K)
                    # the positive diagonal
                    for k in range(states + 1):
                        if abs(k + i - j) > states:
                            continue
                        if k == 0 and h == 1 and i == 0:
                            continue
                        dst = k + i - j if k > j else i
                        for l in range(n_blks + 1, 2 * K + 1):
                            st1n[z + dst, z + dst, l - n_blks - 1] += st1[z + k, z + k, l - 1] * prob
                        acc = 0.0
                        for l in range(lmin):
                            acc += st1[z + k, z + k, l]
                        st2[z + dst] += acc * prob
                    # the 2D plane
                    for x in range(-states, 0):
                        for y in range(states + 1):
                            if x < -i:
                                dst_x = x + i - j
                                dst_y = max(0, y + i - j)
                            else:
                                dist2z = -x
                                tele = y - x
                                dst_x = max(0, tele + (i - dist2z) - j)
                                dst_y = dst_x
                            if min(dst_x, dst_y) < -states or max(dst_x, dst_y) > states:
                                continue
                            for l in range(n_blks + 1, 2 * K + 1):
                                st1n[z + dst_x, z + dst_y, l - n_blks - 1] += st1[z + x, z + y, l - 1] * prob
                            acc = 0.0
                            for l in range(lmin):
                                acc += st1[z + x, z + y, l]
                            st2[z + dst_x] += acc * prob
        st1 = st1n
    return st2


@njit(cache=True)
def _confirm_lb(K, pa_only, ph, pd, pa, st0, alphabet, states, steps, min_prob):
    """Port of ``PoSMCConfirmLB``: the Section 4.7 attack's success probability."""
    z = states
    err = 0.0
    st = np.zeros((states + 1, 2 * states + 1, K + 1))     # (L-p, S-p, k) with k one-based
    for i in range(states + 1):
        st[i, z, 0] = st0[z + i]
    for _ in range(steps):
        stn = np.zeros((states + 1, 2 * states + 1, K + 1))
        # (a=1, h=0)
        for l in range(states):
            for s in range(-states, states):
                for k in range(1, K + 1):
                    v = st[l, z + s, k - 1]
                    if v == 0.0:
                        continue
                    if s + 1 >= 0 and k + 1 > K:
                        err += v * pa_only
                    else:
                        stn[l + 1, z + s + 1, k] += v * pa_only
        # general symbols
        for h in range(1, alphabet + 1):
            for j in range(1, max(1, h - 1) + 1):
                for i in range(alphabet):
                    prob = ph[h - 1] * pd[h - 1, j - 1] * pa[h - 1, j - 1, i]
                    if prob <= min_prob:
                        continue
                    dp = j
                    for l in range(states + 1):
                        for s in range(-states, l + 1):
                            for k in range(1, K + 1):
                                v = st[l, z + s, k - 1]
                                if v == 0.0:
                                    continue
                                if s < 0:
                                    stmp = s + i - dp
                                    ltmp = max(0, l + i - dp)
                                else:
                                    stmp = max(0, s + i - dp)
                                    ltmp = l + i - dp
                                lnew = max(ltmp, stmp)
                                snew = min(ltmp, stmp)
                                knew = max(min(k + snew + dp - s, K + 1), 1)
                                if lnew > states or abs(snew) > states:
                                    continue
                                if snew >= 0 and knew > K:
                                    err += v * prob
                                else:
                                    stn[lnew, z + snew, knew - 1] += v * prob
        st = stn
    return err


def skipped_mass(sp: SlotPdf, alphabet: int, min_prob: float) -> float:
    """Total probability of the general symbols a ``min_prob`` cut leaves out of each step."""
    total = 0.0
    for h in range(1, alphabet + 1):
        for j in range(1, max(1, h - 1) + 1):
            p = sp.ph[h - 1] * sp.pd[h - 1, j - 1] * sp.pa[h - 1, j - 1, :alphabet]
            total += float(p[p <= min_prob].sum())
    return total


def error_ub(K: int, sp: SlotPdf, alphabet: int, states: int, min_prob: float = 0.0) -> float:
    """Upper bound on the chance that a block confirmed K blocks deep is ever displaced.

    ``min_prob`` skips general symbols of at most that probability (default: none, the exact
    port); ``skipped_mass`` reports what such a cut leaves out per step.
    """
    st0 = warmup(sp.pad, alphabet, states, upper=True)
    st2 = _confirm_ub(K, sp.pa_only, sp.ph, sp.pd, sp.pa, st0, alphabet, states, min_prob)
    return final_ub(sp.pad, st2, alphabet, states)


def lb_steps(K: int) -> int:
    """Phases the Section 4.7 attack is followed for.

    The original fixes 80, enough for its Table 1 (K <= 20) but not beyond: at a third of the
    stake and K = 60 the attack has not run its course by phase 80, and the bound collapses by
    nine orders of magnitude. ``max(80, 4K)`` keeps every Table 1 value and converges past it
    (``tests/test_lcbounds.py``).
    """
    return max(LB_STEPS, 4 * K)


def error_lb(K: int, sp: SlotPdf, alphabet: int, states: int, steps: int | None = None,
             min_prob: float = 0.0) -> float:
    """Lower bound: the success probability of the paper's Section 4.7 attack."""
    steps = lb_steps(K) if steps is None else steps
    st0 = warmup(sp.pad, alphabet, states, upper=False)
    return float(_confirm_lb(K, sp.pa_only, sp.ph, sp.pd, sp.pa, st0, alphabet, states, steps,
                             min_prob))
