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

:func:`optimal_policy_stats` reads a second quantity off the same solution: how the orphaned
blocks are *shaped*. The countable uncle model (§2.1) can reference only the **first block of a
fork**, so an override that discards ``h`` honest blocks — one chain — yields one countable
uncle, not ``h``. SM1 never lets the honest branch grow past 1 before acting, so under SM1 every
orphan is countable; the optimum *waits*, and that is what the first-fork restriction cannot
recover (§6.6).
"""

from __future__ import annotations

from dataclasses import dataclass

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
    """Legal-action transition list: [(prob, (a',h',f'), adv_reward, hon_reward, orph_hon,
    orph_adv)].

    Returns None if the action is illegal in this state. At the cap, only adopt/override remain so
    the chain stays bounded (the optimal policy resolves long before the cap in the tested range).

    ``orph_hon`` / ``orph_adv`` are the honest / adversary blocks *discarded* on that branch. They
    are carried here rather than re-derived downstream so the orphan accounting cannot drift from
    the race logic. Each is a **contiguous chain** rooted at the fork point, which is what makes the
    countable model's first-fork rule recover exactly one of them (:func:`optimal_policy_stats`).
    """
    beta = 1.0 - alpha
    at_cap = a >= cap or h >= cap

    if action == ADOPT:
        # abandon the secret chain; the h honest blocks are confirmed, then one block is mined.
        # The a secret blocks are discarded as one chain off the fork point.
        return [(alpha, (1, 0, IRRELEVANT), 0, h, 0, a),
                (beta, (0, 1, IRRELEVANT), 0, h, 0, a)]

    if action == OVERRIDE:
        if a <= h:
            return None                        # need a strictly longer chain to override
        # publish h+1 blocks -> they override the public h; a-h-1 stay secret; then one block mined
        return [(alpha, (a - h, 0, IRRELEVANT), h + 1, 0, h, 0),
                (beta, (a - h - 1, 1, RELEVANT), h + 1, 0, h, 0)]

    if at_cap:
        return None                            # only adopt/override allowed at the boundary

    if action == WAIT:
        if f != ACTIVE:
            return [(alpha, (a + 1, h, IRRELEVANT), 0, 0, 0, 0),
                    (beta, (a, h + 1, RELEVANT), 0, 0, 0, 0)]
        if a < h:
            return None            # inconsistent (unreachable) active state: only adopt is valid
        # waiting while a fork is active: the same race dynamics as match
        return [(alpha, (a + 1, h, ACTIVE), 0, 0, 0, 0),
                (gamma * beta, (a - h, 1, RELEVANT), h, 0, h, 0),  # adv's matched branch wins h
                ((1 - gamma) * beta, (a, h + 1, RELEVANT), 0, 0, 0, 0)]

    if action == MATCH:
        if not (f == RELEVANT and a >= h):
            return None                        # match needs equal-or-longer chain on a fresh tip
        return [(alpha, (a + 1, h, ACTIVE), 0, 0, 0, 0),
                (gamma * beta, (a - h, 1, RELEVANT), h, 0, h, 0),
                ((1 - gamma) * beta, (a, h + 1, RELEVANT), 0, 0, 0, 0)]

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
    ohon = np.zeros((4, n, _K))       # honest blocks discarded on the branch (one chain)
    oadv = np.zeros((4, n, _K))       # adversary blocks discarded on the branch (one chain)
    legal = np.zeros((4, n), dtype=bool)
    for i, (a, h, f) in enumerate(states):
        for action in (ADOPT, OVERRIDE, MATCH, WAIT):
            tr = _transitions(a, h, f, action, alpha, gamma, cap)
            if tr is None:
                continue
            legal[action, i] = True
            for b, (p, s2, ra, rh, oh, oa) in enumerate(tr):
                probs[action, i, b] = p
                nxt[action, i, b] = index[s2]
                radv[action, i, b] = ra
                rhon[action, i, b] = rh
                ohon[action, i, b] = oh
                oadv[action, i, b] = oa
    return probs, nxt, radv, rhon, ohon, oadv, legal


def _solve_reward(pc, reward, ref, iters, tol):
    """Optimal average gain for an arbitrary per-branch reward, by *damped* relative value
    iteration. Returns ``(gain, V)``.

    The chain is periodic, so undamped VI oscillates and a naive |Δgain| stop can false-trigger as
    the gain crosses zero. We damp (``V ← V + τ(TV − V)``) to break periodicity and stop on the
    textbook span criterion: at the average-reward fixed point ``TV − V = g·1`` (span → 0), and the
    gain ``g`` is that uniform increment. Returns the span-centre of the final Bellman increment.
    """
    probs, nxt, _radv, _rhon, _ohon, _oadv, legal = pc
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
    return 0.5 * (d.max() + d.min()), V


def _solve_mdp(pc, rho, ref, iters, tol):
    """Optimal average gain for the rho-parametrised *revenue* reward (the ratio transform)."""
    _probs, _nxt, radv, rhon, _ohon, _oadv, _legal = pc
    return _solve_reward(pc, (1.0 - rho) * radv - rho * rhon, ref, iters, tol)[0]


def _greedy_policy(pc, reward, V):
    """Greedy action per state, tie-broken toward the lowest index (ADOPT first, i.e. the
    least-deviating action) so near-ties resolve deterministically rather than arbitrarily."""
    probs, nxt, _radv, _rhon, _ohon, _oadv, legal = pc
    q = (probs * (reward + V[nxt])).sum(axis=2)
    q[~legal] = -1e18
    best = q.max(axis=0)
    return np.where(q >= best[None, :] - 1e-9, np.arange(4)[:, None], 99).min(axis=0)


def _stationary(pc, pol):
    """Stationary distribution of the policy-induced chain. The chain is periodic (see
    :func:`_solve_reward`), so iterate the LAZY chain — same stationary vector, no oscillation."""
    probs, nxt, *_ = pc
    n = probs.shape[1]
    rows = np.arange(n)
    p_s, n_s = probs[pol, rows], nxt[pol, rows]
    pi = np.full(n, 1.0 / n)
    for _ in range(500_000):
        new = 0.5 * pi + 0.5 * np.bincount(n_s.ravel(), weights=(pi[:, None] * p_s).ravel(),
                                           minlength=n)
        new /= new.sum()
        if np.abs(new - pi).max() < 1e-15:
            return new
        pi = new
    return pi


def _policy_rates(pc, pol, pi):
    """Per-block-finding-event rates under a policy's stationary distribution.

    Every MDP transition consumes exactly one block-finding event (the alpha/beta branch), so
    stationary per-step rates *are* per-event rates.
    """
    probs, nxt, radv, rhon, ohon, oadv, _legal = pc
    rows = np.arange(probs.shape[1])
    w = pi[:, None] * probs[pol, rows]
    oh, oa = ohon[pol, rows], oadv[pol, rows]
    return dict(
        adv_rate=float((w * radv[pol, rows]).sum()),
        hon_rate=float((w * rhon[pol, rows]).sum()),
        orphan_hon_blocks=float((w * oh).sum()),
        orphan_hon_runs=float((w * (oh > 0)).sum()),
        orphan_adv_blocks=float((w * oa).sum()),
        orphan_adv_runs=float((w * (oa > 0)).sum()),
    )


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
    return _bisect_revenue(pc, ref, alpha, iters, tol)


def _bisect_revenue(pc, ref, alpha, iters, tol):
    """Bisection on the ratio objective — the shared inner loop of the revenue solvers."""
    lo, hi = alpha - 1e-9, 1.0             # relative revenue in [alpha, 1)
    for _ in range(44):
        mid = 0.5 * (lo + hi)
        g = _solve_mdp(pc, mid, ref, iters, tol)
        if g > 0:                          # policy still profits at this rho -> true rho is higher
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


@dataclass
class OptimalPolicyStats:
    """Per-block-finding-event rates under the optimal policy's stationary distribution.

    Every MDP transition consumes exactly one block-finding event (the alpha/beta branch), so
    stationary per-step rates *are* per-event rates. ``deviates`` is False below the profitability
    threshold, where the optimum is honest mining and the MDP is indifferent across policies (the
    value-iteration policy is then arbitrary and its orphan structure meaningless).
    """
    alpha: float
    gamma: float
    revenue: float
    deviates: bool
    density_fraction: float        # canonical blocks per event — the raw TSI deflation factor
    orphan_hon_blocks: float       # honest blocks orphaned per event
    orphan_hon_runs: float         # honest orphan *chains* per event (1 countable uncle each)
    orphan_adv_blocks: float       # adversary blocks discarded per event
    orphan_adv_runs: float

    @property
    def countable_recovery(self) -> float:
        """Ceiling on the uncle-recovery fraction ``eta`` under the first-fork rule (§2.1).

        ``runs / blocks``: an override discards a *chain* of honest blocks and only its first is
        referenceable, so this is the largest ``eta`` the deployed counting rules admit — 1.0 under
        SM1 (which never buries a second block), below 1 whenever the policy waits.
        """
        if self.orphan_hon_blocks <= 0:
            return 1.0
        return self.orphan_hon_runs / self.orphan_hon_blocks

    @property
    def countable_recovery_adv(self) -> float:
        """The same ceiling on the attacker *self-uncling* its own abandoned chain (§6.7(a))."""
        if self.orphan_adv_blocks <= 0:
            return 1.0
        return self.orphan_adv_runs / self.orphan_adv_blocks

    def dhat_ratio(self, p_ref: float = 1.0, countable: bool = True) -> float:
        """Equilibrium ``D̂/D*`` = canonical density + the referenced share of honest orphans.

        ``countable=True`` counts one uncle per orphaned *chain* (the deployed rule);
        ``countable=False`` is the unrestricted baseline that counts every orphaned block.
        """
        rec = self.orphan_hon_runs if countable else self.orphan_hon_blocks
        return self.density_fraction + float(np.clip(p_ref, 0.0, 1.0)) * rec


def deflation_optimal_stats(alpha: float, gamma: float, p_ref: float = 1.0, cap: int = 64,
                            iters: int = 4000, tol: float = 1e-10) -> OptimalPolicyStats:
    """The policy that MINIMISES the estimate, rather than the one that maximises revenue.

    Both ceilings in §6.6 come from adversaries optimising something else — revenue (the SSZ
    objective) and reorg depth — so they bound ``eta`` from above without bounding the damage
    from below. This closes that gap by optimising the estimator directly.

    No ratio transform is needed, unlike the revenue objective. Every transition consumes exactly
    one block-finding event, and the estimate is

        D̂/D = (canonical blocks + p_ref · countable uncles) / events

    with one countable uncle per discarded honest *run* (§2.1). So the per-event contribution is
    ``radv + rhon + p_ref·[orphaned honest run]``, and minimising its long-run average is a plain
    average-reward MDP — solved by maximising the negated reward in one value-iteration pass.

    ``p_ref`` is the share of countable orphans that honest referencers actually pick up; at the
    default 1 the adversary faces the most effective possible repair, so the resulting deflation
    is the worst case it can force against a fully-cooperative honest network.

    **The unconstrained optimum is degenerate, and usefully so.** It is pure abstention: mine
    privately, publish nothing, adopt when overtaken. That drives ``D̂`` to exactly ``1 - alpha``
    and revenue to zero. But §6.4 already establishes that this is *correct* measurement rather
    than mis-measurement — a coalition that publishes nothing genuinely is not participating, and
    ``1 - alpha`` is the right answer for the stake that is. So the unconstrained objective asks
    the wrong question; the one that matters is how far ``D̂`` can be pushed by an adversary that
    stays profitable, which :func:`deflation_frontier` traces.
    """
    states, index = _build_states(cap)
    pc = _precompute(alpha, gamma, states, index, cap)
    probs, nxt, radv, rhon, ohon, oadv, legal = pc
    ref = index[(1, 0, IRRELEVANT)]

    dhat_step = radv + rhon + float(p_ref) * (ohon > 0)
    gain, V = _solve_reward(pc, -dhat_step, ref, iters, tol)
    pol = _greedy_policy(pc, -dhat_step, V)
    pi = _stationary(pc, pol)
    rates = _policy_rates(pc, pol, pi)

    # The gain IS the negated minimum estimate; cross-check it against the stationary rates so a
    # silent mismatch between the solver and the accounting cannot pass unnoticed.
    dhat = rates["adv_rate"] + rates["hon_rate"] + float(p_ref) * rates["orphan_hon_runs"]
    if abs(-gain - dhat) > 1e-6:
        raise AssertionError(f"deflation MDP gain {-gain:.9f} != stationary D-hat {dhat:.9f}")

    revenue = (rates["adv_rate"] / (rates["adv_rate"] + rates["hon_rate"])
               if rates["adv_rate"] + rates["hon_rate"] > 0 else 0.0)
    return OptimalPolicyStats(alpha=alpha, gamma=gamma, revenue=revenue, deviates=True,
                              density_fraction=rates["adv_rate"] + rates["hon_rate"],
                              orphan_hon_blocks=rates["orphan_hon_blocks"],
                              orphan_hon_runs=rates["orphan_hon_runs"],
                              orphan_adv_blocks=rates["orphan_adv_blocks"],
                              orphan_adv_runs=rates["orphan_adv_runs"])


def deflation_frontier(alpha: float, gamma: float, lam: float, p_ref: float = 1.0,
                       cap: int = 64, iters: int = 4000, tol: float = 1e-10) -> dict:
    """One point on the profit/deflation trade-off: the policy optimal for a mixed objective.

    Neither pure objective answers item 16. Maximising revenue ignores the estimator; minimising
    the estimate degenerates to abstention, which forfeits every block reward and is correctly
    measured anyway (:func:`deflation_optimal_stats`). What the report needs to know is how much
    deflation an adversary can force *while still being paid* — i.e. the Pareto frontier between
    the two.

    Sweeping ``lam`` from 0 upward traces it: the per-event reward is
    ``lam · (adversary blocks) − (contribution to D̂)``, so ``lam = 0`` is the deflation optimum
    and large ``lam`` approaches the revenue optimum. The point of interest is where the revenue
    *share* crosses ``alpha`` — an adversary doing at least as well as honest mining — because
    below that the attack is self-punishing griefing already bounded by §6.5.
    """
    states, index = _build_states(cap)
    pc = _precompute(alpha, gamma, states, index, cap)
    _probs, _nxt, radv, rhon, ohon, _oadv, _legal = pc
    ref = index[(1, 0, IRRELEVANT)]

    reward = float(lam) * radv - (radv + rhon + float(p_ref) * (ohon > 0))
    _gain, V = _solve_reward(pc, reward, ref, iters, tol)
    pol = _greedy_policy(pc, reward, V)
    rates = _policy_rates(pc, pol, _stationary(pc, pol))
    canonical = rates["adv_rate"] + rates["hon_rate"]
    blocks, runs = rates["orphan_hon_blocks"], rates["orphan_hon_runs"]
    revenue = (rates["adv_rate"] / canonical) if canonical > 0 else 0.0
    return dict(
        alpha=alpha, gamma=gamma, lam=lam,
        revenue=revenue,
        reward_per_stake=(revenue / alpha) if alpha else 0.0,
        density_fraction=canonical,
        dhat_countable=canonical + float(p_ref) * runs,
        dhat_unrestricted=canonical + float(p_ref) * blocks,
        eta=(runs / blocks) if blocks > 0 else 1.0,
        orphan_hon_blocks=blocks,
    )


def optimal_policy_stats(alpha: float, gamma: float, cap: int = 64,
                         iters: int = 4000, tol: float = 1e-10) -> OptimalPolicyStats:
    """Orphan structure of the *optimal* selfish policy — the input the countable model needs.

    Solves the same MDP as :func:`optimal_selfish_revenue`, then reads the greedy policy off the
    value function at the optimal ``rho``, finds its stationary distribution, and accumulates the
    per-event canonical / orphan rates carried on the transition table.

    ``cap`` must be larger here than for the revenue alone: the revenue converges once long leads
    are rare, but the orphan *shape* keeps changing while the policy still waits near the cap
    (measured drift at alpha = 0.45 is ~0.005 in eta from cap 48 to 64, ~0.0003 at alpha = 0.4).
    """
    states, index = _build_states(cap)
    pc = _precompute(alpha, gamma, states, index, cap)
    probs, nxt, radv, rhon, ohon, oadv, legal = pc
    ref = index[(1, 0, IRRELEVANT)]
    revenue = _bisect_revenue(pc, ref, alpha, iters, tol)

    # Below the profitability threshold the optimum is honest mining (revenue == alpha) and the MDP
    # is indifferent among many policies; report the honest outcome rather than an arbitrary one.
    if revenue <= alpha * (1.0 + 1e-6):
        return OptimalPolicyStats(alpha=alpha, gamma=gamma, revenue=revenue, deviates=False,
                                  density_fraction=1.0, orphan_hon_blocks=0.0,
                                  orphan_hon_runs=0.0, orphan_adv_blocks=0.0,
                                  orphan_adv_runs=0.0)

    # Recover V at the optimal rho, then read off the greedy policy and its stationary rates.
    reward = (1.0 - revenue) * radv - revenue * rhon
    _gain, V = _solve_reward(pc, reward, ref, iters, tol)
    pol = _greedy_policy(pc, reward, V)
    rates = _policy_rates(pc, pol, _stationary(pc, pol))
    return OptimalPolicyStats(
        alpha=alpha, gamma=gamma, revenue=revenue, deviates=True,
        density_fraction=rates["adv_rate"] + rates["hon_rate"],
        orphan_hon_blocks=rates["orphan_hon_blocks"],
        orphan_hon_runs=rates["orphan_hon_runs"],
        orphan_adv_blocks=rates["orphan_adv_blocks"],
        orphan_adv_runs=rates["orphan_adv_runs"],
    )
