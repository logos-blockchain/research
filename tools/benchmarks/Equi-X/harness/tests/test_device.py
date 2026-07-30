from pathlib import Path

from equix_bench import report as reportmod
from equix_bench.cli import _load_cells_from_raw
from equix_bench.device import device_from_env, parse_cpu_model, slug
from equix_bench.protocol import Result
from equix_bench.stats import summarize


def test_slug():
    assert slug("Intel(R) Xeon(R) @ 2.10GHz") == "intel-r-xeon-r-2-10ghz"
    assert slug("") == "unknown"


X86_CPUINFO = """processor\t: 0
vendor_id\t: GenuineIntel
model name\t: Intel(R) Xeon(R) Processor @ 2.10GHz
cpu MHz\t\t: 2100.000
"""

# Raspberry Pi 5 (aarch64) has NO "model name"; the board is under "Model".
PI5_CPUINFO = """processor\t: 0
BogoMIPS\t: 108.00
Features\t: fp asimd evtstrm aes pmull sha1 sha2 crc32
CPU implementer\t: 0x41
CPU part\t: 0xd0b
processor\t: 1
CPU part\t: 0xd0b
Revision\t: d04170
Model\t\t: Raspberry Pi 5 Model B Rev 1.0
"""


def test_parse_cpu_model_x86_and_arm():
    assert parse_cpu_model(X86_CPUINFO) == "Intel(R) Xeon(R) Processor @ 2.10GHz"
    # On ARM/Pi we fall back to the board "Model" line instead of "unknown".
    assert parse_cpu_model(PI5_CPUINFO) == "Raspberry Pi 5 Model B Rev 1.0"
    assert parse_cpu_model("no fields here\n") == "unknown"


def test_pi_auto_label_is_meaningful():
    env = {"cpu": "Raspberry Pi 5 Model B Rev 1.0", "arch": "aarch64",
           "device": "cpu", "os_version": "6.6.31-rpi"}
    d = device_from_env(env)
    assert d["arch"] == "aarch64"
    assert d["label"] == "raspberry-pi-5-model-b-rev-1-0-6-6-31-rpi"


def test_device_from_env_precedence():
    env = {"cpu": "My CPU", "arch": "x86_64", "device": "cpu", "os_version": "6.1.0"}
    d = device_from_env(env)
    assert d["type"] == "cpu" and d["name"] == "My CPU" and d["arch"] == "x86_64"
    # OS version is folded into the auto label
    assert d["os_version"] == "6.1.0"
    assert d["label"] == "my-cpu-6-1-0"
    # explicit label override wins
    assert device_from_env(env, override_label="box1")["label"] == "box1"
    # a GPU runner is honored
    g = device_from_env({"cpu": "Some GPU", "arch": "sm_90", "device": "gpu", "os_version": "1"})
    assert g["type"] == "gpu"


def _raw(impl, device_label, wall):
    return {
        "schema_version": 1, "ok": True,
        "impl": {"name": impl, "version": "1", "commit": "c", "runtime_effective": "compiled"},
        "operation": "solve", "runtime_requested": "try-compile",
        "runtime_effective": "compiled",
        "env": {"cpu": device_label, "arch": "x86_64", "device": "cpu"},
        "runs": [{"index": 0, "wall_ns": wall, "solutions": 4, "compile_ns": 0,
                  "attempts": 0, "achieved_effort": 0, "verify_result": None}],
        "solutions_hex": ["00" * 16], "peak_rss_kb": 100, "error": None,
        "_label": {"challenge": "deadbeef"},
        "_device": {"type": "cpu", "name": device_label, "arch": "x86_64", "label": device_label},
        "_impl": impl, "_group": "solve",
    }


def test_summarize_stamps_device():
    r = Result.from_dict(_raw("equix-c", "cpuA", 10))
    st = summarize("equix-c", "solve", "try-compile", {"challenge": "deadbeef"}, r,
                   {"type": "cpu", "name": "cpuA", "arch": "x86_64", "label": "cpuA"})
    assert st.device_label == "cpuA" and st.device_arch == "x86_64"


def test_combine_loader_reconstructs_cells():
    raws = [_raw("equix-c", "cpuA", 10), _raw("equix-rust", "cpuA", 12),
            _raw("equix-c", "cpuB", 20), _raw("equix-rust", "cpuB", 22)]
    cells = _load_cells_from_raw(raws)
    assert len(cells) == 4
    assert {c.device_label for c in cells} == {"cpuA", "cpuB"}
    assert {c.impl for c in cells} == {"equix-c", "equix-rust"}


def test_generate_emits_cross_device_plots(tmp_path: Path):
    raws = [_raw("equix-c", "cpuA", 10), _raw("equix-rust", "cpuA", 12),
            _raw("equix-c", "cpuB", 20), _raw("equix-rust", "cpuB", 22)]
    stats = _load_cells_from_raw(raws)
    reportmod.generate(stats, [], raws, tmp_path,
                       {"timestamp": "t", "config": "test", "devices": ["cpuA", "cpuB"]})
    # faceted solve plot + cross-device chart both present
    assert (tmp_path / "plots" / "solve_time_by_runtime.png").exists()
    assert (tmp_path / "plots" / "xdev_throughput.png").exists()
    assert (tmp_path / "report.md").exists()
