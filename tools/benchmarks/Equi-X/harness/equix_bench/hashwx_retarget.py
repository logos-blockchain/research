"""The reward retarget in target form at HashWX scale, as the reference code states it.

A hash satisfies a target T with probability T / 2^64. The update is the one in
proof-of-work.md with its types changed, so this checks three things before the
specification relies on them: that it steers to its target rate, that integer
rounding does not bias it at the scale of a 64-bit target, and how wide its
intermediates get. Rates are ESTIMATES until the Pi 5 is measured with `make hashwx`.

Run:  python -m equix_bench.hashwx_retarget
"""
from __future__ import annotations

import math
import os
import random
import statistics
from dataclasses import dataclass

TWO64 = 1 << 64
SLOTS_PER_BLOCK = 30                 # 1 / f
R_PI5_MACHINE = float(os.environ.get("HASHWX_R_PI5_MACHINE", 6.0e5))

# Seconds of a whole Pi 5 per claim at the easiest target: the time the `zkhash`
# caps give at 41,391 claim tickets a second.
SECONDS_AT_CAP_515 = 1_620           # about p // 2**26
SECONDS_AT_CAP_521_AFTER = 9_720     # about p // (3 * 2**27)
SECONDS_AT_CAP_521_BOOTSTRAP = 77_760    # about p // (3 * 2**30)

LEPTA = 10**9
POOL_SEED = 200_000_000 * LEPTA      # 2/100 of S_cap
BOOTSTRAP_REWARD = 100 * LEPTA
BOOTSTRAP_EPOCHS = 98
BLOCKS_PER_EPOCH = 21_600


@dataclass(frozen=True)
class Rule:
    name: str
    F: int
    P: int
    num: int                         # the target rate is num / den claims a block
    den: int
    cap: int                         # largest target

    @property
    def floor(self) -> int:
        return max(1, math.ceil(self.F / (self.P - self.F)))

    @property
    def rate(self) -> float:
        return self.num / self.den


def step(rule: Rule, target: int, claims: int) -> int:
    demand = max(1, (rule.P - rule.F) * claims * rule.den + rule.F * rule.num)
    new_target = (rule.num * target * rule.P) // demand
    return min(max(new_target, rule.floor), rule.cap)


def step_exact(rule: Rule, target: float, claims: int) -> float:
    """The same update without rounding, for measuring what rounding costs."""
    demand = max(1, (rule.P - rule.F) * claims * rule.den + rule.F * rule.num)
    return target * (rule.num * rule.P / demand)


def widest_bits(rule: Rule, max_claims: int = 1 << 16) -> int:
    """The widest value the update computes, at its largest target and most claims."""
    product = rule.num * rule.cap * rule.P
    demand = (rule.P - rule.F) * max_claims * rule.den + rule.F * rule.num
    return max(product.bit_length(), demand.bit_length())


def rules(r_board: float = R_PI5_MACHINE) -> list[Rule]:
    def cap(seconds: int) -> int:
        return TWO64 // int(r_board * seconds)

    reward_after = 722_000_000       # 0.722 LOGOS, the later reward at the starting storage price
    pool_after = 1_000_000 * LEPTA   # an example of what the pool holds after the bootstrap
    return [
        Rule("#515, 10 claims a block", 9, 10, 10, 1, cap(SECONDS_AT_CAP_515)),
        Rule("#521 bootstrap", 999, 1000, POOL_SEED,
             BOOTSTRAP_REWARD * (BOOTSTRAP_EPOCHS + 1) * BLOCKS_PER_EPOCH, cap(SECONDS_AT_CAP_521_BOOTSTRAP)),
        Rule("#521 after, 1M LOGOS in the pool", 999, 1000, pool_after,
             reward_after * (BOOTSTRAP_EPOCHS + 1) * BLOCKS_PER_EPOCH, cap(SECONDS_AT_CAP_521_AFTER)),
    ]


def _poisson(rng: random.Random, lam: float) -> int:
    if lam <= 0:
        return 0
    if lam < 30:
        limit, k, p = math.exp(-lam), 0, 1.0
        while True:
            k += 1
            p *= rng.random()
            if p <= limit:
                return k - 1
    return max(0, round(rng.gauss(lam, math.sqrt(lam))))


def simulate(rule: Rule, schedule: list[tuple[int, float]], seed: int, start: int) -> tuple[list[int], list[int]]:
    """schedule: (blocks, hashes per second). Block gaps are exponential."""
    rng = random.Random(seed)
    target = start
    claims_seen: list[int] = []
    targets: list[int] = []
    for blocks, hashes_per_second in schedule:
        for _ in range(blocks):
            gap = rng.expovariate(1 / SLOTS_PER_BLOCK)
            claims = _poisson(rng, hashes_per_second * gap * target / TWO64)
            claims_seen.append(claims)
            targets.append(target)
            target = step(rule, target, claims)
    return claims_seen, targets


def settled_target(rule: Rule, hashes_per_second: float) -> int:
    """The target at which a miner rate finds exactly the target claim rate."""
    return min(rule.cap, int(TWO64 * rule.rate / (hashes_per_second * SLOTS_PER_BLOCK)))


def settling_blocks(targets: list[int], start: int, wanted: int, tolerance: float = 0.25, window: int = 50) -> int | None:
    for i in range(start + window, len(targets)):
        if abs(statistics.median(targets[i - window:i]) / wanted - 1) <= tolerance:
            return i - start
    return None


def rounding_bias(rule: Rule, start: int, blocks: int, seed: int) -> float:
    """Open loop: the same claims through the integer and the exact update, as a
    ratio of the two final targets. 1.0 means rounding did nothing."""
    rng = random.Random(seed)
    target, exact = start, float(start)
    for _ in range(blocks):
        claims = _poisson(rng, rule.rate)
        target = (rule.num * target * rule.P) // max(1, (rule.P - rule.F) * claims * rule.den + rule.F * rule.num)
        exact = step_exact(rule, exact, claims)
    return target / exact


def main() -> int:
    print(f"Whole Pi 5 assumed at {R_PI5_MACHINE:.3g} hashes a second, which is not measured.\n")
    print("| rule | target rate | cap | floor | widest value | steady claims a block | x10 jump settles | back |")
    print("|---|---|---|---|---|---|---|---|")
    for rule in rules():
        # Enough miners that the settled target sits well below the cap.
        hashes = 4 * TWO64 * rule.rate / (SLOTS_PER_BLOCK * rule.cap)
        wanted = settled_target(rule, hashes)
        blocks = int(max(200_000, 200 / max(rule.rate, 1e-3) * (rule.P / (rule.P - rule.F))))
        claims, _ = simulate(rule, [(blocks, hashes)], 31, wanted)
        steady = statistics.mean(claims[blocks // 4:])
        run = int(120 * rule.P / (rule.P - rule.F) / max(min(rule.rate, 1.0), 0.05))
        _, targets = simulate(rule, [(2000, hashes), (run, 10 * hashes), (run, hashes)], 32, wanted)
        up = settling_blocks(targets, 2000, wanted // 10)
        down = settling_blocks(targets, 2000 + run, wanted)
        print(f"| {rule.name} | {rule.rate:.4g} | 2^{math.log2(rule.cap):.1f} | {rule.floor} | "
              f"{widest_bits(rule)} bits | {steady:.4g} | {up} blocks | {down} blocks |")
    print()
    print("Rounding, as the integer target over the exact one after 100,000 blocks, open loop:\n")
    print("| rule | start | ratio |")
    print("|---|---|---|")
    for rule in rules():
        for start in (rule.cap, 1 << 24, 1 << 20, 1 << 16):
            if start <= rule.cap:
                print(f"| {rule.name} | 2^{math.log2(start):.1f} | {rounding_bias(rule, start, 100_000, 7):.5f} |")
    print()
    print("The floor, from a block without claims:\n")
    for rule in rules()[:2]:
        fl = rule.floor
        print(f"- {rule.name}: floor {fl}. {fl - 1} goes to {(fl - 1) * rule.P // rule.F}, "
              f"and {fl} goes to {fl * rule.P // rule.F}.")
    print(f"\nA pool of 64 bits with P = 1000 keeps the product within 128 bits for a cap below 2^{128 - 64 - 10}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
