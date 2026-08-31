"""Whether a bonded miner keeps mining — decided by the miner, not set by the modeller.

Every headline in this study is quoted twice, under a `retiring` regime and a `persistent`
one, because the specification does not say which obtains and nothing in the mechanism pays
for either. That is honest but weak: two hand-set flags standing in for a decision that has an
answer. This module computes the answer.

**Why the break-even the adversarial analysis uses is not sufficient.** §2.1 there prices the
marginal claim as `PoW reward - electricity` and concludes mining stays rational. A bonded
provider's decision is a portfolio decision, and mining buys it a second thing: the endowment
is finite and fully spent, so **every `min_stake` of LGO an incumbent mines is exactly one
newcomer bond that never happens**. Fewer providers means a larger share of a service pot that
is split flat and does not grow with adoption, so suppressing the on-ramp pays the incumbent a
dividend for as long as the network runs. A model that omits that term cannot see it.

The term is included here, and the arithmetic is the point rather than the conclusion:

| `mine iff  (income + exclusion_dividend) * token_price  >  electricity` |
| --- |

where the dividend is `(income / min_stake) * (blend_pool / providers^2) * horizon` — the
bonds displaced, times what each displacement is worth per epoch, times how long the incumbent
counts. The `providers^2` is what makes this interesting: the dividend is enormous while
providers are few and vanishes once they are many, so the incentive to strangle the on-ramp is
strongest exactly when the network is least able to survive it.

**What is assumed, stated rather than buried.** The service pot is a parameter here, not a
model: importing the emission chain that produces it would drag token-value estimation into an
engine that deliberately has none. Its default is measured — `empowering_sim.strategies` settles
at 1,235,274 LGO an epoch — and `sweep_pool` exists because the result should be read against
that assumption rather than through it. The horizon is finite and undiscounted; a discount rate
would only shrink the dividend, and the dividend is already too small to change the answer past
a few hundred providers. Unbonded miners are not modelled as choosing: they are saving for a
bond, which is the whole point of being here.

**The limitation that matters most, because it shapes the output.** Income and cost both scale
linearly with hashrate, so the comparison is *hashrate-independent* and every bonded miner
decides identically: the model can only ever return 0% or 100%, never a mixed equilibrium. Near
the break-even it therefore oscillates period-2 — everyone quits, the field thins, each
survivor's share rises, everyone returns — which is the same bang-bang the Q9 participation
cliff produces, and for the same reason. A real population differs in electricity price,
hardware efficiency, and how far ahead it looks, so it would settle at a *fraction* mining
where this model flips the whole field. **Read the flip epoch as the point where the marginal
operator leaves, not as a claim that the field empties in one epoch.**
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from empowering_sim.services import MIN_PROVIDERS

from .params import Derived
from .priceviz import PI5_WH_PER_CANDIDATE

# Measured: the median epoch of `empowering_sim.strategies.run` at its default config, once
# the emission factor has settled. The first epochs are far below it while stake is thin.
# Pinned at the source by the empowering suite's "settled blend pool" gate, so a change to
# the emission machinery (e.g. the PR-375 pooling substrate, which left it exactly here)
# fails a gate there instead of silently invalidating the conclusions computed from it here.
BLEND_POOL_LGO_PER_EPOCH = 1_235_274.0


@dataclass(frozen=True)
class Rational:
    """A bonded miner keeps mining iff the marginal epoch pays for itself.

    ``count_exclusion`` toggles the second term, which is the whole reason this module exists:
    running the same population with it off measures what the naive break-even would have
    concluded, so the two can be compared rather than argued about.
    """

    token_usd: float = 1.0
    electricity_usd_per_kwh: float = 0.20
    blend_pool_lgo: float = BLEND_POOL_LGO_PER_EPOCH
    horizon_epochs: int = 195
    count_exclusion: bool = True
    # Optional epoch -> factor on the electricity cost. The acceptance-window study feeds
    # the congestion tax through here: when offered demand exceeds block space, expired
    # solutions burn energy without paying, so the effective cost per PAID claim inflates
    # by offered/included (window.py). None means 1.0 everywhere -- the default economics,
    # and every previously pinned result, are unchanged.
    cost_multiplier: object = None

    def keeps_mining(self, d: Derived, hashrate: np.ndarray, bonded: np.ndarray,
                     budget_lepta: int, rate_prev: float, providers: int,
                     epoch: int = 0) -> np.ndarray:
        """Per-miner decision for the bonded set. Returns a bool array over all miners.

        ``rate_prev`` is the previous epoch's live hashrate: a miner deciding at the boundary
        knows the field it competed against last epoch, not the one it is about to face. That
        keeps the decision non-circular.
        """
        cfg = d.cfg
        out = np.zeros(hashrate.shape, dtype=bool)
        if not bonded.any() or rate_prev <= 0:
            return out

        lgo = cfg.base_units_per_lgo
        epoch_seconds = cfg.blocks_per_epoch * cfg.block_seconds

        # What the epoch pays this miner: its share of a budget that is spent either way.
        share = hashrate / rate_prev
        income_lgo = share * (budget_lepta / lgo)

        # What the epoch costs it: grinding is continuous, so energy follows hashrate and
        # wall-clock, not the claims that happen to land.
        cost_usd = (hashrate * epoch_seconds * PI5_WH_PER_CANDIDATE / 1000.0
                    * self.electricity_usd_per_kwh)
        if self.cost_multiplier is not None:
            cost_usd = cost_usd * float(self.cost_multiplier(epoch))

        dividend_lgo = np.zeros_like(income_lgo)
        if self.count_exclusion and providers >= MIN_PROVIDERS:
            displaced = income_lgo / (cfg.min_stake / lgo)
            per_epoch = self.blend_pool_lgo / float(providers) ** 2
            dividend_lgo = displaced * per_epoch * self.horizon_epochs

        pays = (income_lgo + dividend_lgo) * self.token_usd > cost_usd
        out[bonded] = pays[bonded]
        return out


def price_curve(d: Derived, prices=(10.0, 1.0, 0.20, 0.10, 0.05, 0.02, 0.01),
                epochs: int = 240, **kw) -> list[dict]:
    """How much of the bootstrap incumbents suppress, as a function of the token price.

    The counter-intuitive direction is the point: mining income is denominated in LGO and its
    cost in dollars, so a HIGHER token price makes incumbent mining more attractive, sustains
    it further into the phase, and onboards FEWER people. The reference triple's headline
    figure needs a token worth under a cent.
    """
    from . import arrivals, engine, study                        # noqa: PLC0415

    rows = []
    for p in prices:
        r = engine.run(d, arrivals.uniform(220, 130), study.hashrate_draw(d.cfg),
                       epochs=epochs, retirement_policy=Rational(token_usd=p, **kw))
        boot = [q for q in r.rows if q.bootstrap]
        broke = next((q.epoch for q in boot if q.persisting <= 0.5 and q.epoch > 2), None)
        rows.append({"token_usd": p,
                     "persists_until": broke if broke is not None else d.bootstrap_epochs,
                     "bonds": r.rows[-1].bonds_total})
    return rows


def sweep_pool(d: Derived, pools, **kw) -> list[dict]:
    """The result against the one number this module assumes rather than derives."""
    from . import arrivals, engine, study                        # noqa: PLC0415

    rows = []
    for pool in pools:
        r = engine.run(d, arrivals.uniform(220, 130), study.hashrate_draw(d.cfg), epochs=360,
                       retirement_policy=Rational(blend_pool_lgo=pool, **kw))
        # Mid-bootstrap, not end-of-run: post-phase everyone has retired in every run, so an
        # end-state column reads 0.0 regardless of the pool and says nothing about the sweep.
        mid = d.bootstrap_epochs // 2
        rows.append({"blend_pool_lgo": pool, "bonds": r.rows[-1].bonds_total,
                     "transition": r.transition_epoch,
                     "persisting_mid_bootstrap": r.rows[mid].persisting})
    return rows
