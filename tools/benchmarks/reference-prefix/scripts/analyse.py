#!/usr/bin/env python3
"""Turn the measured CSVs into the report's cost tables and latency plot.

Reads results/<machine>/ and prints markdown. Every derived number is computed
here from a measured input, so a reviewer can change an assumption (GPU hash
rate, GPU price) at the top of this file and re-derive the whole table.

    python3 scripts/analyse.py
    python3 scripts/analyse.py --machines mac rpi5
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"

# --- assumptions, all stated so they can be re-priced -----------------------

# Expected candidates before the first birthday repeat is sqrt(pi/2) * 2^(b/2).
SQRT_HALF_PI = math.sqrt(math.pi / 2)

# GPU model and hash rate used for the adversary's strong-hardware column.
# 10^10 H/s is the figure logos-lips#389 argues from, and is roughly 2x above
# published hashcat Blake2b throughput for a single RTX 4090 on short inputs --
# i.e. deliberately generous to the attacker.
GPU_MODEL = "RTX 4090"
GPU_HASH_RATE = 1e10

# Spot-ish rental price for one such GPU. Generous to the attacker.
GPU_USD_PER_HOUR = 0.50

# A reference adversary budget, used to express the margin as "how many
# colliding pairs does this much money buy?" -- which is directly comparable to
# the number of pairs needed to stall a validator.
BUDGET_USD = 10_000.0

# Proposal layout, from logos-lips#389 and core/src/block/mod.rs:
#   Proposal = header(297) + references(2 + L*n) + signature(64)
HEADER_BYTES = 297
SIGNATURE_BYTES = 64
COUNT_PREFIX_BYTES = 2
MAX_BLOCK_TXS = 1024
# master's fixed 1024-entry array of full 32-byte hashes
MASTER_PROPOSAL_BYTES = 33129

PREFIX_LENGTHS = [8, 10, 12, 14, 16]

SECONDS_PER_DAY = 86400.0
SECONDS_PER_YEAR = 365.25 * SECONDS_PER_DAY


# --- loading ----------------------------------------------------------------


def load_csv(machine: str, name: str):
    path = RESULTS / machine / f"{name}.csv"
    if not path.exists():
        return None
    with path.open() as handle:
        return list(csv.DictReader(handle))


def load_rgen(machine: str) -> dict[str, float] | None:
    """Parse single-core candidate rates out of the saved criterion output.

    Falls back to the 1-thread row of throughput.csv when the criterion log is
    absent, so a partially-collected machine still yields a table.
    """
    path = RESULTS / machine / "candidate_generation.txt"
    rates: dict[str, float] = {}
    if path.exists():
        text = path.read_text()
        # criterion prints:  name \n  time: [lo mid hi] \n  thrpt: [lo mid hi]
        pattern = re.compile(
            r"candidate_generation/(\w+)\s*\n\s*time:\s*\[[\d.]+ \w+ ([\d.]+) (\w+)",
            re.MULTILINE,
        )
        unit = {"ns": 1e-9, "µs": 1e-6, "us": 1e-6, "ms": 1e-3, "s": 1.0}
        for name, value, suffix in pattern.findall(text):
            seconds = float(value) * unit[suffix]
            rates[name] = 1.0 / seconds

    if not rates:
        rows = load_csv(machine, "throughput")
        if rows:
            one = next((r for r in rows if int(r["threads"]) == 1), None)
            if one:
                rates["attacker_patched"] = float(one["candidates_per_second"])
    return rates or None


def aggregate_rate(machine: str) -> tuple[float, int] | None:
    rows = load_csv(machine, "throughput")
    if not rows:
        return None
    best = max(rows, key=lambda r: int(r["threads"]))
    return float(best["candidates_per_second"]), int(best["threads"])


# --- formatting -------------------------------------------------------------


def human_time(seconds: float) -> str:
    if seconds < 1e-3:
        return f"{seconds * 1e6:.0f} µs"
    if seconds < 1.0:
        return f"{seconds * 1e3:.0f} ms"
    if seconds < 120:
        return f"{seconds:.1f} s"
    if seconds < 7200:
        return f"{seconds / 60:.1f} min"
    if seconds < 2 * SECONDS_PER_DAY:
        return f"{seconds / 3600:.1f} h"
    if seconds < 2 * SECONDS_PER_YEAR:
        return f"{seconds / SECONDS_PER_DAY:.0f} days"
    years = seconds / SECONDS_PER_YEAR
    if years < 1e4:
        return f"{years:,.0f} years"
    return f"{years:.2e} years"


def human_usd(usd: float) -> str:
    if usd < 0.01:
        return "<$0.01"
    if usd < 1000:
        return f"${usd:,.2f}"
    if usd < 1e6:
        return f"${usd:,.0f}"
    return f"${usd / 1e6:,.1f}M"


def candidates_for_pairs(prefix_len: int, pairs: int) -> float:
    """Candidates needed for `pairs` colliding pairs at an L-byte prefix.

    One pair needs sqrt(pi/2) * 2^(b/2). Collisions accumulate as N^2 / 2^(b+1),
    so k pairs need sqrt(k) times as many -- the sqrt(k) scaling that makes the
    attacker's side of the asymmetry so much flatter than the defender's.
    """
    bits = 8 * prefix_len
    return SQRT_HALF_PI * math.sqrt(pairs) * (2.0 ** (bits / 2.0))


# --- tables -----------------------------------------------------------------


def table_birthday(machine: str) -> str:
    rows = load_csv(machine, "birthday")
    if not rows:
        return f"_no birthday data for `{machine}`_\n"

    out = [
        f"**{machine}** — measured vs. predicted first-collision counts",
        "",
        "| prefix | b (bits) | predicted N | measured N | ratio ± SE |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        out.append(
            f"| {r['prefix_bytes']} B | {r['prefix_bits']} | "
            f"{float(r['predicted_n']):,.0f} | {float(r['measured_n_mean']):,.0f} | "
            f"{float(r['ratio']):.3f} ± {float(r['ratio_stderr']):.3f} |"
        )
    return "\n".join(out) + "\n"


def table_rgen(machines: list[str]) -> str:
    out = [
        "| machine | node path | attacker (patched) | raw Blake2b | aggregate (all cores) |",
        "|---|---|---|---|---|",
    ]
    for machine in machines:
        rates = load_rgen(machine)
        if not rates:
            out.append(f"| {machine} | _(pending)_ | _(pending)_ | _(pending)_ | _(pending)_ |")
            continue
        agg = aggregate_rate(machine)
        agg_text = f"{agg[0]:.3e} /s ({agg[1]} threads)" if agg else "_(pending)_"
        out.append(
            f"| {machine} | "
            f"{rates.get('node_path', float('nan')):.3e} /s | "
            f"{rates.get('attacker_patched', float('nan')):.3e} /s | "
            f"{rates.get('blake2b_only', float('nan')):.3e} /s | "
            f"{agg_text} |"
        )
    return "\n".join(out) + "\n"


def table_generation_cost(machines: list[str]) -> str:
    """Cost of manufacturing ONE colliding pair, at each prefix length."""
    columns: list[tuple[str, float]] = []
    for machine in machines:
        rates = load_rgen(machine)
        if rates and "attacker_patched" in rates:
            columns.append((f"1 core ({machine})", rates["attacker_patched"]))
    for machine in machines:
        agg = aggregate_rate(machine)
        if agg:
            columns.append((f"1 machine ({machine}, {agg[1]}t)", agg[0]))
    columns.append((f"1 GPU ({GPU_MODEL})", GPU_HASH_RATE))
    columns.append((f"100 GPUs", GPU_HASH_RATE * 100))

    header = "| L (bytes) | b (bits) | candidates N | " + " | ".join(
        name for name, _ in columns
    ) + " |"
    sep = "|---" * (3 + len(columns)) + "|"
    out = [header, sep]

    for prefix_len in PREFIX_LENGTHS:
        need = candidates_for_pairs(prefix_len, 1)
        cells = [human_time(need / rate) for _, rate in columns]
        out.append(
            f"| {prefix_len} | {8 * prefix_len} | {need:.3e} | " + " | ".join(cells) + " |"
        )
    return "\n".join(out) + "\n"


def pairs_affordable(prefix_len: int, budget_usd: float) -> float:
    """How many colliding pairs `budget_usd` buys at this prefix length.

    Cost grows as sqrt(k), so inverting gives k = (budget / cost_of_one)^2.
    Compare against the measured number of pairs needed to stall a validator:
    the crossover L is the first one where this drops below that.
    """
    one_pair = candidates_for_pairs(prefix_len, 1)
    cost_of_one = one_pair / GPU_HASH_RATE / 3600.0 * GPU_USD_PER_HOUR
    return (budget_usd / cost_of_one) ** 2


def format_pairs(count: float) -> str:
    if count < 1.0:
        return f"**{count:.3g}** (not even one)"
    if count < 1e5:
        return f"{count:,.0f}"
    return f"{count:.2e}"


def table_summary(machines: list[str], pairs_needed: dict[str, int]) -> str:
    """The decision table: what it costs to stall each machine, per L."""
    out = [
        "| L (bytes) | proposal max | vs. master | GPU-hours for 1 pair | $ for 1 pair | "
        + " | ".join(f"$ to stall {m}" for m in machines)
        + f" | pairs for ${BUDGET_USD:,.0f} |",
        "|---" * (6 + len(machines)) + "|",
    ]
    for prefix_len in PREFIX_LENGTHS:
        proposal = (
            HEADER_BYTES
            + COUNT_PREFIX_BYTES
            + prefix_len * MAX_BLOCK_TXS
            + SIGNATURE_BYTES
        )
        ratio = MASTER_PROPOSAL_BYTES / proposal

        one_pair = candidates_for_pairs(prefix_len, 1)
        gpu_hours = one_pair / GPU_HASH_RATE / 3600.0
        one_pair_usd = gpu_hours * GPU_USD_PER_HOUR

        stall_cells = []
        for machine in machines:
            k = pairs_needed.get(machine)
            if k is None:
                stall_cells.append("_(pending)_")
                continue
            need = candidates_for_pairs(prefix_len, k)
            usd = need / GPU_HASH_RATE / 3600.0 * GPU_USD_PER_HOUR
            stall_cells.append(human_usd(usd))

        out.append(
            f"| {prefix_len} | {proposal:,} B | {ratio:.2f}× | {gpu_hours:,.1f} | "
            f"{human_usd(one_pair_usd)} | "
            + " | ".join(stall_cells)
            + f" | {format_pairs(pairs_affordable(prefix_len, BUDGET_USD))} |"
        )
    return "\n".join(out) + "\n"


def reconstruction_summary(machine: str) -> str:
    rows = load_csv(machine, "reconstruction")
    if not rows:
        return f"_no reconstruction data for `{machine}`_\n"

    out = []
    for block_txs in sorted({int(r["block_txs"]) for r in rows}, reverse=True):
        subset = [
            r
            for r in rows
            if int(r["block_txs"]) == block_txs and r["policy"] == "uncapped"
        ]
        subset.sort(key=lambda r: int(r["k"]))
        baseline = float(subset[0]["median_s"]) if subset else float("nan")

        out.append(f"**{machine}**, block of {block_txs} transactions")
        out.append("")
        out.append("| k | combinations | median | vs. 1 s slot |")
        out.append("|---|---|---|---|")
        for r in subset:
            median = float(r["median_s"])
            verdict = "**over slot**" if r["over_slot"] == "true" else "within"
            out.append(
                f"| {r['k']} | {int(r['combinations']):,} | {human_time(median)} | {verdict} |"
            )
        first_over = next((int(r["k"]) for r in subset if r["over_slot"] == "true"), None)
        out.append("")
        out.append(
            f"Per-combination cost ≈ {human_time(baseline)}; "
            + (
                f"the 1 s slot is first exceeded at **k = {first_over}**."
                if first_over is not None
                else "the slot was not exceeded within the measured range."
            )
        )
        out.append("")
    return "\n".join(out)


def pairs_to_stall(machine: str) -> int | None:
    """Smallest k whose uncapped reconstruction exceeds the slot, at a full block."""
    rows = load_csv(machine, "reconstruction")
    if not rows:
        return None
    full = max(int(r["block_txs"]) for r in rows)
    candidates = [
        int(r["k"])
        for r in rows
        if r["policy"] == "uncapped"
        and int(r["block_txs"]) == full
        and r["over_slot"] == "true"
    ]
    return min(candidates) if candidates else None


# --- plot -------------------------------------------------------------------


def plot(machines: list[str]) -> None:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print(
            "\n_(matplotlib not installed — skipping the plot; "
            "`python3 -m pip install matplotlib` to enable it)_",
            file=sys.stderr,
        )
        return

    fig, ax = plt.subplots(figsize=(9, 5.5))
    colours = {"mac": "#4C72B0", "rpi5": "#C44E52"}

    plotted = False
    for machine in machines:
        rows = load_csv(machine, "reconstruction")
        if not rows:
            continue
        for block_txs, style in ((1024, "-o"), (128, "--s")):
            subset = [
                r
                for r in rows
                if r["policy"] == "uncapped" and int(r["block_txs"]) == block_txs
            ]
            if not subset:
                continue
            subset.sort(key=lambda r: int(r["k"]))
            ax.plot(
                [int(r["k"]) for r in subset],
                [float(r["median_s"]) for r in subset],
                style,
                color=colours.get(machine, None),
                markersize=4,
                linewidth=1.6,
                label=f"{machine}, {block_txs} txs",
            )
            plotted = True

    if not plotted:
        return

    ax.axhline(1.0, color="#555555", linestyle=":", linewidth=1.5)
    ax.text(
        0.02,
        1.15,
        "1 s slot — block production stalls above this line",
        transform=ax.get_yaxis_transform(),
        fontsize=9,
        color="#555555",
    )

    ax.set_yscale("log")
    ax.set_xlabel("k — ambiguous references in the proposal (colliding pairs in the mempool)")
    ax.set_ylabel("reconstruction time (s, log scale)")
    ax.set_title("Uncapped reconstruction cost doubles with every colliding pair")
    ax.grid(True, which="both", alpha=0.25, linewidth=0.6)
    ax.legend(frameon=False)
    fig.tight_layout()

    out = RESULTS / "reconstruction-latency.png"
    fig.savefig(out, dpi=160)
    print(f"\n_wrote {out.relative_to(ROOT)}_", file=sys.stderr)


# --- main -------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--machines",
        nargs="+",
        default=None,
        help="machine labels to include (default: whatever exists under results/)",
    )
    args = parser.parse_args()

    machines = args.machines
    if machines is None:
        machines = sorted(
            d.name for d in RESULTS.iterdir() if d.is_dir() and any(d.iterdir())
        )
    if not machines:
        print("no results found under results/", file=sys.stderr)
        raise SystemExit(1)

    pairs_needed = {m: k for m in machines if (k := pairs_to_stall(m)) is not None}

    print("## Candidate-generation rate (R_gen)\n")
    print(table_rgen(machines))

    print("\n## Birthday model, measured against prediction\n")
    for machine in machines:
        print(table_birthday(machine))

    print("\n## Cost of manufacturing one colliding pair\n")
    print(table_generation_cost(machines))

    print("\n## Reconstruction latency\n")
    for machine in machines:
        print(reconstruction_summary(machine))

    print("\n## Decision table\n")
    print(
        f"_Assumes {GPU_MODEL} at {GPU_HASH_RATE:.1e} H/s, "
        f"${GPU_USD_PER_HOUR:.2f}/GPU-hour._\n"
    )
    for machine, k in pairs_needed.items():
        print(f"_Stalling **{machine}** needs k = {k} colliding pairs (measured)._")
    print()
    print(table_summary(machines, pairs_needed))

    plot(machines)


if __name__ == "__main__":
    main()
