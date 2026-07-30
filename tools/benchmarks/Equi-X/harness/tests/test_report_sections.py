"""End-to-end smoke test for report generation with concurrency + mining data:
a field/format error in these sections must fail here, not at the end of an
hours-long --full run."""
import json
from pathlib import Path

from equix_bench import report as reportmod
from equix_bench.concurrency import ConcResult, LevelStat
from equix_bench.concurrency import write_csv as conc_csv
from equix_bench.mining import MiningPoint, MiningResult
from equix_bench.mining import write_csv as mining_csv
from equix_bench.protocol import Result, Run
from equix_bench.stats import summarize


def _stats_cell(impl, op, median_ns):
    runs = [Run(index=0, wall_ns=median_ns, solutions=1, compile_ns=0, attempts=0,
                achieved_effort=0, verify_result="OK")]
    res = Result(ok=True, impl_name=impl, impl_version="1", impl_commit="c",
                 operation=op, runtime_requested="try-compile", runtime_effective="compiled",
                 env={}, runs=runs, solutions_hex=None, peak_rss_kb=1000, error=None)
    return summarize(impl, op, "try-compile", {"challenge": "deadbeef"}, res,
                     {"label": "cpuX", "type": "cpu", "name": "X", "arch": "arm"})


def _conc(impl, op):
    lv = [LevelStat(1, 1, 0.01, 100.0, 100.0, 1.0, 1000),
          LevelStat(2, 2, 0.011, 182.0, 91.0, 0.91, 2000)]
    return ConcResult(device="cpuX", impl=impl, operation=op, nproc=2, reps=40,
                      challenge="deadbeef", baseline_ops_per_sec=100.0,
                      peak_ops_per_sec=182.0, knee_workers=2, levels=lv)


def _mining(impl):
    # Deliberately non-ascending efforts: the section must sort, not garble.
    pts = [MiningPoint(1000, 10, 3.6, 2.5, 3.4, 500.0, 3000.0, 0.28, 2, 2, 0.55, 0.98, 1, 16, 16, 8),
           MiningPoint(100, 10, 0.165, 0.11, 0.14, 34.0, 350.0, 6.06, 2, 2, 12.2, 1.0, 0, 16, 16, 8)]
    return MiningResult(device="cpuX", impl=impl, challenge_base="abcd", nproc=2, points=pts)


def test_generate_report_with_concurrency_and_mining(tmp_path):
    stats = [_stats_cell("equix-c", "solve", 39_000_000),
             _stats_cell("equix-rust", "solve", 4_500_000),
             _stats_cell("equix-c", "verify", 16_000),
             _stats_cell("equix-rust", "verify", 15_000)]
    conc = [_conc("equix-c", "solve"), _conc("equix-rust", "solve")]
    mining = [_mining("equix-rust")]
    meta = {"timestamp": "t", "config": "test", "cpu": "X", "nproc": 2, "devices": ["cpuX"]}

    reportmod.generate(stats, [], [], tmp_path, meta, concurrency=conc, mining=mining)
    md = (tmp_path / "report.md").read_text()
    assert "Sustained throughput under concurrency" in md
    assert "Mining rate vs difficulty" in md
    # Mining table rows must come out effort-ascending despite input order.
    assert md.index("| 100 |") < md.index("| 1000 |")
    # The 1/effort headline must use the true endpoints (100 -> 1000, a 10x rise).
    assert "10× rise" in md or "10x rise" in md
    # Message-size constancy must be reported when sizes are uniform.
    assert "constant in difficulty" in md

    conc_csv(conc, tmp_path / "concurrency.csv")
    mining_csv(mining, tmp_path / "mining.csv")
    head = (tmp_path / "mining.csv").read_text().splitlines()
    assert head[0].endswith("nonce_bytes_wire")
    assert len(head) == 3  # header + 2 points
