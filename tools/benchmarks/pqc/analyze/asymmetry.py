#!/usr/bin/env python3
"""asymmetry.py — read a stress results file and print the sender/receiver
picture as a table.

  python3 analyze/asymmetry.py reports/pqc/results/stress-<host>-<ts>.json
  python3 analyze/asymmetry.py <file> --phase saturated
  python3 analyze/asymmetry.py <file1> <file2> <file3>    # aggregate repeats

Given several result files it reports the MEDIAN ratio across runs and their
spread, (max-min)/median. That spread is the honest error bar: this is a
throughput measurement on a machine that is never perfectly quiet, and a single
run cannot distinguish a real difference from the scheduler having a bad
second. Quote the median, and treat anything inside the spread as unresolved.

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

`--reject` switches to the per-received-byte view: receiver nanoseconds bought
per byte put on the wire, for EVERY message of the exchange, honest and
attacked. That unit is the defender's scarce resource over the attacker's — an
attacker spends bandwidth, not CPU — so it is what bounds a flood.

It is reported per message because an exchange has more than one and they are
not alike. For a KEM the encapsulator receives a public key and the
decapsulator receives a ciphertext; for Classic McEliece those two differ by
six orders of magnitude, and a single number for the algorithm would be
meaningless. A signer receives nothing, so signatures have only the one
direction.

`rej/ok` near 1.0 means the algorithm does the full work before it can reject,
so garbage costs a receiver the same as honest traffic.

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


def aggregate(docs, args):
    """Median ratio per algorithm across repeat runs, with the spread."""
    host = docs[0].get("host", {})
    print(f"role asymmetry — {host.get('cpu_brand','?')} "
          f"({host.get('ncpu','?')} cores) · {len(docs)} runs, median of")
    loads = [str((d.get("run") or {}).get("loadavg_before", "?")) for d in docs]
    print(f"1-min load at each run's start: {', '.join(loads)}"
          + ("   [not idle — see the report]"
             if any(_num(l) and _num(l) > 1.0 for l in loads) else ""))
    print()
    print(f"{'algorithm':<26} {'runs':>5} {'median':>10} {'spread':>9} "
          f"{'min':>10} {'max':>10}")
    print("-" * 74)

    order, series = [], {}
    for d in docs:
        for r in d.get("algorithms", []):
            if not r.get("enabled"):
                continue
            v = (r.get("asymmetry") or {}).get("latency_ratio_decoder_over_encoder")
            if not v:
                continue
            if r["alg"] not in series:
                series[r["alg"]] = []
                order.append((not r.get("classical"), r.get("kind"), r["alg"]))
            series[r["alg"]].append(v)

    for _, _, alg in sorted(order):
        vs = sorted(series[alg])
        med = vs[len(vs) // 2] if len(vs) % 2 else (vs[len(vs)//2 - 1] + vs[len(vs)//2]) / 2
        spread = (vs[-1] - vs[0]) / med * 100 if med else 0
        print(f"{alg:<26} {len(vs):>5} {med:>10.3f} {spread:>8.1f}% "
              f"{vs[0]:>10.3f} {vs[-1]:>10.3f}")


def _num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results", nargs="+")
    ap.add_argument("--phase", default="isolated",
                    choices=("isolated", "saturated", "contended"),
                    help="which phase's latencies to show (default: isolated)")
    ap.add_argument("--reject", action="store_true",
                    help="show the rejection path (denial-of-service view) instead")
    args = ap.parse_args()

    docs = []
    for path in args.results:
        with open(path) as f:
            docs.append(json.load(f))
    if len(docs) > 1:
        aggregate(docs, args)
        return
    d = docs[0]

    host = d.get("host", {})
    run = d.get("run", {})
    print(f"role asymmetry — {host.get('cpu_brand','?')} "
          f"({host.get('os_pretty','?')}, {host.get('ncpu','?')} cores)")
    print(f"phase: {args.phase} · {run.get('duration_ms_per_leg','?')} ms per leg"
          f" · governor {run.get('governor_after','?')}"
          + ("  [SMOKE — not measurement data]" if run.get("smoke") else ""))
    print()
    if args.reject:
        print(f"{'':<26} {'-- encoder receives --':>26} {'-- decoder receives --':>30}")
        print(f"{'algorithm':<26} {'bytes':>10} {'ns/byte':>14} "
              f"{'bytes':>10} {'ns/byte':>10} {'reject ns/B':>12} {'rej/ok':>7}")
        print("-" * 96)
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
            cpb = r.get("cost_per_received_byte")
            if not cpb:
                print(f"{r['alg']:<26}   (not measured in this run)")
                continue
            enc_r, dec_r, bad_r = cpb["encoder"], cpb["decoder"], cpb["decoder_invalid"]
            if enc_r.get("applicable"):
                enc_s = f"{enc_r['bytes']:>10} {enc_r['ns_per_byte']:>14,.2f}"
            else:
                enc_s = f"{'—':>10} {'(nothing received)':>14}"
            rej_s = (f"{bad_r['ns_per_byte']:>12,.2f}" if bad_r.get("applicable")
                     else f"{'—':>12}")
            ratio = a.get("rejection_vs_valid") or 0
            rat_s = f"{ratio:7.3f}" if bad_r.get("applicable") else f"{'—':>7}"
            print(f"{r['alg']:<26} {enc_s} "
                  f"{dec_r['bytes']:>10} {dec_r['ns_per_byte']:>10,.2f} {rej_s} {rat_s}")
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
