"""Phase B3: the delay-scheduling attacker on Cryptarchia's slot lottery (PLAN.md B3).

The attack is the one the B1 lower bound evaluates: Gaži, Ren and Russell, ePrint 2022/1571
(revision 2025-05-02), §4.7, as coded in ``PoWMCWarmupLB`` and ``PoSMCConfirmLB`` of LCanalysis.
Here it is played on per-slot lottery outcomes instead of the code's continuous-time symbol
distribution.

- **Lottery.** A slot holds an honest win with probability ``1 - (1 - f)^(1 - alpha)`` and an
  adversarial win with probability ``1 - (1 - f)^alpha``, independently: the engine's per-node
  lottery, aggregated. A chain holds one block per slot.
- **Delay.** Every honest block reaches the other honest nodes ``delta`` slots after its slot. An
  honest win adds to the honest chain's depth only when it comes more than ``delta`` slots after
  the last win that did.
- **Symbols.** As LCanalysis cuts time: a phase opens at an honest win and closes after
  ``delta`` slots without one. It carries the depth ``d`` its honest wins add and the slots ``a``
  the adversary wins in it. A slot the adversary wins outside a phase is a symbol of its own.
- **Before the target**, the adversary's lead over the public depth follows
  ``lead' = max(0, lead + a - d)``.
- **After the target**, the adversary keeps two chains, ``L`` and ``S``, at offsets ``x >= y``
  from the public depth. Its wins extend both. An adversary-only symbol adds one to each. A phase
  adds the honest depth to ``L`` while ``y < 0`` and to ``S`` otherwise; a chain that would fall
  below the public depth takes the honest chain instead. ``k`` counts the blocks ``S`` gains,
  from one at the target.
- **Failure at depth K.** The code counts a failure only at the symbol where ``k`` first exceeds
  ``K``, when ``y >= 0`` there; it drops the other paths. That is ``at_confirmation``. The attack
  also succeeds when ``y >= 0`` at any later symbol: ``ever``. Both are followed for
  ``max(80, 4K)`` symbols. Every symbol boundary is a target, as in the code.
"""

from __future__ import annotations

import numpy as np
from numba import njit


@njit(cache=True)
def _symbols(n_slots, p_h, p_a, delta, seed):
    """Symbols (d, a) of n_slots slots; d = -1 marks an adversary-only symbol."""
    np.random.seed(seed)
    cap = int(n_slots * (p_h + p_a) * 1.5) + 1000
    d_out = np.empty(cap, np.int64)
    a_out = np.empty(cap, np.int64)
    n = 0
    in_phase = False
    depth, adv, quiet, last = 0, 0, 0, 0
    for t in range(n_slots):
        h = np.random.random() < p_h
        a = np.random.random() < p_a
        if not in_phase:
            if h:
                in_phase = True
                depth, adv, quiet, last = 1, int(a), 0, t
            elif a:
                d_out[n] = -1
                a_out[n] = 1
                n += 1
        else:
            adv += int(a)
            if h:
                quiet = 0
                if t - last > delta:
                    depth += 1
                    last = t
            else:
                quiet += 1
            if quiet >= delta:
                d_out[n] = depth
                a_out[n] = adv
                n += 1
                in_phase = False
        if n >= cap - 1:
            break
    return d_out[:n], a_out[:n]


@njit(cache=True)
def _attack(d_sym, a_sym, k_max, burn):
    """Failures per depth K = 1..k_max (index K-1), at confirmation and ever, and the targets."""
    n = d_sym.size
    steps_max = max(80, 4 * k_max)
    at_conf = np.zeros(k_max, np.int64)
    ever = np.zeros(k_max, np.int64)
    targets = 0
    lead = 0
    ks = np.empty(steps_max, np.int64)
    ys = np.empty(steps_max, np.int64)
    best = np.empty(steps_max, np.int64)
    for j0 in range(n - steps_max):
        if j0 >= burn:
            targets += 1
            x, y, k, b = lead, 0, 1, 0
            for step in range(steps_max):
                d, a = d_sym[j0 + step], a_sym[j0 + step]
                if d < 0:
                    x += 1
                    y += 1
                    k += 1
                else:
                    if y < 0:
                        s_tmp = y + a - d
                        l_tmp = max(0, x + a - d)
                    else:
                        s_tmp = max(0, y + a - d)
                        l_tmp = x + a - d
                    x_new, y_new = max(l_tmp, s_tmp), min(l_tmp, s_tmp)
                    k = k + y_new + d - y
                    x, y = x_new, y_new
                if y >= 0 and k > b:
                    b = k
                ks[step], ys[step], best[step] = k, y, b
            st = 0
            for kk in range(1, k_max + 1):
                lim = max(80, 4 * kk)
                while st < steps_max and ks[st] <= kk:      # k never falls
                    st += 1
                if st < lim and ys[st] >= 0:
                    at_conf[kk - 1] += 1
                if best[lim - 1] > kk:
                    ever[kk - 1] += 1
        d, a = d_sym[j0], a_sym[j0]
        lead = max(0, lead + a - max(d, 0))
    return at_conf, ever, targets


@njit(cache=True)
def _timelines(n_slots, p_h, p_a, delta, seed):
    """The same draws as _symbols: slots of depth-adding honest wins, and of adversarial wins."""
    np.random.seed(seed)
    honest = np.empty(int(n_slots * p_h * 1.5) + 1000, np.int64)
    adv = np.empty(int(n_slots * p_a * 1.5) + 1000, np.int64)
    nh, na, last = 0, 0, -(1 << 40)
    for t in range(n_slots):
        h = np.random.random() < p_h
        a = np.random.random() < p_a
        if h and t - last > delta:
            honest[nh] = t
            nh += 1
            last = t
        if a:
            adv[na] = t
            na += 1
        if nh >= honest.size - 1 or na >= adv.size - 1:
            break
    return honest[:nh], adv[:na]


def occupancy(f: float, share: float) -> float:
    return 1.0 - (1.0 - f) ** share


def attack(alpha: float, f: float, delta: int, n_slots: int, k_max: int, seed: int,
           burn: int = 2000) -> tuple[np.ndarray, np.ndarray, int]:
    """Failures at depths 1..k_max, at confirmation and ever, over one run's targets."""
    d_sym, a_sym = _symbols(n_slots, occupancy(f, 1.0 - alpha), occupancy(f, alpha), delta,
                            seed)
    return _attack(d_sym, a_sym, k_max, burn)


def timelines(alpha: float, f: float, delta: int, n_slots: int,
              seed: int) -> tuple[np.ndarray, np.ndarray]:
    """The honest chain's block slots and the adversary's winning slots of the same run."""
    return _timelines(n_slots, occupancy(f, 1.0 - alpha), occupancy(f, alpha), delta, seed)
