"""`combine` merges runs from many devices into ONE faceted report — including
the concurrency and mining sections/figures, which the per-run CSVs carry and
which must survive the CSV round-trip. Auto-discovery walks a tree and identifies
runs by their raw record file, taking device identity from the records (not paths)
so an arbitrary collected layout still combines correctly."""
import json
from pathlib import Path

from equix_bench import report as reportmod
from equix_bench.cli import _discover_runs, cmd_combine
from equix_bench.concurrency import ConcResult, LevelStat
from equix_bench.concurrency import read_csv as conc_read
from equix_bench.concurrency import write_csv as conc_write
from equix_bench.mining import MiningPoint, MiningResult
from equix_bench.mining import read_csv as mining_read
from equix_bench.mining import write_csv as mining_write
from equix_bench.protocol import Result, Run
from equix_bench.stats import summarize


# --------------------------------------------------------------- CSV round-trips


def _conc(device, impl):
    lv = [LevelStat(1, 1, 0.01, 100.0, 100.0, 1.0, 1000),
          LevelStat(2, 2, 0.011, 182.0, 91.0, 0.91, 2000)]
    return ConcResult(device=device, impl=impl, operation="solve", nproc=2, reps=40,
                      challenge="deadbeef", baseline_ops_per_sec=100.0,
                      peak_ops_per_sec=182.0, knee_workers=2, levels=lv)


def _mining(device, impl):
    pts = [MiningPoint(100, 10, 0.165, 0.11, 0.14, 34.0, 350.0, 6.06, 2, 2, 12.2, 1.0, 0, 16, 16, 8),
           MiningPoint(1000, 10, 3.6, 2.5, 3.4, 500.0, 3000.0, 0.28, 2, 2, 0.55, 0.98, 1, 16, 16, 8)]
    return MiningResult(device=device, impl=impl, challenge_base="abcd", nproc=2, points=pts)


def test_concurrency_csv_roundtrip(tmp_path):
    orig = [_conc("cpuA", "equix-c"), _conc("cpuA", "equix-rust")]
    conc_write(orig, tmp_path / "c.csv")
    back = conc_read(tmp_path / "c.csv")
    assert {r.impl for r in back} == {"equix-c", "equix-rust"}
    r = next(x for x in back if x.impl == "equix-c")
    # Summary fields are re-derived from the levels, matching measure().
    assert r.nproc == 2 and r.knee_workers == 2
    assert r.baseline_ops_per_sec == 100.0 and r.peak_ops_per_sec == 182.0
    assert [lv.workers for lv in r.levels] == [1, 2]


def test_mining_csv_roundtrip(tmp_path):
    mining_write([_mining("cpuA", "equix-rust")], tmp_path / "m.csv")
    back = mining_read(tmp_path / "m.csv")
    assert len(back) == 1
    r = back[0]
    assert r.nproc == 2 and r.challenge_base == "abcd"
    assert [p.effort for p in r.points] == [100, 1000]  # sorted on read
    assert r.points[0].solution_bytes_max == 16


# ------------------------------------------------------------ discovery + combine


def _raw_record(device_label, impl, op, runtime, median_ns):
    """A minimal enriched raw record in the on-wire schema cmd_run persists to
    raw/results.json (schema_version + nested impl block + _* enrichment)."""
    return {
        "schema_version": 1, "ok": True,
        "impl": {"name": impl, "version": "1", "commit": "c"},
        "operation": op, "runtime_requested": runtime, "runtime_effective": "compiled",
        "env": {"cpu": device_label, "arch": "arm"},
        "runs": [{"index": 0, "wall_ns": median_ns, "solutions": 1, "compile_ns": 0,
                  "attempts": 0, "achieved_effort": 0, "verify_result": "OK"}],
        "solutions_hex": None, "peak_rss_kb": 1000, "error": None,
        "_label": {"challenge": "deadbeef"}, "_impl": impl, "_group": op,
        "_device": {"label": device_label, "type": "cpu", "name": device_label, "arch": "arm"},
    }


def _write_run(dirpath: Path, device_label, ts, with_extras=False):
    dirpath.mkdir(parents=True, exist_ok=True)
    (dirpath / "raw").mkdir(exist_ok=True)
    recs = [_raw_record(device_label, "equix-c", "solve", "try-compile", 39_000_000),
            _raw_record(device_label, "equix-rust", "solve", "try-compile", 4_500_000),
            # two runtimes of the same op must NOT collide during de-dup
            _raw_record(device_label, "equix-c", "solve", "interpret", 42_000_000),
            _raw_record(device_label, "equix-rust", "solve", "interpret", 12_000_000)]
    (dirpath / "raw" / "results.json").write_text(json.dumps(recs))
    (dirpath / "run_meta.json").write_text(json.dumps({"timestamp": ts, "devices": [device_label]}))
    if with_extras:
        conc_write([_conc(device_label, "equix-c"), _conc(device_label, "equix-rust")],
                   dirpath / "concurrency.csv")
        mining_write([_mining(device_label, "equix-rust")], dirpath / "mining.csv")


def test_discover_runs_is_layout_agnostic(tmp_path):
    # Two different nesting depths under one tree; discovery finds both.
    _write_run(tmp_path / "deviceA" / "main", "cpu-a", "2026-07-27T10:00:00+00:00")
    _write_run(tmp_path / "host-b" / "results" / "main", "cpu-b", "2026-07-27T11:00:00+00:00")
    found = _discover_runs(tmp_path)
    assert len(found) == 2
    assert {p.name for p in found} == {"main"}


class _Args:
    def __init__(self, **kw):
        self.inputs = None
        self.root = None
        self.out = None
        self.__dict__.update(kw)


def test_combine_root_produces_faceted_multidevice_report(tmp_path):
    _write_run(tmp_path / "A" / "main", "cpu-a", "2026-07-27T10:00:00+00:00", with_extras=True)
    _write_run(tmp_path / "B" / "main", "cpu-b", "2026-07-27T11:00:00+00:00", with_extras=True)
    out = tmp_path / "combined"
    rc = cmd_combine(_Args(root=str(tmp_path), out=str(out)))
    assert rc == 0
    md = (out / "report.md").read_text()
    # Both devices named as CPUs in the header.
    assert "cpu-a" in md and "cpu-b" in md
    # Concurrency + mining sections survived the combine (they were dropped before).
    assert "Sustained throughput under concurrency" in md
    assert "Mining rate vs difficulty" in md
    # Multi-device concurrency table gains a device column.
    assert "| device | impl | operation |" in md
    # Cross-device (xdev_*) headline figures are emitted with >1 device.
    assert any((out / "plots").glob("xdev_*.png"))
    # The faceted concurrency/mining figures exist.
    assert (out / "plots" / "concurrency_solve.png").exists()
    assert (out / "plots" / "mining_rate.png").exists()


def test_combine_dedups_reruns_keeping_newest(tmp_path):
    # Same device measured twice (a re-run): the newer run must replace, not
    # double the cell count.
    _write_run(tmp_path / "old" / "main", "cpu-a", "2026-07-27T09:00:00+00:00")
    _write_run(tmp_path / "new" / "main", "cpu-a", "2026-07-27T15:00:00+00:00")
    out = tmp_path / "combined"
    rc = cmd_combine(_Args(root=str(tmp_path), out=str(out)))
    assert rc == 0
    rows = (out / "results.csv").read_text().strip().splitlines()[1:]
    # 2 impls x 2 runtimes x 1 device = 4 cells, NOT 8 (dedup collapsed the re-run).
    assert len(rows) == 4
