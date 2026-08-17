"""Protocol constants and simulation settings, loaded into one immutable object.

Protocol values come from ``configs/protocol-snapshot.toml``, a deliberate copy of the
tokenomics config rather than a live read of it -- see that file's header for why.

Names follow the tokenomics report's section 1.0 notation table, so a quantity is called the
same thing here, there, and in the specification. Where the protocol computes in base units
the fields are integers and stay integers; only dimensionless ratios are floats.
"""
from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

# Scalar field modulus of BN254: the space a ticket is drawn from.
FIELD_MODULUS = 21888242871839275222246405745257275088548364400416034343698204186575808495617

_SNAPSHOT = Path(__file__).parent / "configs" / "protocol-snapshot.toml"


@dataclass(frozen=True)
class Config:
    """One run's parameters. Frozen, validated on construction."""

    # ---- consensus ----
    blocks_per_epoch: int
    block_seconds: int
    epochs_per_year: float
    blocks_per_year: int
    max_block_txs: int

    # ---- supply, in LGO and in base units ----
    launch_supply: float
    base_units_per_lgo: int
    min_stake_fraction: float

    # ---- fees, in base units per byte and per gas unit ----
    price_resting: int
    claim_tx_bytes: int
    claim_tx_gas: int
    transfer_tx_bytes: int
    transfer_tx_gas: int

    # ---- proof of work ----
    target_claims_per_block: int
    pow_share_num: int
    pow_share_den: int
    distribution_rate_num: int
    distribution_rate_den: int
    genesis_pool_fraction: float
    smoothing_factor: int
    smoothing_precision: int
    reward_difficulty_exp: int

    # ---- emission and the leader's take ----
    # max_emission_per_year is specified. The two shares are NOT: the report records the
    # leader fee share as unset and nowhere in the specification tree, and carries 0.4 as a
    # modelling choice. Anything downstream of them is conditional on that choice, and the
    # crossover study is entirely downstream of them.
    inscribe_gas: int = 56
    max_emission_per_year: float = 0.01
    leader_fee_share: float = 0.4
    leader_reward_share: float = 1.0

    # ---- measured device data ----
    # Not protocol constants: these are benchmark results, and they belong in the cost
    # estimator once it exists. They live here meanwhile so the engine's hashrate
    # calibration can be gated against a published figure rather than left unchecked.
    seconds_per_candidate_reward: float = 0.0
    reference_cores: int = 1

    # ---- simulation settings (not protocol; this simulator's own) ----
    seed: int = 0
    horizon_epochs: int = 300
    txs_per_block: int = 600
    refill_timing: str = "epoch"          # "epoch" | "block" -- see economics.accrue
    adversary_hashrate: float = 0.33
    honest_stake_frac: float = 1.0
    initial_stake: float = 0.0            # share of supply already staked at launch

    # ---- provenance ----
    snapshot_path: str = ""
    label: str = "specified"

    def __post_init__(self) -> None:
        self._validate()

    # ------------------------------------------------------------------ derived

    @property
    def distribution_rate(self) -> float:
        return self.distribution_rate_num / self.distribution_rate_den

    @property
    def pow_share(self) -> float:
        return self.pow_share_num / self.pow_share_den

    @property
    def smoothing(self) -> float:
        """The retarget's EMA weight. The report shows this is the controller's one dial."""
        return self.smoothing_factor / self.smoothing_precision

    @property
    def claim_fee(self) -> int:
        """What a claim transaction costs to submit, in base units, at the resting price."""
        return (self.claim_tx_bytes + self.claim_tx_gas) * self.price_resting

    @property
    def avg_tx_fee(self) -> int:
        """The average transaction, taken as an ordinary transfer at the resting price."""
        return (self.transfer_tx_bytes + self.transfer_tx_gas) * self.price_resting

    @property
    def fee_ratio(self) -> float:
        """Average transaction's fee over a claim's. The price level cancels."""
        return self.avg_tx_fee / self.claim_fee

    @property
    def genesis_pool(self) -> int:
        """The pool's endowment at launch, in base units."""
        return round(self.genesis_pool_fraction * self.launch_supply * self.base_units_per_lgo)

    @property
    def min_stake(self) -> int:
        """Minimum stake to participate in consensus, in base units."""
        return round(self.min_stake_fraction * self.launch_supply * self.base_units_per_lgo)

    @property
    def genesis_difficulty_target(self) -> int:
        return FIELD_MODULUS >> self.reward_difficulty_exp

    @property
    def blocks_in_horizon(self) -> int:
        return self.horizon_epochs * self.blocks_per_epoch

    def to_lgo(self, base_units: float) -> float:
        return base_units / self.base_units_per_lgo

    # ------------------------------------------------------------------ checks

    def _validate(self) -> None:
        """Refuse a configuration the model cannot honestly evaluate.

        The controller check is the substantive one: the report derives a pole of
        ``smoothing_factor / smoothing_precision``, so a factor at or above the precision is
        not a slower controller but a non-convergent one, and every reconvergence figure
        would be silent nonsense rather than a visible failure.
        """
        if self.target_claims_per_block <= 0:
            raise ValueError(
                f"target_claims_per_block must be > 0, got {self.target_claims_per_block}")
        if self.pow_share_den <= 0 or not (0 <= self.pow_share_num <= self.pow_share_den):
            raise ValueError(
                f"pow_share must be in [0, 1], got {self.pow_share_num}/{self.pow_share_den}")
        if not (0 < self.distribution_rate_num <= self.distribution_rate_den):
            raise ValueError(
                f"distribution_rate must be in (0, 1], got "
                f"{self.distribution_rate_num}/{self.distribution_rate_den}")
        if self.smoothing_factor >= self.smoothing_precision:
            raise ValueError(
                f"the retarget needs smoothing_factor < smoothing_precision for a pole below "
                f"one; got {self.smoothing_factor} and {self.smoothing_precision}")
        if not (0 <= self.genesis_pool_fraction <= 1):
            raise ValueError(
                f"genesis_pool_fraction must be in [0, 1], got {self.genesis_pool_fraction}")
        if self.refill_timing not in ("epoch", "block"):
            raise ValueError(f"refill_timing must be 'epoch' or 'block', got "
                             f"{self.refill_timing!r}")
        if self.blocks_per_epoch <= 0 or self.block_seconds <= 0:
            raise ValueError("blocks_per_epoch and block_seconds must both be positive")
        if not (0 <= self.adversary_hashrate <= 1):
            raise ValueError(f"adversary_hashrate must be in [0, 1], got "
                             f"{self.adversary_hashrate}")


def load(path: str | Path | None = None, **overrides) -> Config:
    """Read the protocol snapshot, apply overrides, validate.

    Overrides name simulation settings, never protocol constants -- changing one of those
    means re-snapshotting, deliberately and in its own commit.
    """
    src = Path(path) if path is not None else _SNAPSHOT
    try:
        cfg = tomllib.loads(src.read_text())
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise SystemExit(f"config {src}: {e}") from e
    try:
        consensus, supply, fees, pow_ = (
            cfg["consensus"], cfg["supply"], cfg["fees"], cfg["pow"])
    except KeyError as e:
        raise SystemExit(f"config {src}: missing section {e.args[0]!r}") from e
    work_ = cfg.get("work", {})
    econ = cfg.get("economics", {})

    protocol = dict(
        blocks_per_epoch=consensus["blocks_per_epoch"],
        block_seconds=consensus["block_seconds"],
        epochs_per_year=consensus["epochs_per_year"],
        blocks_per_year=consensus["blocks_per_year"],
        max_block_txs=consensus["max_block_txs"],
        launch_supply=supply["tge"],
        base_units_per_lgo=supply["base_units_per_lgo"],
        min_stake_fraction=supply["min_stake_fraction"],
        price_resting=fees["price_resting"],
        claim_tx_bytes=fees["claim_tx_bytes"],
        claim_tx_gas=fees["claim_tx_gas"],
        transfer_tx_bytes=fees["transfer_tx_bytes"],
        transfer_tx_gas=fees["transfer_tx_gas"],
        target_claims_per_block=pow_["target_claims_per_block"],
        pow_share_num=pow_["pool_share_num"],
        pow_share_den=pow_["pool_share_den"],
        distribution_rate_num=pow_["distribution_rate_num"],
        distribution_rate_den=pow_["distribution_rate_den"],
        genesis_pool_fraction=pow_["genesis_pool_fraction"],
        smoothing_factor=pow_["ema_smoothing_factor"],
        smoothing_precision=pow_["ema_smoothing_precision"],
        reward_difficulty_exp=pow_["reward_difficulty_exp"],
        seconds_per_candidate_reward=work_.get("seconds_per_candidate_reward", 0.0),
        reference_cores=work_.get("pi5_cores", 1),
        max_emission_per_year=supply["max_emission_per_year"],
        inscribe_gas=cfg.get("mixes", {}).get("inscribe_gas", 56),
        leader_fee_share=econ.get("leader_fee_share", 0.4),
    )
    unknown = set(overrides) - set(Config.__dataclass_fields__)
    if unknown:
        raise SystemExit(f"unknown setting(s): {', '.join(sorted(unknown))}")
    clashes = set(overrides) & set(protocol)
    if clashes:
        raise SystemExit(
            f"{', '.join(sorted(clashes))} are protocol constants and come from the snapshot; "
            f"re-snapshot rather than override")
    return Config(**protocol, snapshot_path=str(src), **overrides)
