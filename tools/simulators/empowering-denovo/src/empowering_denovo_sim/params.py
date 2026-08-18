"""The three parameters, their derived quantities, and the consistency identity.

Everything else this simulator uses is inherited from `empowering_sim`'s verified config --
the fee model, the transaction sizes, the retarget constants, the ledger units -- so the
de-novo design's claim of three parameters is enforced structurally: this module cannot
introduce a fourth without it showing here.
"""
from __future__ import annotations

from dataclasses import dataclass

from empowering_sim.config import Config, load

# The measured conversion-efficiency band (elevation study, EmPoWering-simulator branch):
# the fraction of pool payout that reaches bonds, bracketed by whether bonded miners retire.
EFFICIENCY_PERSISTENT = 0.114
EFFICIENCY_RETIRING = 0.519


class UnsatisfiableTriple(ValueError):
    """The (pool, nodes, years) triple implies a conversion efficiency outside the band."""


@dataclass(frozen=True)
class Triple:
    """The R4 parameters. Everything downstream is derived."""

    pool_fraction: float = 0.005
    expected_nodes: int = 25_000
    expected_years: float = 4.0

    def derived(self, cfg: Config | None = None) -> "Derived":
        cfg = cfg or load()
        endowment = round(self.pool_fraction * cfg.launch_supply * cfg.base_units_per_lgo)
        epochs = round(self.expected_years * cfg.epochs_per_year)
        implied = self.expected_nodes * cfg.min_stake / endowment
        return Derived(triple=self, cfg=cfg, endowment_genesis=endowment,
                       bootstrap_epochs=epochs, implied_efficiency=implied)


@dataclass(frozen=True)
class Derived:
    triple: Triple
    cfg: Config
    endowment_genesis: int          # lepta
    bootstrap_epochs: int
    implied_efficiency: float

    @property
    def anchor(self) -> int:
        """| ``anchor = 2 * tx_fee(transfer)`` -- R8, with transfer ~= inscription.

        Read from the fee model at its resting prices; in a full market simulation this is
        re-read at each epoch boundary.
        """
        return 2 * self.cfg.avg_tx_fee

    @property
    def satisfiable(self) -> bool:
        return EFFICIENCY_PERSISTENT <= self.implied_efficiency <= EFFICIENCY_RETIRING

    def check(self) -> "Derived":
        """The parameterisation-time gate: reject an unsatisfiable triple before running."""
        if not self.satisfiable:
            raise UnsatisfiableTriple(
                f"({self.triple.pool_fraction:.3%}, {self.triple.expected_nodes:,}, "
                f"{self.triple.expected_years} yr) implies a conversion efficiency of "
                f"{self.implied_efficiency:.1%}, outside the measured "
                f"[{EFFICIENCY_PERSISTENT:.1%}, {EFFICIENCY_RETIRING:.1%}] band")
        return self

    def opening_sub_pool(self) -> int:
        return self.endowment_genesis // self.bootstrap_epochs

    def opening_reward(self) -> int:
        """Genesis: `claims_prev = 0`, so the divisor floors at the block count."""
        return max(self.anchor, self.opening_sub_pool() // self.cfg.blocks_per_epoch)
