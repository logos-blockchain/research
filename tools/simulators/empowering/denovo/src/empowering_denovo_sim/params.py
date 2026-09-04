"""The three parameters, their derived quantities, and the consistency identity.

Everything else this simulator uses is inherited from `empowering_sim`'s verified config --
the fee model, the transaction sizes, the retarget constants, the ledger units -- so the
de-novo design's claim of three parameters is enforced structurally: this module cannot
introduce a fourth without it showing here.
"""
from __future__ import annotations

from dataclasses import dataclass

from empowering_sim.config import Config, load

# Conversion efficiency -- the fraction of pool payout that reaches bonds -- MEASURED IN THIS
# MECHANISM rather than imported from the old design's elevation study, which reported
# 11.4%/51.9% at a single arrival rate. Measuring it here showed that is not one number per
# regime but two different shapes:
#
#   persistent (nobody retires):  13.9% / 15.9% / 14.6% at 65 / 130 / 260 arrivals an epoch
#                                 -- essentially FLAT: everyone keeps mining, so the field
#                                 grows with the arrival rate and dilution cancels the gain.
#   retiring:                     24.9% / 49.3% / 64.2% at the same rates (re-measured
#                                 2026-09 on the 3-permutation basis; the fast rate read
#                                 74.1% on the naive one -- block space now clips it)
#                                 -- strongly RISING: retirement frees claim share for the
#                                 next cohort, so faster arrival converts better.
#
# So retirement is not a caveat on one figure; it changes what kind of quantity the efficiency
# is. Under persistence a triple's feasibility is a property of the triple alone; under
# retirement it also depends on how fast nodes turn up.
EFFICIENCY_PERSISTENT = 0.15          # flat, and what the incentives actually deliver
EFFICIENCY_RETIRING_SLOW = 0.25       # at half the reference arrival rate
EFFICIENCY_RETIRING_FAST = 0.64       # at twice it (0.74 before block space bound)

# Retiring is NOT incentivised: a bonded node can provide service and go on mining, and the
# marginal claim pays at any plausible token price (adversarial-analysis section 2). All
# figures are on the four-core board basis of `power.py`. The
# default regime for a feasibility check is therefore the persistent one.
EFFICIENCY_DEFAULT = EFFICIENCY_PERSISTENT


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
        """| ``anchor = claim_fee + tx_fee(transfer)`` -- R8, re-struck 2026-09-05.

        The claim covers its own inclusion and delivers one average transaction of value.
        Struck as ``2 * avg_tx_fee`` until the 2026-09 upstream claim signature made a
        claim cost 2.03 transfers and pushed that anchor 140 lepta under the claim's own
        fee; the re-strike (design owner, 2026-09-05) writes R1's guarantee into the
        definition itself, so no future movement of the claim's fee ratio can reopen it --
        the surplus is one transfer BY CONSTRUCTION, not by coincidence of the ratio.

        Read from the fee model at its resting prices; in a full market simulation this is
        re-read at each epoch boundary.
        """
        return self.cfg.claim_fee + self.cfg.avg_tx_fee

    @property
    def satisfiable(self) -> bool:
        """Feasible under the regime the incentives deliver -- persistence.

        A triple asserting more than the persistent efficiency is betting on a behaviour
        nothing pays for. `satisfiable_if_retiring` reports the optimistic reading beside it,
        because a design owner is entitled to take that bet knowingly.
        """
        return self.implied_efficiency <= EFFICIENCY_PERSISTENT

    @property
    def satisfiable_if_retiring(self) -> bool:
        return self.implied_efficiency <= EFFICIENCY_RETIRING_FAST

    @property
    def regime_note(self) -> str:
        e = self.implied_efficiency
        if e <= EFFICIENCY_PERSISTENT:
            return "feasible under either regime"
        if e <= EFFICIENCY_RETIRING_SLOW:
            return "needs retirement, and works even at slow arrival"
        if e <= EFFICIENCY_RETIRING_FAST:
            return "needs retirement AND fast arrival -- a bet on two behaviours"
        return "infeasible under any measured regime"

    def check(self, allow_retiring: bool = True) -> "Derived":
        """The parameterisation-time gate.

        ``allow_retiring`` admits a triple that only works if bonded miners stop mining --
        the default, because that is the reading both designs have quoted, but the result
        carries `regime_note` so the bet is visible rather than assumed.
        """
        ok = self.satisfiable_if_retiring if allow_retiring else self.satisfiable
        if not ok:
            raise UnsatisfiableTriple(
                f"({self.triple.pool_fraction:.3%}, {self.triple.expected_nodes:,}, "
                f"{self.triple.expected_years} yr) implies a conversion efficiency of "
                f"{self.implied_efficiency:.1%}: {self.regime_note}")
        return self

    def opening_sub_pool(self) -> int:
        return self.endowment_genesis // self.bootstrap_epochs

    def opening_reward(self) -> int:
        """Genesis: `claims_prev = 0`, so the divisor floors at the block count."""
        return max(self.anchor, self.opening_sub_pool() // self.cfg.blocks_per_epoch)
