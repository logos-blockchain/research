"""The mining population: who is here, what they have earned, and who has graduated.

**Why crediting once per epoch is exact, not a shortcut.** The engine draws claims block by
block because the retarget is a per-block controller. Attribution to nodes does not have to
follow it. Within one epoch the reward is a constant, so a node's earnings depend only on how
many of the epoch's claims it won, not on which blocks they fell in; and the number of claims
a node wins over an epoch is the sum of its per-block Poisson counts, which is Poisson at the
epoch rate. Conditional on the epoch's total, the split across nodes is multinomial in exactly
the way it is conditional on a block's total. So one multinomial per epoch carries the same
joint distribution as 21,600 of them, and costs one.

The one thing this gives up is *within-epoch ordering* -- which node's claim was the one the
pool could no longer cover. That is immaterial here: the engine has already decided how many
claims the pool paid, and every paid claim is worth the same amount, so who got them does not
change the pool's trajectory. Ordering would matter only if the reward varied inside an
epoch, and it does not.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import Config

NOT_GRADUATED = -1


@dataclass
class Population:
    """Miners, as flat arrays. Preallocated, because arrivals are known in advance."""

    arrived_epoch: np.ndarray      # int32
    mining_units: np.ndarray       # float64 -- device-equivalents each node contributes
    balance: np.ndarray            # int64, base units, net of the fees paid to claim
    claims: np.ndarray             # int64
    graduated_epoch: np.ndarray    # int32, NOT_GRADUATED until the minimum stake is reached
    device_class: np.ndarray       # int32, index into the scenario's device classes
    candidates_per_second: np.ndarray   # float64, one machine of that class
    cost_per_candidate_usd: np.ndarray  # float64, at the scenario's electricity price
    active: np.ndarray             # bool, currently finds the work worth doing
    count: int = 0

    @classmethod
    def empty(cls, capacity: int) -> "Population":
        return cls(
            arrived_epoch=np.full(capacity, NOT_GRADUATED, dtype=np.int32),
            mining_units=np.zeros(capacity, dtype=np.float64),
            balance=np.zeros(capacity, dtype=np.int64),
            claims=np.zeros(capacity, dtype=np.int64),
            graduated_epoch=np.full(capacity, NOT_GRADUATED, dtype=np.int32),
            device_class=np.zeros(capacity, dtype=np.int32),
            candidates_per_second=np.zeros(capacity, dtype=np.float64),
            cost_per_candidate_usd=np.zeros(capacity, dtype=np.float64),
            active=np.zeros(capacity, dtype=bool),
            count=0,
        )

    @property
    def capacity(self) -> int:
        return self.mining_units.size

    @property
    def total_units(self) -> float:
        return float(self.mining_units[:self.count].sum())

    @property
    def graduated(self) -> int:
        return int((self.graduated_epoch[:self.count] != NOT_GRADUATED).sum())

    def arrive(self, n: int, epoch: int, units_each: float = 1.0) -> int:
        """Add ``n`` nodes at ``epoch``. Returns how many were actually seated."""
        if n <= 0:
            return 0
        seated = min(n, self.capacity - self.count)
        if seated <= 0:
            return 0
        lo, hi = self.count, self.count + seated
        self.arrived_epoch[lo:hi] = epoch
        self.mining_units[lo:hi] = units_each
        self.count = hi
        return seated

    def arrive_classed(self, n: int, epoch: int, class_ids: np.ndarray,
                       rates: np.ndarray, costs: np.ndarray) -> int:
        """Seat ``n`` nodes carrying a device class, its search rate and its cost."""
        seated = self.arrive(n, epoch, units_each=1.0)
        if seated <= 0:
            return 0
        lo, hi = self.count - seated, self.count
        ids = class_ids[:seated]
        self.device_class[lo:hi] = ids
        self.candidates_per_second[lo:hi] = rates[ids]
        self.cost_per_candidate_usd[lo:hi] = costs[ids]
        self.active[lo:hi] = False
        return seated

    def hashrate_weights(self) -> np.ndarray:
        """Search power each node actually contributes: its rate if mining, else nothing."""
        live = slice(0, self.count)
        return np.where(self.active[live], self.candidates_per_second[live], 0.0)

    def credit(self, rng: np.random.Generator, claims_paid: int, net_per_claim: int,
               epoch: int, min_stake: int, weights: np.ndarray | None = None) -> int:
        """Deal an epoch's paid claims out to miners and record any graduations.

        ``net_per_claim`` is what a miner keeps: the reward less the fee it paid to submit
        the claim. ``weights`` overrides the default equal-device weighting, and is how a
        population of unequal machines -- or one where some have stopped mining -- is
        attributed correctly. Returns how many nodes graduated this epoch.
        """
        if self.count == 0 or claims_paid <= 0:
            return 0
        units = self.mining_units[:self.count] if weights is None else weights
        total = units.sum()
        if total <= 0:
            return 0

        won = rng.multinomial(claims_paid, units / total)
        self.claims[:self.count] += won
        if net_per_claim > 0:
            self.balance[:self.count] += won * net_per_claim

        pending = self.graduated_epoch[:self.count] == NOT_GRADUATED
        newly = pending & (self.balance[:self.count] >= min_stake)
        n_new = int(newly.sum())
        if n_new:
            self.graduated_epoch[:self.count][newly] = epoch
        return n_new

    # ------------------------------------------------------------------ reporting

    def credit_groups(self, rng: np.random.Generator, group_claims: np.ndarray,
                      net_per_claim: int, epoch: int, min_stake: int) -> int:
        """Credit each device class its own share, then split within the class.

        Two stages because participation is decided per class -- every member of a class
        faces the same cost, so they enter and leave together -- while attribution within a
        class is uniform. Splitting in one multinomial over all nodes would be wrong once
        classes spend different fractions of the epoch mining.
        """
        if self.count == 0:
            return 0
        live = slice(0, self.count)
        classes = self.device_class[live]
        for k, claims_k in enumerate(group_claims):
            n = int(round(float(claims_k)))
            if n <= 0:
                continue
            members = np.flatnonzero(classes == k)
            if members.size == 0:
                continue
            won = rng.multinomial(n, np.full(members.size, 1.0 / members.size))
            self.claims[members] += won
            if net_per_claim > 0:
                self.balance[members] += won * net_per_claim

        pending = self.graduated_epoch[live] == NOT_GRADUATED
        newly = pending & (self.balance[live] >= min_stake)
        n_new = int(newly.sum())
        if n_new:
            self.graduated_epoch[live][newly] = epoch
        return n_new

    def time_to_graduate(self) -> np.ndarray:
        """Epochs each graduated node took, from arrival. Only for those who made it."""
        live = slice(0, self.count)
        got = self.graduated_epoch[live] != NOT_GRADUATED
        return (self.graduated_epoch[live][got] - self.arrived_epoch[live][got]).astype(np.int64)

    def cohort_summary(self, cfg: Config) -> list[dict]:
        """One row per arrival cohort: how many arrived, how many made it, how long it took."""
        live = slice(0, self.count)
        arrived = self.arrived_epoch[live]
        grad = self.graduated_epoch[live]
        out = []
        for e in np.unique(arrived):
            in_cohort = arrived == e
            made_it = in_cohort & (grad != NOT_GRADUATED)
            took = (grad[made_it] - e) if made_it.any() else np.array([], dtype=np.int64)
            out.append(dict(
                cohort_epoch=int(e),
                cohort_years=float(e / cfg.epochs_per_year),
                arrived=int(in_cohort.sum()),
                graduated=int(made_it.sum()),
                share=float(made_it.sum() / in_cohort.sum()) if in_cohort.any() else 0.0,
                median_epochs=float(np.median(took)) if took.size else float("nan"),
                median_years=float(np.median(took) / cfg.epochs_per_year) if took.size
                else float("nan"),
            ))
        return out
