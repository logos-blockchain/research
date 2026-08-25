"""Scenarios: a network use pattern, a token valuation, and a population of machines.

One scenario is one run. The axes here are the exogenous inputs the model cannot derive --
how busy the network is, what a token is worth, who shows up with what hardware -- and
everything else is a consequence the simulator computes.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from .config import Config
from .market import DeviceClass


# ------------------------------------------------------------------ traffic patterns

def constant_traffic(level: int):
    def f(cfg: Config, epoch: int) -> int:
        return level
    f.label = f"flat@{level}"          # type: ignore[attr-defined]
    return f


def logistic_ramp(years_to_mature: float, start: int = 20, cap: int | None = None):
    """Traffic growing from ``start`` to capacity, maturing at ``years_to_mature``.

    The same shape the tokenomics report uses to size the endowment, so a run here and a
    figure there refer to the same ramp rather than to two different curves with one name.
    """
    def f(cfg: Config, epoch: int) -> int:
        top = cfg.max_block_txs if cap is None else cap
        epochs = years_to_mature * cfg.epochs_per_year
        if epochs <= 0:
            return top
        x = 12.0 * (epoch - epochs / 2) / epochs
        return int(start + (top - start) / (1 + math.exp(-x)))
    f.label = f"ramp@{years_to_mature}y"   # type: ignore[attr-defined]
    return f


# ------------------------------------------------------------------ token valuations

def constant_price(usd: float):
    def f(cfg: Config, epoch: int) -> float:
        return usd
    f.label = f"${usd:g}"              # type: ignore[attr-defined]
    return f


def price_ramp(start_usd: float, end_usd: float, years: float):
    """A token appreciating (or not) over the horizon, geometrically."""
    def f(cfg: Config, epoch: int) -> float:
        epochs = max(1.0, years * cfg.epochs_per_year)
        t = min(1.0, epoch / epochs)
        return start_usd * (end_usd / start_usd) ** t
    f.label = f"${start_usd:g}->${end_usd:g}@{years}y"   # type: ignore[attr-defined]
    return f


# ------------------------------------------------------------------ the scenario

@dataclass
class Scenario:
    """One point in the study's parameter space."""

    label: str
    classes: list[DeviceClass]
    mix: dict[str, float]                  # device class key -> arrival weight
    joiners_per_epoch: float
    epochs: int
    traffic: object = field(default_factory=lambda: constant_traffic(600))
    token_price: object = field(default_factory=lambda: constant_price(0.10))

    def __post_init__(self) -> None:
        keys = {c.key for c in self.classes}
        unknown = set(self.mix) - keys
        if unknown:
            raise ValueError(f"mix names classes that were not priced: {sorted(unknown)}. "
                             f"Available: {sorted(keys)}")
        total = sum(self.mix.values())
        if total <= 0:
            raise ValueError("mix weights must sum to something positive")

    @property
    def class_keys(self) -> list[str]:
        return [c.key for c in self.classes]

    def arrival_probabilities(self) -> np.ndarray:
        """Weight per class, in the order :attr:`classes` gives, normalised."""
        w = np.array([self.mix.get(c.key, 0.0) for c in self.classes], dtype=float)
        return w / w.sum()

    def rates(self) -> np.ndarray:
        return np.array([c.candidates_per_second for c in self.classes], dtype=float)

    def costs(self) -> np.ndarray:
        return np.array([c.cost_per_candidate_usd for c in self.classes], dtype=float)

    def cheapest_cost(self) -> float:
        """The class that sets the difficulty under free entry."""
        return float(min(c.cost_per_candidate_usd for c in self.classes))
