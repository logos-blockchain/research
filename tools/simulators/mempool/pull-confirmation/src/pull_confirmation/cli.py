"""Command line entry points: evaluate a candidate, calibrate, or verify."""

from __future__ import annotations

import argparse

from .calibrate import Target, sweep_fraction
from .model import Parameters, liveness_failure, security_failure, security_margin_bits
from .simulate import simulate, within_three_sigma

__all__ = ["main"]

DEFAULT_FRACTIONS = [0.10, 0.20, 0.25, 1 / 3, 0.40, 0.45]


def _base_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    # Defaults match the documented operating assumptions (5000 active
    # declarations, adversarial fraction one third) so a bare invocation scores
    # against the same set the README and the specification quote.
    parser.add_argument("--providers", type=int, default=5000, help="active declaration set size")
    parser.add_argument(
        "--fraction",
        type=float,
        default=1 / 3,
        help="adversarial share of that set (the adversary count rounds up)",
    )
    parser.add_argument(
        "--hold",
        type=float,
        default=0.99,
        help="probability an honest provider already holds a broadcast transaction",
    )
    parser.add_argument(
        "--withhold",
        action="store_true",
        help="model the adversary refusing to attest to transactions it holds",
    )
    parser.add_argument("--max-security", type=float, default=1e-9)
    parser.add_argument("--max-liveness", type=float, default=1e-6)
    return parser


def _fmt(p: float) -> str:
    return "0" if p == 0.0 else f"{p:.3e}"


def cmd_evaluate(args: argparse.Namespace) -> int:
    params = Parameters(
        n_providers=args.providers,
        adversarial_fraction=args.fraction,
        sample_size=args.sample,
        max_rounds=args.rounds,
        threshold=args.threshold,
        hold_probability=args.hold,
        adversary_withholds=args.withhold,
    )
    sec = security_failure(params)
    live = liveness_failure(params)
    target = Target(args.max_security, args.max_liveness)

    print(f"providers            {params.n_providers}")
    print(f"adversarial fraction {params.adversarial_fraction:.3f}"
          f"  ({params.n_adversarial} providers)")
    print(f"sample/round         {params.sample_size}")
    print(f"max rounds           {params.max_rounds}")
    print(f"total sampled        {params.total_sampled}")
    print(f"threshold            {params.threshold}")
    print()
    print(f"security failure     {_fmt(sec)}   ({security_margin_bits(params):.1f} bits)"
          f"   {'OK' if sec <= target.max_security_failure else 'FAIL'}")
    print(f"liveness failure     {_fmt(live)}"
          f"   {'OK' if live <= target.max_liveness_failure else 'FAIL'}")
    return 0 if sec <= target.max_security_failure and live <= target.max_liveness_failure else 1


def cmd_calibrate(args: argparse.Namespace) -> int:
    base = Parameters(
        n_providers=args.providers,
        adversarial_fraction=args.fraction,
        sample_size=1,
        max_rounds=1,
        threshold=1,
        hold_probability=args.hold,
        adversary_withholds=args.withhold,
    )
    target = Target(args.max_security, args.max_liveness)

    print(f"target: security <= {_fmt(target.max_security_failure)}, "
          f"liveness <= {_fmt(target.max_liveness_failure)}")
    print(f"hold probability {args.hold}, "
          f"adversary {'withholds' if args.withhold else 'cooperates'}, "
          f"{args.providers} providers")
    print()
    print(f"{'f':>8}  {'sample':>7}  {'threshold':>10}  {'t/S':>6}  "
          f"{'P[sec]':>11}  {'P[live]':>11}")

    fractions = args.fractions or DEFAULT_FRACTIONS
    any_missing = False
    for fraction, result in sweep_fraction(base, target, fractions):
        if result is None:
            any_missing = True
            print(f"{fraction:>8.4f}  {'-':>7}  {'-':>10}  {'-':>6}  "
                  f"{'infeasible':>11}  {'infeasible':>11}")
            continue
        p = result.params
        print(
            f"{fraction:>8.4f}  {p.total_sampled:>7}  {p.threshold:>10}  "
            f"{p.threshold / p.total_sampled:>6.2f}  "
            f"{_fmt(result.security_failure):>11}  {_fmt(result.liveness_failure):>11}"
        )
    return 1 if any_missing else 0


def cmd_verify(args: argparse.Namespace) -> int:
    """Check the closed forms against the simulated protocol.

    Verification uses deliberately loose parameters: probabilities a Monte-Carlo
    run can actually resolve. A 1e-9 bound is not measurable in 1e5 trials, so
    agreement is checked where both methods have signal and the closed form is
    trusted to extrapolate — which is the reason the closed form exists.
    """
    # Each case is chosen to put at least one of the two probabilities in a
    # range 1e5 trials can resolve. A configuration whose analytic answer is
    # 1e-9 tells the simulator nothing, so the cases that exercise liveness use
    # a low hold probability or a withholding adversary to pull the failure rate
    # up into measurable territory — the mechanism is the same either way.
    cases = [
        # (fraction, threshold, hold, withholds)
        (0.33, 12, args.hold, args.withhold),
        (0.33, 20, args.hold, args.withhold),
        (0.50, 20, args.hold, args.withhold),
        (0.20, 10, args.hold, args.withhold),
        (0.33, 28, 0.70, False),   # liveness bites: mean attesters ~28 of 40
        (0.33, 24, 0.99, True),    # withholding bites: only honest draws attest
        (0.45, 18, 0.85, True),    # both sides in range at once
    ]

    failures = 0
    for fraction, threshold, hold, withholds in cases:
        params = Parameters(
            n_providers=args.providers,
            adversarial_fraction=fraction,
            sample_size=8,
            max_rounds=5,
            threshold=threshold,
            hold_probability=hold,
            adversary_withholds=withholds,
        )
        for tagged in (True, False):
            analytic = security_failure(params) if tagged else 1.0 - liveness_failure(params)
            result = simulate(params, tagged=tagged, trials=args.trials, seed=args.seed)
            observed = result.confirm_rate
            ok = within_three_sigma(observed, analytic, args.trials)
            failures += not ok
            label = "tagged   " if tagged else "broadcast"
            print(
                f"f={fraction:.4f} t={threshold:<3} hold={hold:.2f} "
                f"{'wh' if withholds else '  '} {label}  "
                f"analytic {analytic:.5f}  simulated {observed:.5f}  "
                f"{'ok' if ok else 'MISMATCH'}"
            )

    print()
    print("PASS" if failures == 0 else f"FAIL ({failures} mismatches)")
    return 0 if failures == 0 else 1


def cmd_cost(args: argparse.Namespace) -> int:
    """Expected query cost of a calibrated configuration, from simulation."""
    params = Parameters(
        n_providers=args.providers,
        adversarial_fraction=args.fraction,
        sample_size=args.sample,
        max_rounds=args.rounds,
        threshold=args.threshold,
        hold_probability=args.hold,
        adversary_withholds=args.withhold,
    )
    broadcast = simulate(params, tagged=False, trials=args.trials, seed=args.seed)
    tagged = simulate(params, tagged=True, trials=args.trials, seed=args.seed + 1)
    print(f"broadcast: confirm rate {broadcast.confirm_rate:.5f}  "
          f"mean queries {broadcast.mean_queries:.1f}  "
          f"mean rounds {broadcast.mean_rounds:.2f}")
    print(f"tagged:    confirm rate {tagged.confirm_rate:.5f}  "
          f"mean queries {tagged.mean_queries:.1f}  "
          f"mean rounds {tagged.mean_rounds:.2f}")
    return 0


def main(argv: list[str] | None = None) -> int:
    base = _base_parser()
    parser = argparse.ArgumentParser(
        prog="pull-confirmation",
        description="Calibrate and verify the mempool pull confirmation threshold.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    evaluate = sub.add_parser("evaluate", parents=[base], help="score one candidate configuration")
    evaluate.add_argument("--sample", type=int, required=True, help="providers per round")
    evaluate.add_argument("--rounds", type=int, required=True)
    evaluate.add_argument("--threshold", type=int, required=True)
    evaluate.set_defaults(func=cmd_evaluate)

    calib = sub.add_parser("calibrate", parents=[base], help="find the cheapest safe configuration")
    calib.add_argument("--fractions", type=float, nargs="*", default=None)
    calib.set_defaults(func=cmd_calibrate)

    verify = sub.add_parser("verify", parents=[base], help="closed form vs simulated protocol")
    verify.add_argument("--trials", type=int, default=200_000)
    verify.add_argument("--seed", type=int, default=1)
    verify.set_defaults(func=cmd_verify)

    cost = sub.add_parser("cost", parents=[base], help="expected queries per transaction")
    cost.add_argument("--sample", type=int, required=True)
    cost.add_argument("--rounds", type=int, required=True)
    cost.add_argument("--threshold", type=int, required=True)
    cost.add_argument("--trials", type=int, default=20_000)
    cost.add_argument("--seed", type=int, default=1)
    cost.set_defaults(func=cmd_cost)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
