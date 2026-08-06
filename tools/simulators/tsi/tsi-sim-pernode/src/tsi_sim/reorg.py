"""Private-chain "deepest-reorg" adversary: how deep a reorganisation an attacker can force.

A coalition holding stake fraction ``alpha`` mines a HIDDEN chain off the current public tip
and releases it to override the public chain — the classic longest-chain private-chain attack,
here run to maximise the *depth* of the override (the number of honest blocks discarded), which
is the cost a reorg imposes, rather than to maximise revenue (that is §6.6's selfish MDP).

Because the density engine reads a window past k-finality where the chain is settled, the race
is a global longest-chain race, so we model it directly (as §6.6 does) rather than in the
per-node loop. Two ingredients tie it to the protocol parameters:

* **Effective adversary share.** Honest blocks orphaned by natural forks (Blend delay) do not
  extend the public chain, so they do not count in the race. With honest orphan rate ``o`` (the
  engine's ``fork_rate`` at 0 % adversary), the adversary's *effective* share of chain-extending
  blocks is ``alpha_eff = alpha / (alpha + (1-alpha)(1-o))`` — deeper honest forking *helps* the
  attacker. Keeping the operating point at ``rho < 1`` (low ``o``) is therefore also what keeps
  reorgs shallow. Uncle references change what is *counted*, not the longest-chain race, so they
  do **not** change reorg depth.
* **Deepest-reorg strategy.** The adversary's lead ``L = adv_len - pub_len`` is a random walk:
  ``+1`` w.p. ``alpha_eff`` (adversary extends privately), ``-1`` w.p. ``1-alpha_eff`` (honest
  extends the public chain). Each excursion above 0 is one attack; the deepest reorg it can force
  is the maximum lead reached (release the private chain at its peak, displacing that many public
  confirmations). ``P(depth >= d) = (alpha_eff/(1-alpha_eff))**d`` (``alpha_eff < 1/2``) is the
  Nakamoto/Rosenfeld gambler's-ruin *catch-up* probability — the chance an adversary ``d`` blocks
  behind ever draws level — an upper bound on that per-attack maximum, not its exact distribution
  (which is smaller). ``fig27`` plots the occupancy Monte-Carlo; §6.10's 4/8/17 and 8/15/34 are the
  engine's realised reorg depths.
"""

from __future__ import annotations

import numpy as np


def alpha_effective(alpha: float, orphan_rate: float) -> float:
    """Adversary share of chain-extending blocks, given honest orphan rate ``o``."""
    honest_eff = (1.0 - alpha) * (1.0 - orphan_rate)
    denom = alpha + honest_eff
    return alpha / denom if denom > 0 else 0.0


def reorg_depth_tail(alpha_eff: float, d: int) -> float:
    """Closed-form ``P(reorg depth >= d)`` (gambler's-ruin). 1.0 for ``alpha_eff >= 1/2``."""
    if d <= 0:
        return 1.0
    if alpha_eff >= 0.5:
        return 1.0
    if alpha_eff <= 0.0:
        return 0.0
    return (alpha_eff / (1.0 - alpha_eff)) ** d


def simulate_deepest_reorg(alpha_eff: float, n_events: int,
                           rng: np.random.Generator) -> np.ndarray:
    """Monte-Carlo the deepest-reorg strategy; return the reorg depth of each attack (excursion).

    Walks the lead over ``n_events`` block events. An excursion is one private-chain attempt (from
    when the adversary first pulls ahead until the public chain ties it back); its reorg depth is
    the maximum lead reached — the public confirmations the adversary displaces by releasing at
    the peak. Validates the closed-form tail :func:`reorg_depth_tail`.
    """
    steps = rng.random(n_events) < alpha_eff       # True = adversary extends
    depths = []
    lead = 0
    peak = 0
    for adv in steps:
        if adv:
            lead += 1
            peak = max(peak, lead)
        elif lead > 0:
            lead -= 1
            if lead == 0:                          # excursion closes: record its deepest reorg
                depths.append(peak)
                peak = 0
        # honest block at lead 0 -> canonical growth, no attack in progress
    return np.asarray(depths, dtype=np.int64)


def countable_recovery_from_depths(depths: np.ndarray) -> float:
    """Share of reorg-discarded public blocks the countable model can reference back (§6.6).

    A depth-``d`` reorg displaces ``d`` *consecutive* public blocks. They form one chain rooted at
    the fork point, and the countable model can reference only the block whose parent lies on the
    referencing chain — so one of the ``d`` is recoverable into the density and ``d-1`` are not.
    Over a run of attacks that ceiling is ``attacks / blocks = len(depths) / sum(depths)``.

    This is the depth-*maximising* adversary's value; the revenue-maximising one is
    :func:`tsi_sim.selfish_mdp.optimal_policy_stats`. Neither is a worst case for the estimator —
    an adversary optimising deflation directly would trade revenue for depth.
    """
    d = np.asarray(depths, dtype=np.int64)
    total = int(d.sum())
    return (d.size / total) if total else 1.0
