"""Optimal selfish-mining strategy via the Sapirshtein–Sompolinsky–Zohar (2016) MDP.

§6.6 measures the *SM1* selfish strategy (Eyal–Sirer). SM1 is not optimal: an adversary can do
better by choosing, in each state, among {adopt, override, match, wait} rather than following the
fixed SM1 rule. SSZ cast this as an MDP over states ``(a, h, fork)`` — adversary secret-chain length
``a``, honest public-chain length ``h`` since the fork, and ``fork ∈ {irrelevant, relevant,
active}`` — and maximise the *relative* revenue ``adv/(adv+hon)``.

Because the objective is a ratio, we use the standard transform: for a candidate value ``rho`` the
per-step reward is ``(1-rho)·adv − rho·hon``; the optimal average reward ``g(rho)`` is decreasing in
``rho``, and the ``rho*`` where ``g(rho*) = 0`` is the optimal relative revenue. We find it by
bisection, solving each inner MDP by relative value iteration.

The optimal revenue is an upper bound on any selfish adversary's take; it lower-bounds the honest
stake threshold above which deviating pays. Used in §6.6 to bracket the real profit frontier.
"""

from __future__ import annotations

import numpy as np

# fork labels
IRRELEVANT, RELEVANT, ACTIVE = 0, 1, 2
# actions
ADOPT, OVERRIDE, MATCH, WAIT = 0, 1, 2, 3


def _build_states(cap: int):
    """Enumerate (a, h, fork) with 0<=a,h<=cap; return index maps."""
    states = [(a, h, f) for a in range(cap + 1) for h in range(cap + 1)
              for f in (IRRELEVANT, RELEVANT, ACTIVE)]
    index = {s: i for i, s in enumerate(states)}
    return states, index


def _transitions(a, h, f, action, alpha, gamma, cap):
    """Legal-action transition list: [(prob, (a',h',f'), adv_reward, hon_reward)].

    Returns None if the action is illegal in this state. At the cap, only adopt/override remain so
    the chain stays bounded (the optimal policy resolves long before the cap in the tested range).
    """
    beta = 1.0 - alpha
    at_cap = a >= cap or h >= cap

    if action == ADOPT:
        # abandon the secret chain; the h honest blocks are confirmed, then one block is mined
        return [(alpha, (1, 0, IRRELEVANT), 0, h),
                (beta, (0, 1, IRRELEVANT), 0, h)]

    if action == OVERRIDE:
        if a <= h:
            return None                        # need a strictly longer chain to override
        # publish h+1 blocks -> they override the public h; a-h-1 stay secret; then one block mined
        return [(alpha, (a - h, 0, IRRELEVANT), h + 1, 0),
                (beta, (a - h - 1, 1, RELEVANT), h + 1, 0)]

    if at_cap:
        return None                            # only adopt/override allowed at the boundary

    if action == WAIT:
        if f != ACTIVE:
            return [(alpha, (a + 1, h, IRRELEVANT), 0, 0),
                    (beta, (a, h + 1, RELEVANT), 0, 0)]
        if a < h:
            return None            # inconsistent (unreachable) active state: only adopt is valid
        # waiting while a fork is active: the same race dynamics as match
        return [(alpha, (a + 1, h, ACTIVE), 0, 0),
                (gamma * beta, (a - h, 1, RELEVANT), h, 0),      # adv's matched branch wins h
                ((1 - gamma) * beta, (a, h + 1, RELEVANT), 0, 0)]

    if action == MATCH:
        if not (f == RELEVANT and a >= h):
            return None                        # match needs equal-or-longer chain on a fresh tip
        return [(alpha, (a + 1, h, ACTIVE), 0, 0),
                (gamma * beta, (a - h, 1, RELEVANT), h, 0),
                ((1 - gamma) * beta, (a, h + 1, RELEVANT), 0, 0)]

    return None


_K = 3   # max successor branches of any (state, action)


def _precompute(alpha, gamma, states, index, cap):
    """Padded transition tensors (A, n, K) for a fully-vectorised value iteration, plus a legality
    mask. Independent of rho — built once per (alpha, gamma) and reused across the bisection."""
    n = len(states)
    probs = np.zeros((4, n, _K))
    nxt = np.zeros((4, n, _K), dtype=np.int64)
    radv = np.zeros((4, n, _K))
    rhon = np.zeros((4, n, _K))
    legal = np.zeros((4, n), dtype=bool)
    for i, (a, h, f) in enumerate(states):
        for action in (ADOPT, OVERRIDE, MATCH, WAIT):
            tr = _transitions(a, h, f, action, alpha, gamma, cap)
            if tr is None:
                continue
            legal[action, i] = True
            for b, (p, s2, ra, rh) in enumerate(tr):
                probs[action, i, b] = p
                nxt[action, i, b] = index[s2]
                radv[action, i, b] = ra
                rhon[action, i, b] = rh
    return probs, nxt, radv, rhon, legal


def _solve_mdp(pc, rho, ref, iters, tol):
    """Optimal average gain for the rho-parametrised reward, by *damped* relative value iteration.

    The chain is periodic, so undamped VI oscillates and a naive |Δgain| stop can false-trigger as
    the gain crosses zero. We damp (``V ← V + τ(TV − V)``) to break periodicity and stop on the
    textbook span criterion: at the average-reward fixed point ``TV − V = g·1`` (span → 0), and the
    gain ``g`` is that uniform increment. Returns the span-centre of the final Bellman increment.
    """
    probs, nxt, radv, rhon, legal = pc
    reward = (1.0 - rho) * radv - rho * rhon          # (4, n, K), constant across iterations
    V = np.zeros(probs.shape[1])
    tau = 0.5
    d = np.zeros(1)
    for _ in range(iters):
        q = (probs * (reward + V[nxt])).sum(axis=2)   # (4, n)
        q[~legal] = -1e18
        d = q.max(axis=0) - V                           # Bellman increment TV − V
        if d.max() - d.min() < tol:
            break
        V = V + tau * d
        V -= V[ref]                                     # anchor to keep values bounded
    return 0.5 * (d.max() + d.min())


def optimal_selfish_revenue(alpha: float, gamma: float, cap: int = 60,
                            iters: int = 4000, tol: float = 1e-10) -> float:
    """Optimal relative revenue adv/(adv+hon) for a selfish miner with stake ``alpha``, tie-break
    ``gamma``. Bisection on ``rho`` (the objective value), inner MDP by relative value iteration.

    Always ``>= max(alpha, SM1)``; equals ``alpha`` below the profitability threshold. ``cap``
    bounds the tracked lead and ``iters`` the value-iteration budget — both must grow *together*
    near ``alpha → 0.5`` (long leads). The defaults are converged to <1e-3 for ``alpha <= 0.46``;
    for ``alpha >= 0.47`` raise both (e.g. ``cap=80, iters=6000``) or the optimum is over-estimated
    by ~0.01 (cap-truncation + under-iteration). ``cap=16`` suffices for ``alpha <= 0.4``.
    """
    states, index = _build_states(cap)
    pc = _precompute(alpha, gamma, states, index, cap)
    ref = index[(1, 0, IRRELEVANT)]
    lo, hi = alpha - 1e-9, 1.0             # relative revenue in [alpha, 1)
    for _ in range(44):
        mid = 0.5 * (lo + hi)
        g = _solve_mdp(pc, mid, ref, iters, tol)
        if g > 0:                          # policy still profits at this rho -> true rho is higher
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)
