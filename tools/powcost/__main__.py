"""Print the cost table, its coverage, and the frontier it implies.

Run as ``python3 -m powcost`` from ``tools/``.
"""
from __future__ import annotations

import argparse

from . import kernel, profiles, rates
from .kernel import PowerBasis
from .puzzles import FIELD_MODULUS, PUZZLES


def main() -> int:
    ap = argparse.ArgumentParser(prog="powcost")
    ap.add_argument("--puzzle", default="poseidon2_reward", choices=sorted(PUZZLES))
    ap.add_argument("--price", type=float, default=0.20, help="electricity, per kWh")
    ap.add_argument("--difficulty-exp", type=int, default=26,
                    help="difficulty target as field_modulus / 2**exp")
    args = ap.parse_args()

    print("COVERAGE -- what is measured and what is missing\n")
    buckets = list(profiles.BUCKETS)
    print("  " + "".join(f"{h:<18}" for h in ["puzzle \\ device"] + buckets))
    for row in rates.coverage_matrix():
        print("  " + f"{row["puzzle"]:<18}" + "".join(f"{row[b]:<18}" for b in buckets))

    print("\n  power figures, per bucket:")
    for row in profiles.coverage():
        flag = "" if row["audited"] else "   [NOT AUDITED]"
        print(f"    {row['bucket']:<8} measured={','.join(row['measured']) or '-':<26} "
              f"estimated={','.join(row['estimated']) or '-'}{flag}")

    print(f"\n\nEFFICIENCY FRONTIER -- {args.puzzle}, dedicated-miner basis\n")
    print("  Under free entry the cheapest bucket sets the difficulty, so every bucket")
    print("  above the best mines at a loss. The ordering is the decentralisation claim.\n")
    for r in kernel.frontier(args.puzzle, PowerBasis.TOTAL):
        if r["joules_per_candidate"] is None:
            print(f"    {r['bucket']:<8} GAP -- {r['gap']}")
        else:
            print(f"    {r['bucket']:<8} {r['joules_per_candidate'] * 1e6:>8.1f} uJ/candidate"
                  f"   {r['times_worse_than_best']:>5.2f}x the best")

    print("\n\nWHAT AN ACCELERATOR WOULD HAVE TO REACH\n")
    print("  No accelerator rate exists for any puzzle here and no processor ratio predicts")
    print("  one, so the question is inverted: rather than guess a throughput, state the")
    print("  efficiency at which each bucket stops being able to compete.\n")
    for bucket in profiles.BUCKETS:
        try:
            be = kernel.break_even_accelerator_efficiency(args.puzzle, bucket)
        except Exception:
            continue
        print(f"    to price out {bucket:<8} an accelerator needs "
              f"{be:>12,.0f} candidates/joule")

    d = FIELD_MODULUS >> args.difficulty_exp
    print(f"\n\nONE CLAIM at field_modulus / 2**{args.difficulty_exp}, "
          f"electricity at {args.price:.2f}/kWh\n")
    for bucket in profiles.BUCKETS:
        try:
            c = kernel.cost_per_claim(args.puzzle, bucket, d, args.price, PowerBasis.TOTAL)
        except Exception:
            continue
        print(f"    {bucket:<8} {c.candidates_per_claim:>14,.0f} candidates  "
              f"{c.seconds_per_claim_all_cores / 3600:>7.2f} h  "
              f"{c.joules_per_claim / 3600:>8.2f} Wh  {c.money_per_claim:>10.5f}")

    print("\n  Tail, since the wait is geometric and the mean understates what a")
    print("  participant waiting on one solution experiences:")
    for bucket in ("rpi5",):
        try:
            c = kernel.cost_per_claim(args.puzzle, bucket, d, args.price, PowerBasis.TOTAL)
        except Exception:
            continue
        q = PUZZLES[args.puzzle].quantiles(c.seconds_per_claim_all_cores / 3600)
        print(f"    {bucket:<8} p50 {q['p50']:.2f} h   mean {q['mean']:.2f} h   "
              f"p95 {q['p95']:.2f} h   p99 {q['p99']:.2f} h")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
