#!/usr/bin/env python3
"""asymmetry.py — read a stress results file and print the sender/receiver
picture as a table.

  python3 analyze/asymmetry.py reports/pqc/results/stress-<host>-<ts>.json
  python3 analyze/asymmetry.py <file> --phase saturated

The column that matters is `dec/enc`: the cost of consuming a message divided
by the cost of producing one. `per-sess` is the same ratio when the keypair is
ephemeral and generated per exchange (the TLS shape); `contended` is how many
decoder cores one encoder thread keeps busy when both roles compete for the
machine at once — the same quantity, measured under load instead of derived.

`mean` is the same ratio taken from each role's mean cost per operation rather
than its median. It exists because a median is quantised by the platform's
clock: macOS resolves ~1 us, so a 6 us ML-KEM operation lands on a 1 us grid and
its median ratio can only take coarse values. The mean is computed over every
operation the leg completed — often hundreds of thousands — so for anything
faster than ~20 us the `mean` column is the more trustworthy of the two. Where
the two disagree, the operation is too fast for this machine's clock, not
unstable.

`per-sess` prints "-" when it would rest on fewer than MIN_SETUP_SAMPLES keygen
measurements. Classic McEliece keygen takes whole seconds, so a 2 s leg yields
one or two samples — a ratio computed from that is a number, not a measurement,
and printing it would invite it to be quoted.

  > 1   the receiver pays more than the sender. A peer can impose more work
        than it performs, and the gap is the multiplier an attacker gets for
        free. Rate-limit on the receiving side.
  ≈ 1   symmetric; the exchange costs both peers the same.
  < 1   the sender pays more. Cheap to verify, expensive to produce — the
        comfortable direction for a node that consumes many messages from
        many peers.

`--reject` switches to the denial-of-service view: what the decoder spends on a
message that does NOT verify. `rej/ok` near 1.0 means the algorithm does the
full work before it can reject, so garbage costs a receiver the same as real
traffic. `ns/byte` is receiver nanoseconds bought per byte the attacker sends,
which is the figure that bounds a flood — an attacker spends bandwidth, not
CPU, so a small wire object backed by expensive verification is the dangerous
shape.

Ratios are the portable output. The absolute rates in the same file describe
one machine under saturation and do not transfer.
"""
from __future__ import annotations
import argparse
import json
import sys


MIN_SETUP_SAMPLES = 30


def fmt_ns(v):
    if not v:
        return "       -"
    if v >= 1e6:
        return f"{v/1e6:7.2f}ms"
    if v >= 1e3:
        return f"{v/1e3:7.2f}us"
    return f"{v:7.0f}ns"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--phase", default="isolated",
                    choices=("isolated", "saturated", "contended"),
                    help="which phase's latencies to show (default: isolated)")
    ap.add_argument("--reject", action="store_true",
                    help="show the rejection path (denial-of-service view) instead")
    args = ap.parse_args()

    with open(args.results) as f:
        d = json.load(f)

    host = d.get("host", {})
    run = d.get("run", {})
    print(f"role asymmetry — {host.get('cpu_brand','?')} "
          f"({host.get('os_pretty','?')}, {host.get('ncpu','?')} cores)")
    print(f"phase: {args.phase} · {run.get('duration_ms_per_leg','?')} ms per leg"
          f" · governor {run.get('governor_after','?')}"
          + ("  [SMOKE — not measurement data]" if run.get("smoke") else ""))
    print()
    if args.reject:
        print(f"{'algorithm':<26} {'wire bytes':>10} {'accept':>10} {'reject':>10} "
              f"{'rej/ok':>7} {'ns/byte':>12}")
        print("-" * 80)
    else:
        print(f"{'algorithm':<26} {'roles':<16} {'encoder':>9} {'decoder':>9} "
              f"{'dec/enc':>9} {'mean':>7} {'per-sess':>9} {'contended':>9}  cheaper")
        print("-" * 112)

    rows = [r for r in d.get("algorithms", []) if r.get("enabled")]
    # classical baselines first: the comparison only means something against
    # what is deployed today
    rows.sort(key=lambda r: (not r.get("classical"), r.get("kind"), r.get("alg")))

    absent = [r for r in d.get("algorithms", []) if not r.get("enabled")]
    for r in rows:
        ph = (r.get("phases") or {}).get(args.phase) or {}
        enc, dec = ph.get("encoder") or {}, ph.get("decoder") or {}
        a = r.get("asymmetry") or {}
        el = (enc.get("latency_ns") or {}).get("median")
        dl = (dec.get("latency_ns") or {}).get("median")
        ratio = (dl / el) if (el and dl) else 0
        roles = f"{(r.get('roles') or {}).get('encoder','?')}/{(r.get('roles') or {}).get('decoder','?')}"
        # mean cost per op: immune to the clock grid that quantises a median
        ec, dc = enc.get("cpu_ns_per_op"), dec.get("cpu_ns_per_op")
        mean_ratio = (dc / ec) if (ec and dc) else 0

        # per-session leans on the keygen leg; refuse to show it when that leg
        # got too few samples to mean anything (see module docstring)
        setup = ((r.get("phases") or {}).get("isolated") or {}).get("decoder_setup") or {}
        setup_n = (setup.get("latency_ns") or {}).get("samples") or 0
        sess = a.get("latency_ratio_per_session") or 0
        sess_s = f"{sess:9.2f}" if setup_n >= MIN_SETUP_SAMPLES else f"{'-':>9}"

        if args.reject:
            iso = (r.get("phases") or {}).get("isolated") or {}
            wire = (r.get("sizes") or {}).get("encoder_emits")
            if "decoder_invalid" not in iso:
                # a run from before the rejection path existed — say so rather
                # than implying the algorithm has none
                print(f"{r['alg']:<26} {wire or 0:>10} "
                      f"{'—':>10} {'—':>10} {'—':>7} {'—':>12}   (not measured in this run)")
                continue
            bad = iso.get("decoder_invalid") or {}
            if not bad.get("applicable"):
                print(f"{r['alg']:<26} {wire or 0:>10} "
                      f"{'—':>10} {'—':>10} {'—':>7} {'—':>12}   (no rejection path)")
                continue
            bl = (bad.get("latency_ns") or {}).get("median")
            print(f"{r['alg']:<26} {wire or 0:>10} {fmt_ns(dl):>10} {fmt_ns(bl):>10} "
                  f"{a.get('rejection_vs_valid') or 0:7.3f} "
                  f"{a.get('rejection_ns_per_wire_byte') or 0:12.1f}")
            continue

        mark = "  <-- receiver pays" if ratio > 1.05 else ""
        print(f"{r['alg']:<26} {roles:<16} {fmt_ns(el)} {fmt_ns(dl)} "
              f"{ratio:9.2f} {mean_ratio:7.2f} {sess_s} "
              f"{a.get('contended_decoder_cores_per_encoder_core') or 0:9.2f}"
              f"  {a.get('cheaper_side','?'):<8}{mark}")

    if absent:
        print()
        print("absent (not enabled in this build):")
        for r in absent:
            print(f"  {r.get('alg')}: {r.get('reason','')}")

    for w in d.get("warnings") or []:
        print(f"\nWARN: {w}", file=sys.stderr)


if __name__ == "__main__":
    main()
