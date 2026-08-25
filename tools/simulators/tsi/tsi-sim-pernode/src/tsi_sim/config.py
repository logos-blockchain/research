"""Configuration dataclasses for single runs and parameter sweeps."""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field, replace
from typing import Any, Literal

from . import constants

StakeDist = Literal["uniform", "pareto"]
UncleStrategy = Literal["oldest", "random"]
# Uncle counting/selection model:
#  "countable" (default) — the spec's counting-only model (cryptarchia-v1-protocol.md):
#     only the FIRST block of a fork is referenceable/countable (its parent lies on the
#     referencing chain), the window is derived as w_u = window_absorption / f slots,
#     selection excludes slots already occupied on the producer's chain and picks at most
#     one uncle per slot, and counting re-checks every rule per reference.
#  "old" — the pre-redesign model (run with --old): window = uncle_window slots directly,
#     any orphan in view is referenceable regardless of fork depth, no occupied-slot or
#     per-slot exclusion, and every baked reference counts.
UncleModel = Literal["countable", "old"]
Topology = Literal["full_mesh", "regular", "blend"]
LinkLatencyDist = Literal["fixed", "uniform", "exp", "geo"]
JitterDist = Literal["exp", "poisson"]
ChurnMode = Literal["sine", "ramp", "step"]
InitDest = Literal["common", "heterogeneous"]
# How the adversary_frac coalition attacks the TSI density count:
#  "suppress" — produces normally but references NO uncles (starves the recovered density; weak);
#  "withhold" — never gossips its blocks (they are orphaned, its won slots become gaps in the
#     canonical chain), so the counted density drops ~adversary_frac and TSI deflates D_est toward
#     the reduced ACTIVE stake. Stronger, but the withheld blocks earn nothing (griefing/grinding).
#  "selfish" — mines a PRIVATE chain and releases it to orphan honest blocks (Eyal-Sirer SM1).
#     Unlike "withhold" (which discards its blocks — abstention, a dead loss), this recovers the
#     forfeit by displacing honest work, and is the one profitable lever (report §6.6). Its
#     estimator damage is what the countable uncle rule can only partly repair, because an
#     override discards a CHAIN of honest blocks and only the first is referenceable (§2.1).
#  "deep_parent" — mints blocks that hang off an ANCIENT chain block instead of the current
#     tip. Each is a genuine lottery win and a legal first-fork uncle, and under the spec's
#     uncle-anchored window it is eligible the moment it is produced (its OWN slot is recent),
#     so honest proposers reference it — forcing every validator to derive the epoch and ledger
#     state at that ancient parent to check its Proof of Leadership. The attack this branch
#     evaluates: it costs the adversary nothing it would not already spend, and the effort it
#     imposes is bounded only by how far back the block tree reaches.
AdversaryStrategy = Literal["suppress", "withhold", "selfish", "deep_parent"]
# WHICH nodes make up that coalition, at the same total stake:
#  "random" — a uniformly random set grown until its stake reaches adversary_frac (the default; the
#     block share is then smooth in adversary_frac, which is all the density levers depend on);
#  "whale"  — the LARGEST holders first. Same stake, far fewer nodes, so the coalition's block
#     production is lumpier — the untested concentration case flagged in report §6.5's scope.
AdversarySelection = Literal["random", "whale"]
# WHICH slot the uncle reference window is measured against:
#  "uncle"  (spec) — the uncle's own slot: 0 < sl_A - sl_U <= w_u. Bounds how old a referenced
#     block may be, but leaves its PARENT unbounded, so a valid uncle may hang off an
#     arbitrarily old chain block and force a validator to derive historical epoch/ledger
#     state at that ancient parent to check its Proof of Leadership.
#  "parent" (proposed) — the uncle's parent's slot: sl_A - sl_parent(U) <= w_u. Since a block
#     strictly postdates its parent, the parent gap is never smaller than the uncle gap, so
#     this is STRICTLY TIGHTER: it bounds both, and bounds how far back state must be reached.
UncleWindowAnchor = Literal["uncle", "parent"]
# Which referencing blocks the density count reads. "window" is the spec rule
# (cryptarchia-v1-protocol.md, Epoch State Pseudocode): referenced_uncles is drawn from the
# chain blocks that lie in the observation window, so a block past the window's end cannot add
# occupied slots to a closed window. "chain" is the pre-2026-08-17 wording, which gated on the
# uncle's own slot alone and let a block up to w_u slots past the window reach back into it.
RefScope = Literal["window", "chain"]


@dataclass(frozen=True)
class SimConfig:
    """A single fully-specified simulation run (one grid cell, one replicate)."""

    # --- network / stake ---
    n_nodes: int = 1000
    stake_dist: StakeDist = "uniform"
    pareto_shape: float = 1.16          # Pareto (Lomax) tail index; ~80/20 by default
    uniform_random: bool = False        # if True, draw i.i.d. uniform stakes; else equal
    total_stake: float = 1.0e9          # FIXED across distributions for comparability

    # --- network latency (slots) ---
    latency: int = 0                    # L: full-mesh uniform link latency (block seen at t+L)
    latency_stochastic: bool = False    # if True, L is the mean of a stochastic model

    # --- network topology (per-node model) ---
    # "full_mesh": every node one hop away, uniform latency = `latency` (reproduces the
    #   reduced model). "regular": random d-regular peering graph with per-link latency;
    #   a block reaches a node after the shortest WEIGHTED path from its producer.
    # "blend": same d-regular graph, but a block is first relayed through `blend_hops` random
    #   nodes (a mix cascade, each adding a Uniform(0, blend_delay_max) mixing delay) before a
    #   final network-wide gossip makes it visible — models routing over the Blend mixnet.
    topology: Topology = "full_mesh"
    degree: int = 8                     # peering degree (regular / blend graph)
    # One entropy contributor to the per-trajectory RNG (via key()), NOT an independent topology
    # knob: the graph is seeded from the config's full-key spawn hierarchy (engine.run_trajectory),
    # so it is fixed per trajectory but is re-rolled by ANY key() field (stake_dist, f,
    # adversary_frac, replicate, ...). Consequently two configs that differ only in a non-topology
    # field draw different graphs; adversary-vs-honest comparisons are therefore unpaired in the
    # graph sample (a variance source averaged out over replicates, not a bias — the main deflation
    # effects are topology-independent, §6.4). Making it a paired/independent knob would require
    # seeding the graph from topology-only entropy and re-running every sweep.
    graph_seed: int = 0
    # Blend mixnet cascade (topology == "blend"): the producer picks `blend_hops` distinct
    # relay nodes uniformly at random; the block hops producer -> r1 -> ... -> r_hops over the
    # graph, each relay waiting Uniform(0, blend_delay_max) slots before forwarding; the last
    # relay's forward is the final network-wide gossip. Ignored by full_mesh / regular.
    blend_hops: int = 3                 # number of random relay hops in the mix cascade
    adversary_strategy: AdversaryStrategy = "suppress"   # how adversary_frac attacks (see above)
    blend_delay_max: float = 3.0        # max per-relay mixing delay (slots); delay ~ U(0, this)
    # Mean one-way per-link latency in SLOTS (1 slot = 1 s). Realistic direct-gossip links are
    # sub-slot (~0.04-0.15 slot = 40-150 ms); whole-slot values (1, 2, ...) model routing over
    # the Blend mixnet, where each hop costs seconds. Arrivals are kept sub-slot (float).
    link_latency_mean: float = 1.0
    # Per-link latency distribution (all have mean = link_latency_mean): "fixed" (all equal),
    # "uniform" (0..2*mean), "exp" (long tail), "geo" (real-world geographic band mixture:
    # short intra-region links, long inter-continental ones — see constants.GEO_LATENCY_*).
    link_latency_dist: LinkLatencyDist = "fixed"
    jitter_mean: float = 0.0            # extra per-(block,node) jitter (slots); 0 = none.
    # Jitter model (active when jitter_mean > 0):
    #  "exp"     — EVERY delivery gets +Exp(jitter_mean); the §6.1 robustness model.
    #  "poisson" — a random fraction `jitter_frac` of deliveries gets +Poisson(jitter_mean)
    #              whole slots; the rest arrive on time. A LONG-TAIL model: most deliveries are
    #              unaffected, a few straggle by multiple slots (case (b) of the N-scaling study).
    jitter_dist: JitterDist = "exp"
    jitter_frac: float = 1.0            # fraction of deliveries hit (poisson model; exp uses all)

    # --- uncle references ---
    uncle_model: UncleModel = "countable"     # countable (spec, default) | old (--old)
    # Countable model: window absorption parameter W; the uncle reference window is DERIVED
    # as w_u = W / f slots (W expected block-intervals), bounded 1 <= W <= 0.6*k
    # (constants.W_ABS_MAX_FACTOR). Ignored by the old model.
    window_absorption: float = constants.W_ABS_DEFAULT
    # Old model only (--old): the uncle reference window w_u in slots, set directly.
    # Ignored by the countable model, which derives the window from window_absorption.
    uncle_window: int = constants.W_DEFAULT
    # COMMON RANDOM NUMBERS for countable-vs-old comparisons. Off by default, and deliberately
    # NOT part of key() — with it off every seed is byte-identical to before, so historical runs
    # and --old bit-reproduction are untouched.
    #
    # The two uncle models normally draw independent streams (uncle_model is in the key), so a
    # comparison pays the full between-run variance TWICE and the arms differ in stake draw,
    # peering graph and every lottery outcome. With paired_streams=True the RNG root is derived
    # from the model-independent part of the key instead, so both arms get the SAME stake, the
    # SAME graph and the SAME lottery draws; the only difference is the uncle rule, and the
    # per-replicate difference becomes a paired observation with the shared variance cancelled.
    # Trajectories still diverge legitimately after epoch 0 — a different counted density feeds
    # back into the next epoch's difficulty — which is the effect being measured, not noise.
    paired_streams: bool = False
    max_uncles: int = 0                       # U (0 = baseline, no uncles)
    # "oldest" IS the spec rule: cryptarchia-v1-protocol.md (Uncle Selection) has the proposer
    # take the oldest candidates first, deterministically, because an uncle expires w_u slots
    # after its own slot so the oldest are the closest to expiring. Every headline result uses it.
    uncle_strategy: UncleStrategy = "oldest"
    # DEFAULT is the deployed rule, so the simulator describes the protocol as it stands and the
    # §6.12 proposal is an explicit arm — the same convention `fixed_point` follows. It must also
    # stay "uncle" for a harder reason: key() appends the anchor only when it is not "uncle", so
    # this default is what keeps an --old run's key byte-identical to the pre-redesign key and
    # lets it bit-reproduce every historical run (§9).
    uncle_window_anchor: UncleWindowAnchor = "uncle"
    # DEFAULT is the spec rule (see RefScope). Deliberately NOT in key(): the reference scope is a
    # MEASUREMENT rule that consumes no RNG, so both arms of a comparison run on a bit-identical
    # block tree and their difference carries no sampling noise at all — the same reasoning that
    # keeps windowed_fork_choice out of the key. Like selfish_lead_cap, that makes this a knob
    # where an unchanged key does NOT imply an unchanged number; §9 records what was re-measured.
    ref_scope: RefScope = "window"
    # "random" is NOT a spec variant — it is the deviation probe: walk the same oldest-first
    # candidate order but include each candidate with probability uncle_random_p, so a lone
    # candidate is dropped half the time. Uncle selection is proposer-local and unvalidated, so a
    # proposer CAN deviate; this measures what that costs the estimate (report §3.4).
    uncle_random_p: float = 0.5
    # --- adversary (grinding via D_est deflation) ---
    # Fraction of TOTAL STAKE controlled by an adversary that suppresses uncle references in its
    # own blocks (references no uncles), starving the TSI density count so honest nodes under-count
    # blocks and infer a LOW D_est -> everyone's win probability phi(f, w/D_est) rises, which is the
    # grinding payoff. 0.0 = fully honest (the studied baseline). The coalition is by default a
    # RANDOM node set whose stake sums to adversary_frac (see engine._adversary_mask); block
    # production is stake-proportional, so the deflation depends only on that summed share, not on
    # whether the coalition is one whale or many small nodes. Withholding is a separate, stronger
    # lever, and adversary_selection controls WHICH nodes are taken at that fixed stake.
    adversary_frac: float = 0.0
    adversary_selection: AdversarySelection = "random"
    # How many INDEPENDENT coalitions the adversarial stake is split into (§6.9). 1 = the single
    # coalition every other study assumes. K > 1 partitions the same adversary_frac into K groups
    # of near-equal stake, each running its OWN private chain with its own view: a rival's
    # unreleased blocks are invisible (they reach no node until released), so the coalitions
    # orphan each other as well as the honest chain. Only meaningful for
    # adversary_strategy == "selfish" — under "suppress"/"withhold" the deflation depends on the
    # summed stake alone, which is exactly the structure-independence result of §6.9, so the
    # partition provably cannot matter there and the engine ignores it.
    adversary_coalitions: int = 1
    # Lead at which a selfish coalition PUBLISHES its private chain instead of extending it.
    #   0  (default) -> the finality depth k: a lead past k can never be caught, so holding it
    #                   gains nothing and a rational coalition cashes in.
    #   > 0          -> that lead, explicitly.
    #   < 0          -> uncapped: textbook SM1, which waits for as long as it leads.
    # Textbook SM1 assumes the lead returns to zero and the chain is cashed in then. That fails
    # under a forking honest network: the public chain's HEIGHT grows at ~(1-alpha)*f*(1-fork)
    # while a coalition sharing one view extends privately at the full alpha*f, so past a fork
    # rate of ~1 - alpha/(1-alpha) the private chain outruns the public one and `wait` never
    # terminates. See _SelfishCoalition.decide.
    selfish_lead_cap: int = 0
    # Dynamic (withhold-then-rejoin) schedule for the withholding lever (§6.5). The coalition is
    # FIXED (identity from adversary_frac); this only gates whether it withholds in a given epoch.
    #  adversary_period == 0  -> STATIC: the coalition attacks (withholds) every epoch (the §6.4
    #     model; backward-compatible default).
    #  adversary_period  > 0  -> PERIODIC: withhold for the first `adversary_withhold_epochs` of
    #     every `adversary_period`-epoch cycle, then behave honestly (produce + gossip) for the
    #     rest — an abstain-then-rejoin grinder. A single downward pulse (does D_est recover, or
    #     tip into the §6.2 collapsed branch?) is period == epochs, withhold_epochs == pulse length.
    # Only affects adversary_strategy == "withhold"; suppression stays static.
    adversary_period: int = 0
    adversary_withhold_epochs: int = 0

    # --- consensus / TSI ---
    f: float = constants.F               # slot activation coefficient (configurable; sweepable)
    beta: float = constants.BETA_DEFAULT
    k: int = 64                          # scaled by default; full scale = 2160
    genesis_d_factor: float = 0.5        # genesis D = factor * true total stake
    epochs: int = 40
    # If True, quantise the target rate the way an on-chain integer estimator does:
    # f_p = int(f*f_precision)/f_precision. Default False keeps the analysis-faithful exact-f
    # behaviour, which is right for DESIGN questions (it isolates the mechanism under test).
    fixed_point: bool = False
    # The on-chain fixed-point scale, read only when fixed_point is True. The deployed spec and
    # this report disagree: cryptarchia-total-stake-inference.md carries `const PRECISION = 1e3`
    # (f_p = 0.033 at f = 1/30, so f/f_p ~ 1.010 — the ~1 % over-estimate of Appendix A), while
    # the report recommends 1e6 (f_p = 0.033333, residual < 1e-5). Default is the recommendation;
    # set 1000 for a SPEC-FAITHFUL arm answering "what would the deployed chain read".
    f_precision: int = 1_000_000
    # If True, count uncle references per BLOCK ID (the pre-fix behaviour, which double-counts
    # same-slot co-winners and inflates the equilibrium by c(f)). The correct default counts
    # per SLOT (one count per slot, matching the pre-uncle design invariant). Kept as a flag
    # for reproducing historical runs only; no study uses it.
    legacy_block_count: bool = False
    # Early stop: when the per-epoch estimate has converged (trailing epochs statistically
    # flat), run ES_MEASURE more epochs as the equilibrium sample and stop. Truncation-only:
    # per-epoch RNG streams are pre-spawned, so the epochs that DO run are bit-identical to a
    # full run's prefix (hence excluded from key()). Auto-disabled for periodic-adversary
    # schedules (sawtooths must run their full budget).
    early_stop: bool = False
    # Organic (non-adversarial) participation churn: each epoch a `churn_amp` fraction of honest
    # stake goes inactive following a schedule, so the ACTIVE stake oscillates/ramps and TSI must
    # track it. churn_amp = peak inactive fraction; churn_period = epochs per cycle; churn_mode:
    #  "sine"  — active fraction = 1 - churn_amp*(1-cos(2π·epoch/period))/2 (smooth weekly cycle)
    #  "ramp"  — active fraction declines linearly to 1-churn_amp over churn_period, then holds
    #  "step"  — one-time drop to (1-churn_amp) at churn_period (mass leave)
    churn_amp: float = 0.0
    churn_period: int = 4
    churn_mode: ChurnMode = "sine"
    # INERT: nothing reads this. The §6.1 clock-skew study is run stand-alone by
    # scripts/clock_skew.py, which applies its own per-node offsets — not through this field.
    # Retained only as a key() seed contributor for run-hash compatibility (like `per_node_dest`);
    # leave at 0.
    clock_skew_max: int = 0
    # Each node updates its OWN D_est from its OWN view — the point of this simulator, and the ONLY
    # mode implemented here (always True). The global-consensus-D_est baseline (per_node_dest=False)
    # is not built in this package; it lives in the sibling reduced model (tsi-sim). Retained as a
    # key() seed contributor for compatibility; do not set False (no code path reads it).
    per_node_dest: bool = True
    # "common": all nodes start at genesis_d_factor*D_true (studies convergence FROM
    #   agreement). "heterogeneous": per-node initial D_est drawn with relative spread
    #   `init_spread` around genesis (studies transient re-convergence from disagreement).
    init_dest: InitDest = "common"
    init_spread: float = 0.0             # relative spread of heterogeneous initial D_est

    # --- performance ---
    # INERT: nothing reads this — `simulate_epoch` never calls `lottery.sample_wins_chunked`,
    # so it has no modelled effect. Retained as a key() seed contributor for run-hash
    # compatibility (like `per_node_dest` above); leave at 1.
    lottery_chunks: int = 1
    # Windowed fork choice bounds the per-slot candidate scan to a horizon of the max path
    # latency (plus the fully-propagated best tip), turning O(n_blocks^2) into O(n_blocks*H).
    # EXACT when link latency is deterministic (jitter_mean == 0). With jitter_mean > 0 it is
    # a (usually tiny) approximation and emits a warning — see blocktree.build_tree_pernode.
    # Set False for a guaranteed-exact full scan.
    windowed_fork_choice: bool = True
    # Sliding-window pruning of the (N x n_blocks) arrival matrix: keep per-node arrival columns
    # only for blocks still inside the keep-span max(horizon, uncle_window); blocks past that are
    # finalized (arrived at every node under the deterministic horizon), so their columns are
    # dropped. Turns O(N * n_blocks) memory into O(N * keep-span-blocks) — the fix for the
    # collapsed-D_est block explosion. EXACT vs the full matrix when jitter_mean == 0 (needs the
    # horizon, so it only applies when windowed_fork_choice is on); set False to store the whole
    # matrix (the parity oracle, and required for a guaranteed-exact jitter>0 run).
    prune_arrival: bool = True

    # --- bookkeeping ---
    replicate: int = 0
    root_seed: int = 12345

    def __post_init__(self) -> None:
        # frozen dataclass: validation only (no attribute assignment)
        if self.stake_dist not in ("uniform", "pareto"):
            raise ValueError(f"stake_dist must be uniform|pareto, got {self.stake_dist!r}")
        if self.uncle_strategy not in ("oldest", "random"):
            raise ValueError(f"uncle_strategy must be oldest|random, got {self.uncle_strategy!r}")
        if self.uncle_model not in ("countable", "old"):
            raise ValueError(f"uncle_model must be countable|old, got {self.uncle_model!r}")
        if self.uncle_model == "countable":
            if self.window_absorption < 1.0:
                raise ValueError(
                    f"window_absorption W={self.window_absorption} must be >= 1")
            if self.window_absorption > constants.W_ABS_MAX_FACTOR * self.k:
                # The spec bounds W <= 0.6*k (w_u <= 0.6*k/f, inside the finalization
                # window). Scaled-down research geometries (small k) may violate it on
                # purpose — warn loudly rather than refuse, but full-scale runs should
                # never see this.
                import warnings

                warnings.warn(
                    f"window_absorption W={self.window_absorption} exceeds the spec bound "
                    f"{constants.W_ABS_MAX_FACTOR}*k = "
                    f"{constants.W_ABS_MAX_FACTOR * self.k:g} (k={self.k}); the derived "
                    f"window is outside the finalization window at this geometry",
                    RuntimeWarning, stacklevel=2)
        if self.topology not in ("full_mesh", "regular", "blend"):
            raise ValueError(f"topology must be full_mesh|regular|blend, got {self.topology!r}")
        if self.link_latency_dist not in ("fixed", "uniform", "exp", "geo"):
            raise ValueError(f"link_latency_dist must be fixed|uniform|exp|geo, got "
                             f"{self.link_latency_dist!r}")
        if self.jitter_dist not in ("exp", "poisson"):
            raise ValueError(f"jitter_dist must be exp|poisson, got {self.jitter_dist!r}")
        if not 0.0 <= self.jitter_frac <= 1.0:
            raise ValueError(f"jitter_frac must be in [0, 1], got {self.jitter_frac}")
        if self.init_dest not in ("common", "heterogeneous"):
            raise ValueError(f"init_dest must be common|heterogeneous, got {self.init_dest!r}")
        if self.churn_mode not in ("sine", "ramp", "step"):
            raise ValueError(f"churn_mode must be sine|ramp|step, got {self.churn_mode!r}")
        if not 0.0 <= self.churn_amp < 1.0:
            raise ValueError(f"churn_amp must be in [0, 1), got {self.churn_amp}")
        if self.churn_period < 1:
            raise ValueError(f"churn_period must be >= 1, got {self.churn_period}")
        if self.clock_skew_max < 0:
            raise ValueError(f"clock_skew_max must be >= 0, got {self.clock_skew_max}")
        if self.f_precision < 1 or self.f_precision != int(self.f_precision):
            raise ValueError(f"f_precision must be a positive integer, got {self.f_precision!r}")
        if self.uncle_window_anchor not in ("uncle", "parent"):
            raise ValueError(f"uncle_window_anchor must be uncle|parent, got "
                             f"{self.uncle_window_anchor!r}")
        if self.ref_scope not in ("window", "chain"):
            raise ValueError(f"ref_scope must be window|chain, got {self.ref_scope!r}")
        if self.adversary_selection not in ("random", "whale"):
            raise ValueError(f"adversary_selection must be random|whale, got "
                             f"{self.adversary_selection!r}")
        if self.adversary_strategy not in ("suppress", "withhold", "selfish",
                                           "deep_parent"):
            raise ValueError(f"adversary_strategy must be "
                             f"suppress|withhold|selfish|deep_parent, got "
                             f"{self.adversary_strategy!r}")
        checks = {
            "n_nodes": self.n_nodes >= 1,
            "k": self.k >= 1,
            "epochs": self.epochs >= 1,
            "latency": self.latency >= 0,
            "max_uncles": self.max_uncles >= 0,
            "uncle_window": self.uncle_window >= 1,
            "lottery_chunks": self.lottery_chunks >= 1,
            "uncle_random_p": 0.0 <= self.uncle_random_p <= 1.0,
            "f": 0.0 < self.f < 1.0,
            "beta": self.beta > 0.0,
            "genesis_d_factor": self.genesis_d_factor > 0.0,
            "pareto_shape": self.pareto_shape > 0.0,
            "total_stake": self.total_stake > 0.0,
            "degree": self.degree >= 1,
            "link_latency_mean": self.link_latency_mean >= 0.0,
            "jitter_mean": self.jitter_mean >= 0.0,
            "init_spread": self.init_spread >= 0.0,
            "blend_hops": self.blend_hops >= 1,
            "blend_delay_max": self.blend_delay_max >= 0.0,
            "adversary_frac": 0.0 <= self.adversary_frac < 1.0,
            "adversary_period": self.adversary_period >= 0,
            "adversary_withhold_epochs": self.adversary_withhold_epochs >= 0,
            "adversary_coalitions": self.adversary_coalitions >= 1,
        }
        bad = [name for name, ok in checks.items() if not ok]
        if bad:
            raise ValueError(f"invalid SimConfig field(s): {bad}")
        if self.adversary_period > 0 and self.adversary_withhold_epochs > self.adversary_period:
            raise ValueError(
                f"adversary_withhold_epochs ({self.adversary_withhold_epochs}) must be "
                f"<= adversary_period ({self.adversary_period})")
        if self.topology in ("regular", "blend"):
            # a d-regular graph on n nodes needs degree < n and n*degree even
            if self.degree >= self.n_nodes:
                raise ValueError(f"degree ({self.degree}) must be < n_nodes ({self.n_nodes})")
            if (self.n_nodes * self.degree) % 2 != 0:
                raise ValueError("regular graph requires n_nodes*degree to be even")
        if self.topology == "blend":
            # need `blend_hops` DISTINCT relay nodes drawn from the non-producer pool
            if self.blend_hops > self.n_nodes - 1:
                raise ValueError(
                    f"blend_hops ({self.blend_hops}) must be <= n_nodes-1 ({self.n_nodes - 1})")

    def adversary_withholds(self, epoch: int) -> bool:
        """Whether the (fixed) coalition withholds this epoch under its schedule.

        Static (``adversary_period == 0``) attacks every epoch; periodic attacks the first
        ``adversary_withhold_epochs`` epochs of each ``adversary_period``-epoch cycle. Meaningful
        only for ``adversary_strategy == "withhold"`` with ``adversary_frac > 0``.
        """
        if self.adversary_period <= 0:
            return True
        return (epoch % self.adversary_period) < self.adversary_withhold_epochs

    # derived geometry -------------------------------------------------------
    @property
    def effective_uncle_window(self) -> int:
        """The uncle reference window ``w_u`` in slots actually used by this run.

        Countable model (default): derived, ``w_u = round(window_absorption / f)``.
        Old model (``--old``): ``uncle_window`` taken directly.
        """
        if self.uncle_model == "old":
            return self.uncle_window
        return constants.uncle_window_slots(self.window_absorption, self.f)

    @property
    def epoch_len(self) -> int:
        return constants.epoch_len(self.k, self.f)

    @property
    def period_T(self) -> int:
        return constants.period_T(self.k, self.f)

    def _base_key(self) -> tuple:
        """Identity fields shared by both uncle models — see ``key`` and ``seed_key``."""
        return (
            self.n_nodes, self.stake_dist, self.pareto_shape, self.uniform_random,
            self.total_stake, self.latency, self.latency_stochastic, self.uncle_window,
            self.max_uncles, self.uncle_strategy, self.uncle_random_p, self.f, self.beta,
            self.k, self.genesis_d_factor, self.epochs, self.fixed_point,
            self.legacy_block_count, self.churn_amp, self.churn_period, self.churn_mode,
            self.clock_skew_max, self.per_node_dest,
            self.lottery_chunks, self.topology, self.degree, self.graph_seed,
            self.link_latency_mean, self.link_latency_dist, self.jitter_mean,
            self.jitter_dist, self.jitter_frac,
            self.blend_hops, self.blend_delay_max, self.adversary_frac, self.adversary_strategy,
            self.adversary_period, self.adversary_withhold_epochs,
            self.init_dest, self.init_spread, self.replicate,
        )
        # NOTE: windowed_fork_choice and prune_arrival are deliberately excluded — they are pure
        # compute/memory optimisations that consume no RNG and (at jitter_mean == 0) change no
        # result, so pruned and full-matrix runs must share a seed (see test_pernode parity).

    def key(self) -> tuple:
        """Hashable identity used to seed the RNG deterministically.

        Must include EVERY field that affects the run (guarded by test_rng), otherwise two
        distinct configs would share an RNG stream. ``uncle_model`` /
        ``window_absorption`` are appended ONLY for the countable model: an ``--old`` run's
        key is then byte-identical to the pre-redesign key, so ``--old`` bit-reproduces
        historical runs (the two models still get distinct streams from the marker).
        """
        # uncle_model == "old" keeps the historical tuple exactly (--old bit-compat).
        base = (self._base_key() if self.uncle_model == "old"
                else self._base_key() + (self.uncle_model, self.window_absorption))
        # Appended ONLY when non-default, for the same reason the uncle_model marker is: a
        # "random"-coalition run's key must stay byte-identical to every historical run's.
        if self.adversary_selection != "random":
            base = base + (self.adversary_selection,)
        # Same append-only-when-non-default discipline: a run at the default precision keeps a
        # byte-identical key, so no committed result is reseeded by adding the knob.
        if self.f_precision != 1_000_000:
            base = base + (self.f_precision,)
        # Likewise: K == 1 is the single-coalition assumption every prior study was run under, so
        # a K == 1 key must stay byte-identical to the historical one.
        if self.adversary_coalitions != 1:
            base = base + (self.adversary_coalitions,)
        # Same discipline again. NOTE this knob changes RESULTS at the default value (it fixes the
        # runaway described on the field), so it is the one case where an unchanged key does not
        # imply an unchanged number — see report §9 on which selfish runs were re-measured.
        if self.selfish_lead_cap != 0:
            base = base + (self.selfish_lead_cap,)
        return base if self.uncle_window_anchor == "uncle" else base + (self.uncle_window_anchor,)

    def seed_key(self) -> tuple:
        """The identity the RNG root is actually derived from (see ``rng.seedseq_for``).

        Identical to ``key`` except under ``paired_streams``, where it deliberately drops the
        uncle-model marker so that a countable run and an ``--old`` run of the SAME cell draw
        the SAME root seed — common random numbers, which is what makes the two arms a
        *paired* sample (see ``paired_streams``).
        """
        return self._base_key() if self.paired_streams else self.key()


# Axes that can be swept; every SimConfig field is legal here.
_SWEEP_AXES = (
    "n_nodes", "stake_dist", "latency", "max_uncles", "uncle_strategy", "uncle_window",
    "uncle_window_anchor",
    "ref_scope",
    "window_absorption",
    "topology", "degree", "link_latency_mean", "link_latency_dist",
    "blend_hops", "blend_delay_max", "init_dest", "f",
)


@dataclass
class SweepConfig:
    """A cartesian grid of runs plus replicates, all sharing ``base`` settings."""

    n_nodes: list[int] = field(default_factory=lambda: [1000])
    stake_dist: list[StakeDist] = field(default_factory=lambda: ["uniform"])
    latency: list[int] = field(default_factory=lambda: [0])
    max_uncles: list[int] = field(default_factory=lambda: [0, 1, 2, 4])
    uncle_strategy: list[UncleStrategy] = field(default_factory=lambda: ["oldest"])
    uncle_window: list[int] = field(default_factory=lambda: [constants.W_DEFAULT])
    uncle_window_anchor: list[UncleWindowAnchor] = field(default_factory=lambda: ["uncle"])
    ref_scope: list[RefScope] = field(default_factory=lambda: ["window"])
    window_absorption: list[float] = field(default_factory=lambda: [constants.W_ABS_DEFAULT])
    topology: list[Topology] = field(default_factory=lambda: ["regular"])
    degree: list[int] = field(default_factory=lambda: [8])
    link_latency_mean: list[float] = field(default_factory=lambda: [1.0])
    link_latency_dist: list[LinkLatencyDist] = field(default_factory=lambda: ["fixed"])
    blend_hops: list[int] = field(default_factory=lambda: [3])
    blend_delay_max: list[float] = field(default_factory=lambda: [3.0])
    init_dest: list[InitDest] = field(default_factory=lambda: ["common"])
    f: list[float] = field(default_factory=lambda: [constants.F])
    replicates: int = 8
    base: dict[str, Any] = field(default_factory=dict)

    def expand(self) -> list[SimConfig]:
        """Materialise every ``SimConfig`` in the grid × replicates."""
        base = SimConfig(**self.base)
        cells: list[SimConfig] = []
        axis_values = [getattr(self, ax) for ax in _SWEEP_AXES]
        for combo in itertools.product(*axis_values):
            overrides = dict(zip(_SWEEP_AXES, combo, strict=True))
            # U=0 references no uncles, so it is independent of uncle_strategy AND the window
            # knobs; keep only the first of each to avoid duplicate (identical) work.
            if overrides["max_uncles"] == 0 and (
                overrides["uncle_strategy"] != self.uncle_strategy[0]
                or overrides["uncle_window"] != self.uncle_window[0]
                or overrides["window_absorption"] != self.window_absorption[0]
            ):
                continue
            # each uncle model reads exactly one window knob — collapse the other axis so a
            # sweep never emits duplicate cells that differ only in an ignored field.
            if base.uncle_model == "countable" and (
                overrides["uncle_window"] != self.uncle_window[0]
            ):
                continue
            if base.uncle_model == "old" and (
                overrides["window_absorption"] != self.window_absorption[0]
            ):
                continue
            # full mesh ignores degree / link-latency model; keep only the first to avoid dupes.
            if overrides["topology"] == "full_mesh" and (
                overrides["degree"] != self.degree[0]
                or overrides["link_latency_mean"] != self.link_latency_mean[0]
                or overrides["link_latency_dist"] != self.link_latency_dist[0]
            ):
                continue
            # only blend uses the mix-cascade knobs; collapse them elsewhere to avoid dupes.
            if overrides["topology"] != "blend" and (
                overrides["blend_hops"] != self.blend_hops[0]
                or overrides["blend_delay_max"] != self.blend_delay_max[0]
            ):
                continue
            # `latency` is the full_mesh uniform-L knob; regular/blend ignore it — collapse it
            # for them so sweeping latency doesn't emit duplicate (seed-shifted) graph cells.
            if overrides["topology"] != "full_mesh" and overrides["latency"] != self.latency[0]:
                continue
            for rep in range(self.replicates):
                cells.append(replace(base, **overrides, replicate=rep))
        return cells

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SweepConfig:
        d = dict(d)
        base = d.pop("base", {})
        known = {*_SWEEP_AXES, "replicates"}
        unknown = set(d) - known
        if unknown:
            raise ValueError(
                f"unknown sweep keys: {sorted(unknown)} (valid: {sorted(known)}; "
                "per-run settings belong under 'base:')"
            )
        return cls(base=base, **d)
