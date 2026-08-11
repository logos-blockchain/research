"""Load a config file into one immutable parameter object.

Every module takes a Params rather than importing constants, so the config file is the
single source of truth and two configs can be compared by running the same code twice.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

# Scalar field modulus of BN254: the space a puzzle ticket is drawn from.
P_FIELD = 21888242871839275222246405745257275088548364400416034343698204186575808495617


@dataclass(frozen=True)
class Params:
    name: str
    description: str
    # consensus
    N_b: int
    block_seconds: int
    epochs_per_year: float
    blocks_per_year: int
    max_block_txs: int
    # supply
    S_tge: float
    base_units_per_lgo: int
    I_max: float
    min_stake_fraction: float
    # fees
    price_floor: int
    price_resting: int
    claim_tx_bytes: int
    claim_tx_gas: int
    transfer_tx_bytes: int
    transfer_tx_gas: int
    # pow
    T: int
    beta_num: int
    beta_den: int
    rho_num: int
    rho_den: int
    genesis_pool_fraction: float
    F_ema: int
    P_ema: int
    reward_difficulty_exp: int
    # blend
    blend_base_exp: int
    blend_target_txs: int
    blend_damping_num: int
    blend_damping_den: int
    blend_max_step: int
    beta_max: int
    # work (measured)
    sec_per_candidate: float
    sec_per_candidate_opt: float
    sec_per_permutation: float
    pi5_slowdown: float
    pi5_slowdown_low: float
    pi5_slowdown_high: float
    pi5_cores: int
    # model assumptions
    n_tx_ref: int
    adversary_h: float
    honest_stake_fraction: float
    horizon_epochs: int

    # ---- derived, all denomination-free ----
    @property
    def rho(self) -> float:
        return self.rho_num / self.rho_den

    @property
    def beta(self) -> float:
        return self.beta_num / self.beta_den

    def claim_fee(self, price: int | None = None) -> float:
        """Fee of the claim + transfer transaction, in LGO, at the given price level."""
        p = self.price_resting if price is None else price
        return (self.claim_tx_bytes + self.claim_tx_gas) * p / self.base_units_per_lgo

    def transfer_fee(self, price: int | None = None) -> float:
        p = self.price_resting if price is None else price
        return (self.transfer_tx_bytes + self.transfer_tx_gas) * p / self.base_units_per_lgo

    @property
    def phi(self) -> float:
        """The claim fee at the resting price: the reference fee for every ratio."""
        return self.claim_fee()

    @property
    def psi(self) -> float:
        """Average transaction's fee over the claim's. Price level cancels."""
        return self.transfer_fee() / self.claim_fee()

    @property
    def r_max(self) -> float:
        """Maximum minted block reward, I_max * S_tge / blocks_per_year."""
        return self.I_max * self.S_tge / self.blocks_per_year

    @property
    def R0(self) -> float:
        """Genesis reward pool, in LGO."""
        return self.genesis_pool_fraction * self.S_tge

    @property
    def min_stake(self) -> float:
        return self.min_stake_fraction * self.S_tge


def load(path: str | Path) -> Params:
    cfg = tomllib.loads(Path(path).read_text())
    c, s, f, w, b, m, p = (cfg["consensus"], cfg["supply"], cfg["fees"],
                           cfg["work"], cfg["blend"], cfg["model"], cfg["pow"])
    return Params(
        name=cfg["name"], description=cfg["description"],
        N_b=c["blocks_per_epoch"], block_seconds=c["block_seconds"],
        epochs_per_year=c["epochs_per_year"], blocks_per_year=c["blocks_per_year"],
        max_block_txs=c["max_block_txs"],
        S_tge=s["tge"], base_units_per_lgo=s["base_units_per_lgo"],
        I_max=s["max_emission_per_year"], min_stake_fraction=s["min_stake_fraction"],
        price_floor=f["price_floor"], price_resting=f["price_resting"],
        claim_tx_bytes=f["claim_tx_bytes"], claim_tx_gas=f["claim_tx_gas"],
        transfer_tx_bytes=f["transfer_tx_bytes"], transfer_tx_gas=f["transfer_tx_gas"],
        T=p["target_claims_per_block"],
        beta_num=p["pool_share_num"], beta_den=p["pool_share_den"],
        rho_num=p["distribution_rate_num"], rho_den=p["distribution_rate_den"],
        genesis_pool_fraction=p["genesis_pool_fraction"],
        F_ema=p["ema_smoothing_factor"], P_ema=p["ema_smoothing_precision"],
        reward_difficulty_exp=p["reward_difficulty_exp"],
        blend_base_exp=b["difficulty_base_exp"], blend_target_txs=b["target_txs_per_block"],
        blend_damping_num=b["damping_num"], blend_damping_den=b["damping_den"],
        blend_max_step=b["max_step"], beta_max=b["beta_max"],
        sec_per_candidate=w["seconds_per_candidate"],
        sec_per_candidate_opt=w["seconds_per_candidate_opt"],
        sec_per_permutation=w["seconds_per_permutation"],
        pi5_slowdown=w["pi5_slowdown"], pi5_slowdown_low=w["pi5_slowdown_low"],
        pi5_slowdown_high=w["pi5_slowdown_high"], pi5_cores=w["pi5_cores"],
        n_tx_ref=m["reference_txs_per_block"], adversary_h=m["adversary_hashrate"],
        honest_stake_fraction=m["honest_stake_fraction"],
        horizon_epochs=m["horizon_epochs"],
    )
