"""The DoS-protection evaluation must correctly quantify the attacker/defender
asymmetry that makes Equi-X an effective client puzzle."""
from equix_bench.dosprotect import DEFAULT_THRESHOLD, assess, min_verify_seconds
from equix_bench.stats import CellStats


def _cell(op, impl, median_ns, label=None, device="cpuX"):
    return CellStats(
        impl=impl, operation=op, runtime_requested="try-compile",
        runtime_effective="compiled", label=label or {},
        reps=3, ok=True, min_ns=median_ns, median_ns=median_ns, mean_ns=median_ns,
        stddev_ns=0, p95_ns=median_ns, solutions_mean=1, compile_median_ns=0,
        attempts_mean=0, achieved_effort_mean=0, solves_per_sec=0, hashes_per_sec=0,
        peak_rss_kb=1000, verify_result="OK", device_label=device,
    )


def test_min_verify_seconds():
    stats = [
        _cell("verify", "equix-c", 40_000),      # 40 µs
        _cell("verify", "equix-rust", 44_000),   # 44 µs
    ]
    assert abs(min_verify_seconds(stats, "cpuX") - 40e-6) < 1e-12
    assert min_verify_seconds(stats, "other") is None


def test_effective_protection_on_realistic_numbers():
    # verify ~40 µs; crafting a token at effort 1000 ~ 4.4 s -> huge asymmetry.
    stats = [
        _cell("verify", "equix-c", 40_000),
        _cell("effort", "equix-c", 4_400_000_000, {"target_effort": 1000}),
        _cell("effort", "equix-rust", 4_600_000_000, {"target_effort": 1000}),
    ]
    rows, effective, threshold = assess(stats)
    assert threshold == DEFAULT_THRESHOLD
    assert len(rows) == 1
    r = rows[0]
    # attacker uses the FASTER impl (equix-c here, 4.4s)
    assert r.attacker_impl == "equix-c"
    assert abs(r.protection_factor - (4.4 / 40e-6)) < 1.0      # ~110,000x
    assert effective is True
    assert r.verify_per_sec > 20_000                            # defender screens >20k/s
    assert r.attacker_tokens_per_sec < 1                        # attacker <1 token/s


def test_weak_protection_flagged():
    # Pathological: verify as expensive as crafting -> not effective.
    stats = [
        _cell("verify", "equix-c", 1_000_000_000),                        # 1 s verify
        _cell("effort", "equix-c", 2_000_000_000, {"target_effort": 10}),  # 2 s craft
    ]
    rows, effective, _ = assess(stats)
    assert rows and effective is False
    assert rows[0].protection_factor < 10
