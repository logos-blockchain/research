"""Selfish / private-chain block withholding, and its interaction with TSI.

§6.5 modelled withholding as *abstention* — a coalition that discards its own blocks to deflate the
active-stake estimate — and found it strictly unprofitable (the forfeit is a dead loss). The classic
"block withholding" attack is different and stronger: the coalition mines a **private chain** and
**releases** it to orphan honest blocks (Eyal & Sirer, *Majority is not Enough*, 2013), recovering
the forfeit. This module models that adversary and its TSI-specific coupling.

Why a global longest-chain race (not the per-node arrival engine): TSI reads density from a window
buried far past k-finality, where every node provably agrees on the canonical chain (§3.1). The
selfish/honest outcome is decided by that single finalized chain, so the standard block-level race —
with a network tie-break parameter ``gamma`` (fraction of honest miners that build on the
adversary's block in a same-length race) — is the faithful, exact tool for the reward and density.

Two quantities matter:
  * **revenue share** ``adv/(adv+hon)`` — the adversary's fraction of *canonical* blocks. Above the
    selfish threshold (``alpha > (1-gamma)/(3-2*gamma)``; 1/3 at gamma=0) it exceeds the stake
    share ``alpha`` — i.e. private-chain withholding IS profitable, unlike §6.5's abstention.
  * **canonical density fraction** ``(adv+hon)/events`` < 1 — orphaned honest blocks go uncounted,
    so TSI measures a low density and **deflates ``D̂`` to ``D*``·(density fraction)**. Uncle
    references (§6.3–6.4) recover orphaned honest blocks into the count, blunting the deflation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def selfish_revenue_closed_form(alpha: float, gamma: float) -> float:
    """Eyal–Sirer relative revenue of the selfish pool (fraction of canonical blocks).

    ``R = [a(1-a)^2 (4a + g(1-2a)) - a^3] / [1 - a(1 + (2-a)a)]`` (a=alpha, g=gamma).
    Exceeds ``alpha`` above the profitability threshold ``alpha > (1-gamma)/(3-2gamma)``.
    """
    a, g = float(alpha), float(gamma)
    num = a * (1 - a) ** 2 * (4 * a + g * (1 - 2 * a)) - a ** 3
    den = 1 - a * (1 + (2 - a) * a)
    return num / den


def selfish_threshold(gamma: float) -> float:
    """Stake fraction above which selfish mining out-earns honest: ``(1-gamma)/(3-2gamma)``."""
    return (1 - gamma) / (3 - 2 * gamma)


@dataclass
class RaceResult:
    adv: int              # adversary blocks on the canonical chain
    hon: int              # honest blocks on the canonical chain
    orphan_hon: int       # honest blocks orphaned by adversary overrides (recoverable via uncles)
    orphan_adv: int       # adversary private blocks that lost a race (dead)
    events: int           # total block-finding events

    @property
    def revenue_share(self) -> float:
        c = self.adv + self.hon
        return self.adv / c if c else 0.0

    @property
    def density_fraction(self) -> float:
        """Counted canonical blocks / all mined blocks — the factor TSI deflates ``D̂`` by."""
        return (self.adv + self.hon) / self.events if self.events else 1.0


def simulate_selfish(is_adv: np.ndarray, gamma: float, rng: np.random.Generator) -> RaceResult:
    """Eyal–Sirer SM1 selfish-mining race over a stream of block-finding events.

    ``is_adv[i]`` marks whether event ``i`` was found by the adversary pool. Honest miners build on
    the public head; the adversary builds a private chain and reveals it per SM1. ``gamma`` is the
    tie-race bias. Reward is assigned to the canonical (surviving) branch at each resolution.

    State ``k`` = adversary's hidden lead over the public branch; ``tie`` = the 1–1 race state 0'.
    """
    k = 0                      # adversary private lead
    tie = False                # in the 0' (1–1 race) state
    adv = hon = orphan_hon = orphan_adv = 0
    for x in np.asarray(is_adv, dtype=bool):
        if tie:                                    # resolving a 1–1 race (adversary revealed 1)
            if x:                                  # adversary extends its branch -> it wins
                adv += 2
                orphan_hon += 1                    # the honest matching block is orphaned
            elif rng.random() < gamma:             # honest builds on adversary block -> adv wins
                adv += 1
                hon += 1
                orphan_hon += 1                    # the honest matcher is orphaned by the race
            else:                                  # honest builds on honest block -> honest wins
                hon += 2
                orphan_adv += 1                    # the adversary's revealed block is orphaned
            tie = False
            k = 0
            continue
        if x:                                      # adversary found a block: extend private chain
            k += 1
        elif k == 0:                               # honest found, adversary no lead -> honest wins
            hon += 1
        elif k == 1:                               # honest matches a 1-lead -> reveal 1, race 0'
            tie = True
            k = 0
        elif k == 2:                               # honest chips a 2-lead -> reveal all, override
            adv += 2
            orphan_hon += 1                        # the honest block is orphaned
            k = 0
        else:                                      # k > 2: reveal one to stay ahead, orphan honest
            adv += 1
            orphan_hon += 1
            k -= 1
    # flush: adversary reveals any remaining private lead (longer -> canonical)
    if tie:
        hon += 1                                   # unresolved tie: honest keeps its block (H),
        orphan_adv += 1                            # the adversary's revealed matcher is lost
    adv += k
    return RaceResult(adv=adv, hon=hon, orphan_hon=orphan_hon, orphan_adv=orphan_adv,
                      events=int(np.asarray(is_adv).size))


def race_from_alpha(alpha: float, n_events: int, gamma: float,
                    rng: np.random.Generator) -> RaceResult:
    """Convenience: a Bernoulli(``alpha``) event stream of ``n_events`` blocks through the race."""
    is_adv = rng.random(n_events) < alpha
    return simulate_selfish(is_adv, gamma, rng)


@dataclass
class RewardParams:
    """A configurable block/uncle reward schedule (all rewards as a fraction of a block reward = 1).

    ``w_uncle`` — paid to the *producer* of an orphaned block referenced as an uncle (GHOST/Ethereum
        style). Compensates a miner whose block was orphaned by latency (§3.2).
    ``w_nephew`` — paid to the block that *references* an uncle (per uncle). Incentivises inclusion.

    The reference game is strategic — who references whom decides who is compensated — so three rate
    knobs model it (all fractions in [0,1]):
      ``p_ref``      — honest orphans that get referenced. Under the SOFT (reward-weighted)
                       inclusion rule (§6.8) this is EMERGENT and high: an honest orphan is
                       published, so any honest canonical block within ``W`` references it for the
                       nephew reward; the attacker only suppresses on its own blocks. Rises toward 1
                       with ``W``; driven low only by deep reorgs whose orphans age out (residual).
      ``p_ref_adv``  — the attacker's OWN revealed-but-lost blocks (``orphan_adv``) that it
                       self-uncles to recover reward. A rational attacker → 1.
      ``adv_nephew`` — of the honest orphans that are referenced, the fraction whose *nephew* reward
                       the attacker captures (its canonical block did the referencing — e.g. forced
                       to under a mandate). 0 without a mandate (honest blocks reference); >0 with.

    Safety constraint (§6.7): self-uncling a block pays ``w_uncle + w_nephew``; orphaning a block
    you could have made canonical to farm that pays iff ``w_uncle + w_nephew > 1``, so a sound
    schedule needs **w_uncle + w_nephew < 1**.
    """
    w_uncle: float = 0.0
    w_nephew: float = 0.0
    p_ref: float = 1.0
    p_ref_adv: float = 0.0
    adv_nephew: float = 0.0

    @classmethod
    def mandatory(cls, w_uncle: float, w_nephew: float = 0.0,
                  adv_region_frac: float = 0.5) -> RewardParams:
        """The ``p_ref = 1`` limit — every in-window uncle referenced. NOT a deployed *hard mandate*
        (a validity rule cannot prove what forks a producer saw, §6.8 — rejected for fork-safety);
        this is the large-``W`` / full-honest-referencer limit that the SOFT rule *approaches*. The
        resulting share is ``≈ α`` with a small residual premium that grows with alpha (~0 near 1/3,
        +0.006 at 0.4, +0.014 at 0.46). Two-
        type model: no ``W``/``U`` queue, so ``p_ref`` is a knob, not derived — real coverage is
        ``< 1``, set by ``W``/visibility (see the ``p_ref`` sweep in scripts/reward_mandate.py)."""
        return cls(w_uncle=w_uncle, w_nephew=w_nephew, p_ref=1.0, p_ref_adv=1.0,
                   adv_nephew=adv_region_frac)


@dataclass
class RewardSplit:
    adv_reward: float
    hon_reward: float

    @property
    def adv_reward_share(self) -> float:
        t = self.adv_reward + self.hon_reward
        return self.adv_reward / t if t else 0.0


def reward_shares(race: RaceResult, rp: RewardParams) -> RewardSplit:
    """Reward-weighted split under an uncle-reward schedule (block reward = 1 per canonical block).

    Four reference flows (uncle -> producer, nephew -> referencer): honest orphans referenced
    (uncle -> honest; nephew -> honest, or -> attacker for the ``adv_nephew`` fraction it must
    reference); and the attacker's own lost blocks self-uncled (uncle **and** nephew -> attacker).
    ``adv_reward_share`` is the attacker's fraction of *total issued reward*.
    """
    adv, hon = race.adv, race.hon
    if adv + hon == 0:
        return RewardSplit(0.0, 0.0)
    ref_hon = rp.p_ref * race.orphan_hon               # honest orphans compensated (uncle->honest)
    ref_adv = rp.p_ref_adv * race.orphan_adv           # attacker self-uncles its own lost blocks
    hon_reward = (hon + rp.w_uncle * ref_hon           # honest uncle producers
                  + rp.w_nephew * ref_hon * (1.0 - rp.adv_nephew))   # honest nephews
    adv_reward = (adv + rp.w_nephew * ref_hon * rp.adv_nephew        # attacker-captured nephews
                  + (rp.w_uncle + rp.w_nephew) * ref_adv)            # self-uncle: producer + nephew
    return RewardSplit(adv_reward=adv_reward, hon_reward=hon_reward)


def honest_reward_recovery(race: RaceResult, rp: RewardParams) -> float:
    """Fraction of honest miners' *mined* value they actually collect (fairness metric).

    Without uncle rewards an honest miner loses everything for a latency-orphaned block; with them
    it recovers ``w_uncle`` per referenced orphan. Returns
    ``(hon + w_uncle·p_ref·orphan_hon) / (hon + orphan_hon)`` — 1.0 means fully compensated.
    """
    mined = race.hon + race.orphan_hon
    if mined == 0:
        return 1.0
    return (race.hon + rp.w_uncle * rp.p_ref * race.orphan_hon) / mined


def tsi_dhat_ratio(race: RaceResult, uncle_recovery: float) -> float:
    """Equilibrium ``D̂/D*`` under a selfish attack with uncle recovery.

    TSI drives the *counted* density to ``f``; the counted density is the canonical fraction plus a
    recovered fraction ``uncle_recovery ∈ [0,1]`` of the orphaned HONEST blocks (referenced back as
    uncles — adversary blocks reference none, §6.4). ``D̂/D* = (adv + hon + u*orphan_hon)/events``.
    """
    u = float(np.clip(uncle_recovery, 0.0, 1.0))
    counted = race.adv + race.hon + u * race.orphan_hon
    return counted / race.events if race.events else 1.0
