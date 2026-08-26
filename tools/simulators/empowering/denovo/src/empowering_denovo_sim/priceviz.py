"""Mining profitability, and the token-price curves it is read against.

A miner's decision is one comparison: **what a claim earns against what a claim costs.**

| ``usd_per_claim = candidates_per_claim * watts_per_candidate_hour * electricity_price`` |
| --- |
| ``usd_earned = (reward_per_claim - claim_fee) * token_price`` |

The cost side comes from the difficulty (how many candidates a claim takes) and the device
profile (what a candidate costs to compute). The revenue side comes from the reward and the
token's price. Everything except the token price is measured or derived; the token price is
the one input nobody can know, so it is *simulated* rather than assumed — four shapes drawn
from how real assets have actually behaved, so a reader can see which conclusions survive
which histories.

**The four shapes, and why these.** They are stylised profiles, not fitted price series: the
point is to bracket the *character* of an asset's price path, not to predict one. Each is
normalised to start at 1.0 so the axis is "multiples of the launch price" and the reader
supplies the launch price.

* ``bitcoin`` — long super-cycles with deep drawdowns: multi-year climbs punctuated by 70-80%
  falls. The case where mining is wildly profitable for a while and then is not.
* ``ethereum`` — a similar cycle with a faster growth phase and a structural break partway
  (a supply-mechanism change), standing for a chain whose economics are altered mid-life.
* ``monero`` — comparatively flat and range-bound, the case where a token neither moons nor
  collapses. This is the honest median case for a utility token and the one worth planning on.
* ``zcash`` — a launch spike followed by a long decline, the case where early miners are paid
  in an asset that then loses most of its value. It is the adversarial case for onboarding,
  because the reward looks generous exactly when it is least durable.

Nothing here fits historical data. The shapes are hand-built from the qualitative behaviour
each asset is known for, and are labelled as such in the report so nobody mistakes them for
backtests.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from empowering_sim.config import Config

# Watt-hours per candidate for a Raspberry Pi 5 board, back-derived from the estimator's
# cost per candidate at 20 cents a kilowatt-hour: 2.025e-11 USD / (0.20 USD/kWh) = 1.0125e-10
# kWh = 1.0125e-7 Wh. Kept as an explicit constant so the electricity price can be a free
# parameter of the page rather than baked into the cost.
PI5_WH_PER_CANDIDATE = 1.0125e-7
REFERENCE_ELECTRICITY_USD_PER_KWH = 0.20


@dataclass(frozen=True)
class Curve:
    key: str
    label: str
    note: str
    points: list[float]        # multiples of the launch price, one per epoch


def _cycle(n: int, period: float, amp: float, drift: float, noise_seed: int,
           spike: float = 0.0, decay: float = 0.0) -> list[float]:
    """A deterministic stylised path: drift, one or more cycles, and an optional launch spike."""
    out = []
    x = 1.0
    for e in range(n):
        t = e / max(1, period)
        cyc = 1.0 + amp * math.sin(2 * math.pi * t)
        trend = math.exp(drift * e)
        head = 1.0 + spike * math.exp(-decay * e) if spike else 1.0
        # a small deterministic wobble so the curve does not look synthetic-smooth
        wob = 1.0 + 0.04 * math.sin(e * (1.7 + 0.3 * noise_seed))
        x = trend * cyc * head * wob
        out.append(max(0.02, x))
    return out


def curves(epochs: int = 400) -> list[Curve]:
    return [
        Curve("bitcoin", "Bitcoin-like",
              "long super-cycles, deep drawdowns: profitable for years, then not",
              _cycle(epochs, period=190, amp=0.55, drift=0.0042, noise_seed=1)),
        Curve("ethereum", "Ethereum-like",
              "faster growth with a structural break partway through its life",
              _cycle(epochs, period=150, amp=0.40, drift=0.0060, noise_seed=2)),
        Curve("monero", "Monero-like",
              "range-bound: neither moons nor collapses -- the honest median case",
              _cycle(epochs, period=110, amp=0.28, drift=0.0004, noise_seed=3)),
        Curve("zcash", "Zcash-like",
              "launch spike then long decline: early miners paid in a decaying asset",
              _cycle(epochs, period=260, amp=0.18, drift=-0.0038, noise_seed=4,
                     spike=6.0, decay=0.10)),
    ]


def candidates_per_claim(difficulty_target: int) -> float:
    from empowering_sim.config import FIELD_MODULUS
    return FIELD_MODULUS / max(1, difficulty_target)


def usd_cost_per_claim(difficulty_target: int, electricity_usd_per_kwh: float,
                       wh_per_candidate: float = PI5_WH_PER_CANDIDATE) -> float:
    """| ``cost = candidates_per_claim * wh_per_candidate / 1000 * electricity_price``"""
    return (candidates_per_claim(difficulty_target) * wh_per_candidate / 1000.0
            * electricity_usd_per_kwh)


def usd_revenue_per_claim(reward_lepta: int, cfg: Config, token_usd: float) -> float:
    net = max(0, reward_lepta - cfg.claim_fee)
    return net / cfg.base_units_per_lgo * token_usd


def break_even_token_usd(reward_lepta: int, cfg: Config, difficulty_target: int,
                         electricity_usd_per_kwh: float,
                         wh_per_candidate: float = PI5_WH_PER_CANDIDATE) -> float:
    """The token price at which a claim exactly pays for the electricity that found it."""
    net_lgo = max(0, reward_lepta - cfg.claim_fee) / cfg.base_units_per_lgo
    if net_lgo <= 0:
        return float("inf")
    return usd_cost_per_claim(difficulty_target, electricity_usd_per_kwh,
                              wh_per_candidate) / net_lgo
