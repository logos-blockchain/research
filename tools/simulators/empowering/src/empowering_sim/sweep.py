"""Sweeps: expand a grid of scenarios, run each, and report where the model works.

A working region is the set of parameter values at which every one of the model's conditions
holds at once. The point of reporting them separately is that the conjunction alone says a
cell fails without saying *which* constraint bound it, and that is the part that tells you
what to change.

Cells are run with common random numbers -- the same seed for every cell -- so that a
difference between two cells is a difference in the parameters and not in the draws. That is
the paired-design discipline the uncle-model simulator uses for the same reason.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Callable, Iterable

import numpy as np

from . import market, simulate
from .config import Config
from .scenarios import Scenario, constant_price, constant_traffic


@dataclass
class Cell:
    """One grid point and what came out of it."""

    axes: dict
    constraints: dict
    excluded: list[str]
    graduates: int
    pooled_equivalent: int
    final_break_even: float
    min_mining_fraction: float

    @property
    def works(self) -> bool:
        """Every condition holds: the pool funds itself, claiming pays, somebody mines,
        and the on-ramp seats at least one participant."""
        c = self.constraints
        return bool(c.get("self_funding") and c.get("claiming_continues")
                    and c.get("mining_never_died") and c.get("graduated_any"))


def grid(**axes: Iterable) -> list[dict]:
    """Cartesian product of named axes, as a list of dicts."""
    keys = list(axes)
    return [dict(zip(keys, combo)) for combo in itertools.product(*(axes[k] for k in keys))]


def run_grid(cfg: Config, points: list[dict],
             build: Callable[[Config, dict], Scenario],
             seed: int = 1) -> list[Cell]:
    """Run every grid point under common random numbers."""
    cells = []
    for point in points:
        scenario = build(cfg, point)
        rng = np.random.default_rng(seed)          # same draws in every cell, deliberately
        pop, out = simulate.run(cfg, scenario, rng)
        con = simulate.constraints(cfg, pop, out, scenario)
        cells.append(Cell(
            axes=dict(point),
            constraints=con,
            excluded=simulate.excluded_classes(pop, out, scenario),
            graduates=con.get("graduates", 0),
            pooled_equivalent=con.get("pooled_equivalent", 0),
            final_break_even=con.get("break_even_price_final", float("nan")),
            min_mining_fraction=con.get("min_mining_fraction", 0.0),
        ))
    return cells


# ------------------------------------------------------------------ the standard programme

def default_builder(classes, mix, epochs: int):
    """Build a scenario from a grid point over token price, joiners and traffic."""
    def build(cfg: Config, point: dict) -> Scenario:
        return Scenario(
            label=",".join(f"{k}={v}" for k, v in point.items()),
            classes=classes, mix=mix,
            joiners_per_epoch=point.get("joiners", 1.0),
            epochs=epochs,
            traffic=constant_traffic(point.get("txs", 600)),
            token_price=constant_price(point.get("price", 0.10)),
        )
    return build


def affordability_frontier(cfg: Config, classes, epochs: int = 120,
                           joiners: float = 2.0, seed: int = 1) -> list[dict]:
    """At what token price does each device class stop being able to mine?

    Swept rather than solved, because the answer is a fixed point: a class leaving relaxes
    the difficulty, which lowers the price at which it would have left. What the sweep shows
    is where the field settles once that has played out.
    """
    prices = [10 ** e for e in np.arange(-6.0, 0.5, 0.5)]
    rows = []
    for price in prices:
        scenario = Scenario(
            label=f"price={price:g}", classes=classes,
            mix={c.key: 1.0 for c in classes},
            joiners_per_epoch=joiners, epochs=epochs,
            traffic=constant_traffic(600), token_price=constant_price(price),
        )
        pop, out = simulate.run(cfg, scenario, np.random.default_rng(seed))
        last = out[-1]
        rows.append(dict(
            price=price,
            mining=last.mining, miners=last.miners,
            by_class=dict(zip(scenario.class_keys, last.active_by_class)),
            candidates_per_claim=last.candidates_per_claim,
            break_even=last.break_even_price,
            graduates=pop.graduated,
        ))
    return rows
