"""The acceptance window, priced: expiry, the energy tax, and what it moves.

`mantle` §Proof of Work Operations binds every claim to a recent block and accepts it only
while that anchor sits inside a window of ``EXPECTED_BLOCKS_PER_WINDOW = 10`` expected blocks
(about five minutes). The design intent is grinding resistance: work cannot be stockpiled,
because a solution's anchor goes stale. For the *search* this is free — the puzzle is
progress-free, so abandoning unfinished work when the anchor rolls costs nothing in
expectation. For a *found* solution it is not: a solution that cannot be included before its
window closes dies, and re-mining it costs a full expected solve.

The engines ignore this entirely — `engine.run` clips offered claims at `max_block_txs`
before paying, so demand above the cap never existed as far as every published figure is
concerned. This module prices what the clip discards, in the three places our own findings
say inclusion is not prompt:

1. **Congestion expiry** (bootstrap). The difficulty is floored, so offered demand scales
   with the live field while inclusion is capped at 1,024 a block. Whenever offered exceeds
   the cap for longer than the window, the queue's tail expires. Modelled exactly: a FIFO
   inclusion queue with per-age counts, arrivals Poisson at the epoch's unclipped rate,
   service `max_block_txs` a block, expiry at `W_BLOCKS`.
2. **The post-phase tail** (R7b's own design). The throttle steers saturation into the
   epoch's last half-percent; a solution found after admission stops waits for the next
   budget. Anchors from the final `W_BLOCKS` survive into the next epoch; everything found
   between saturation and that grace strip expires. Measured from the engine's own
   `saturation_block`.
3. **The retirement thresholds.** Expired solutions burn electricity without paying, so the
   effective cost per PAID claim inflates by offered/included — and the retirement decision
   compares income against exactly that cost. `congested_price_curve` closes the loop
   through `retirement.Rational.cost_multiplier`.

And the security half, stated with its arithmetic rather than as a slogan: the window bounds
any stockpile to what the attacker's own live rate produces in `W_BLOCKS` blocks —
`stockpile_bound` — which is why the adversarial analysis, whose harness already limits every
attacker to its live rate, was never understating this.

Not modelled: reorg re-mining (a further small tax proportional to the reorg rate; the spec
expects it, and pricing it needs a fork model this simulator deliberately lacks).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import arrivals, engine, retirement, study
from .params import Derived

# mantle:1585, `EXPECTED_BLOCKS_PER_WINDOW` -- W_b, the anchor's maximum staleness in
# expected blocks. Slots convert via the activation coefficient; in a simulator that steps
# in blocks, the block count is the quantity itself.
W_BLOCKS = 10


@dataclass(frozen=True)
class EpochCongestion:
    offered: int          # solutions found (unclipped demand)
    included: int         # solutions paid within their window
    expired: int          # solutions that aged out -- energy spent, nothing earned

    @property
    def inflation(self) -> float:
        """Energy per paid claim, as a multiple of the uncongested cost."""
        return self.offered / self.included if self.included else float("inf")

    @property
    def expiry_fraction(self) -> float:
        return self.expired / self.offered if self.offered else 0.0


class _Queue:
    """The inclusion queue: exact FIFO by per-age buckets, expiry past `ttl` blocks.

    An entry arrives at age 0 (its anchor block) and may be included at ages 0..ttl — the
    spec's `0 <= current_slot - block.slot <= WINDOW` — then expires. O(ttl) per block,
    which is what lets the study run in minutes rather than modelling individual claims.
    The queue PERSISTS across epoch boundaries: bootstrap admission is continuous, and a
    first version that reset it each epoch fabricated ~0.5% expiry at every seam.
    """

    def __init__(self, cap: int, ttl: int = W_BLOCKS) -> None:
        self.cap, self.ttl = cap, ttl
        self.ages = np.zeros(ttl + 1, dtype=np.int64)

    def step(self, a_t: int) -> tuple[int, int]:
        """One block: age everyone, admit arrivals, serve oldest first. -> (included, expired)"""
        expired = int(self.ages[self.ttl])
        self.ages[1:] = self.ages[:-1]
        self.ages[0] = a_t
        room, included = self.cap, 0
        for age in range(self.ttl, -1, -1):
            take = min(room, int(self.ages[age]))
            self.ages[age] -= take
            included += take
            room -= take
            if room == 0:
                break
        return included, expired


def congestion_profile(rows, cfg, seed: int = 51_001) -> list[EpochCongestion]:
    """Per-epoch congestion for a finished engine run, from its recorded unclipped demand.

    One continuous queue over the whole bootstrap; per-epoch tallies. Whatever is still
    queued when the bootstrap ends is counted expired against the final epoch — the budget
    regime changes under it, which is the one seam that is real.
    """
    rng = np.random.default_rng(seed)
    q = _Queue(cfg.max_block_txs)
    out = []
    boot = [r for r in rows if r.bootstrap]
    for r in boot:
        draws = rng.poisson(r.offered_mu, cfg.blocks_per_epoch)
        offered = int(draws.sum())
        included = expired = 0
        for a_t in draws:
            inc, exp = q.step(int(a_t))
            included += inc
            expired += exp
        out.append(EpochCongestion(offered, included, expired))
    if out:
        left = int(q.ages.sum())
        last = out[-1]
        out[-1] = EpochCongestion(last.offered, last.included, last.expired + left)
    return out


def post_tail_loss(rows, cfg) -> float:
    """Mean fraction of a post-phase epoch's solutions that die in the saturation tail.

    Solutions found after admission stops wait for the next budget. Anchors from the final
    `W_BLOCKS` blocks are still fresh when it opens; everything found between the saturation
    point and that grace strip expires. Uniform arrival of solutions across the epoch is the
    right model here because the throttle's whole job (R7b) is exactly that flattening.
    """
    losses = []
    for r in rows:
        if r.bootstrap or r.saturation_block == engine.NOT_SET:
            continue
        dead_blocks = max(0, cfg.blocks_per_epoch - W_BLOCKS - r.saturation_block)
        losses.append(dead_blocks / cfg.blocks_per_epoch)
    return float(np.mean(losses)) if losses else 0.0


def stockpile_bound(d: Derived, attacker_rate: float) -> float:
    """The most solutions an attacker can hold ready: its own rate, for one window."""
    from empowering_sim import work                            # noqa: PLC0415
    cfg = d.cfg
    per_block = work.expected_claims(attacker_rate, cfg.genesis_difficulty_target, cfg)
    return per_block * W_BLOCKS


def congested_price_curve(d: Derived, prices=(1.0, 0.10, 0.05, 0.01),
                          epochs: int = 240) -> list[dict]:
    """The retirement price curve with the congestion tax closed through the decision.

    One fixed-point pass per price: run the persistent field uncongested to learn its live
    rate, price that trajectory's congestion, then rerun with the per-epoch cost multiplier.
    A second pass would refine the factors against the congested trajectory; the first is
    where the effect lives, and the gate pins its output rather than its convergence.
    """
    cfg = d.cfg
    out = []
    for p in prices:
        base = engine.run(d, arrivals.uniform(220, 130), study.hashrate_draw(cfg),
                          epochs=epochs, retirement_policy=retirement.Rational(token_usd=p))
        prof = congestion_profile(base.rows, cfg)
        factors = np.ones(epochs)
        for i, c in enumerate(prof):
            factors[i] = max(1.0, c.inflation)
        taxed = engine.run(d, arrivals.uniform(220, 130), study.hashrate_draw(cfg),
                           epochs=epochs,
                           retirement_policy=retirement.Rational(
                               token_usd=p,
                               cost_multiplier=lambda e, f=factors: f[min(e, epochs - 1)]))
        def until(r):
            boot = [q for q in r.rows if q.epoch < d.bootstrap_epochs and q.bonds_total > 0]
            return next((q.epoch for q in boot if q.persisting <= 0.5 and q.epoch > 2),
                        d.bootstrap_epochs)
        out.append({"token_usd": p,
                    "persists_until": until(base), "persists_until_taxed": until(taxed),
                    "bonds": base.rows[-1].bonds_total,
                    "bonds_taxed": taxed.rows[-1].bonds_total,
                    "peak_inflation": float(max(c.inflation for c in prof))})
    return out


if __name__ == "__main__":
    from .params import Triple

    d = Triple().derived().check()
    cfg = d.cfg

    print("The acceptance window, priced (W =", W_BLOCKS, "blocks)\n")

    print("1. Congestion, reference retiring run (field stays small):")
    r = engine.run(d, arrivals.uniform(220, 130), study.hashrate_draw(cfg), epochs=220)
    prof = congestion_profile(r.rows, cfg)
    worst = max(prof, key=lambda c: c.inflation)
    print(f"   worst epoch inflation {worst.inflation:.3f}x, expiry {worst.expiry_fraction:.2%}")

    print("2. Congestion, persistent field (nobody leaves, offered grows past the cap):")
    rp = engine.run(d, arrivals.uniform(220, 130), study.hashrate_draw(cfg), epochs=220,
                    retire_on_bond=False)
    profp = congestion_profile(rp.rows, cfg)
    for e in (30, 100, 194):
        c = profp[e]
        print(f"   epoch {e:>3}: offered/blk {c.offered / cfg.blocks_per_epoch:7.1f}  "
              f"inflation {c.inflation:5.2f}x  expiry {c.expiry_fraction:6.2%}")

    print("3. The x100 spike epoch:")
    rs = engine.run(d, arrivals.spike(220, 130, at=30, factor=100),
                    study.hashrate_draw(cfg), epochs=220)
    cs = congestion_profile(rs.rows, cfg)[30]
    print(f"   offered/blk {cs.offered / cfg.blocks_per_epoch:.1f}  "
          f"inflation {cs.inflation:.3f}x  expiry {cs.expiry_fraction:.2%}")

    print("4. Post-phase saturation tail:")
    print(f"   mean lost-work fraction {post_tail_loss(r.rows, cfg):.3%} per epoch")

    print("5. Stockpile bound (grinding resistance, quantified):")
    from . import power
    board = power.board(cfg).candidates_per_second
    print(f"   a 10x-the-field whale (vs 1,000 boards) holds at most "
          f"{stockpile_bound(d, 10 * 1000 * board):,.1f} claims ready")

    print("6. Retirement thresholds with the congestion tax:")
    for row in congested_price_curve(d):
        print(f"   ${row['token_usd']:<5} persists {row['persists_until']:>3} -> "
              f"{row['persists_until_taxed']:>3} taxed   bonds {row['bonds']:,} -> "
              f"{row['bonds_taxed']:,}   peak inflation {row['peak_inflation']:.2f}x")
