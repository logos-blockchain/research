"""Prove every gate can fail: apply each registered mutation, run its gate, restore the file.

    python scripts/check_mutations.py            # all mutations
    python scripts/check_mutations.py baseline   # those whose name contains "baseline"

A mutation passes this check when its gate FAILS on the mutated code. Bytecode caching is
disabled for the gate run: two mutations of equal size written within the same second would
otherwise reuse the previous mutation's cached bytecode and test the wrong code.
"""

from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
TSI = HERE.parent / "tsi" / "tsi-sim-pernode" / "src" / "tsi_sim"

# (name, file, original text, mutated text, gate)
MUTATIONS = [
    ("baseline: rounds start at zero", TSI / "topology.py",
     "rng.integers(1, int(delay_max) + 1)", "rng.integers(0, int(delay_max) + 1)",
     "tests/test_baseline.py::test_rounds_delays_are_whole_rounds_from_one_to_max"),
    ("baseline: one canonical block dropped", HERE / "src/finality_sim/baseline.py",
     "canonical[chain] = True", "canonical[chain[1:]] = True",
     "tests/test_baseline.py::test_orphan_share_matches_engine_fork_rate"),
    ("baseline: depth successor off by one", HERE / "src/finality_sim/baseline.py",
     "succ = chain[ok + d]", "succ = chain[ok + d - 1]",
     "tests/test_baseline.py::test_depth_time_counts_canonical_successors"),
    ("lcbounds: adversarial block counts down by 1", HERE / "src/finality_sim/lcbounds.py",
     "n_blks = h + 2 * i", "n_blks = h + i",
     "tests/test_lcbounds.py::test_table1_pos_bounds_reproduce"),
    ("lcbounds: attack countdown off by one", HERE / "src/finality_sim/lcbounds.py",
     "knew = max(min(k + snew + dp - s, K + 1), 1)", "knew = max(min(k + snew + dp - s + 1, K + 1), 1)",
     "tests/test_lcbounds.py::test_table1_pos_bounds_reproduce"),
    ("lcbounds: lagger probability ignores the honest rate", HERE / "src/finality_sim/lcbounds.py",
     "g = np.exp(-alpha * delta)", "g = np.exp(-delta)",
     "tests/test_lcbounds.py::test_table1_pos_bounds_reproduce"),
    ("lcbounds: attack followed for the original 80 phases only", HERE / "src/finality_sim/lcbounds.py",
     "return max(LB_STEPS, 4 * K)", "return LB_STEPS",
     "tests/test_lcbounds.py::test_lower_bound_converges_in_phases_at_depth"),
    ("lcbounds: the warm-up drops the adversary's lead", HERE / "src/finality_sim/lcbounds.py",
     "                    dst = max(0, k + i - j)", "                    dst = max(0, k - j)",
     "tests/test_lcbounds.py::test_port_matches_the_original_code_run_in_octave"),
    ("ghost: longest-chain delay counted twice", HERE / "src/finality_sim/ghost.py",
     "return 1.0 / (delta + 1.0 / rho_h)", "return 1.0 / (2 * delta + 1.0 / rho_h)",
     "tests/test_ghost.py::test_longest_chain_region_is_the_private_attack_threshold"),
    ("ghost: the prior, looser GHOST bound", HERE / "src/finality_sim/ghost.py",
     "return rho_h * math.exp(-rho_h * delta)", "return rho_h * math.exp(-2 * rho_h * delta)",
     "tests/test_ghost.py::test_region_formulas_at_unit_honest_load"),
    ("race: success threshold one block too high", HERE / "src/finality_sim/race.py",
     "if best_after[kk] >= win_at:", "if best_after[kk] >= win_at + 1:",
     "tests/test_race.py::test_race_without_premining_matches_closed_form"),
    ("race: no-premine attacker starts at the target", HERE / "src/finality_sim/race.py",
     "start = lead_before[i] if premine else since_parent[i]", "start = lead_before[i] if premine else 0",
     "tests/test_race.py::test_race_without_premining_matches_closed_form"),
    ("recovery: lower tail misses one dead time", HERE / "src/finality_sim/recovery.py",
     "le_trials = w - (n + 1) * delta", "le_trials = w - n * delta",
     "tests/test_recovery.py::test_worst_case_count_matches_slot_by_slot_process"),
    ("recovery: upper tail counts one dead time too few", HERE / "src/finality_sim/recovery.py",
     "ge_trials = w - n * delta", "ge_trials = w - (n - 1) * delta",
     "tests/test_recovery.py::test_worst_case_count_matches_slot_by_slot_process"),
    ("recovery: a tie goes to the fork", HERE / "src/finality_sim/recovery.py",
     "stats.binom.logsf(n, w, pa)", "stats.binom.logsf(n - 1, w, pa)",
     "tests/test_recovery.py::test_failure_matches_monte_carlo"),
    ("recovery: honest chain not thinned by growth", HERE / "src/finality_sim/recovery.py",
     "stats.binom.logpmf(n, w, growth * ph)", "stats.binom.logpmf(n, w, ph)",
     "tests/test_recovery.py::test_failure_matches_monte_carlo"),
    ("recovery: an underflowed lower tail is not cut off", HERE / "src/finality_sim/recovery.py",
     "lower = np.where(np.isneginf(log_le), -np.inf, lower)", "lower = lower",
     "tests/test_recovery.py::test_worst_case_pmf_holds_at_the_longest_window"),
    ("recovery: the honest chain loses the bought keys", HERE / "src/finality_sim/recovery.py",
     "ph = occupancy(f, 1.0 - alpha if honest is None else honest)", "ph = occupancy(f, 1.0 - alpha)",
     "tests/test_recovery.py::test_bought_keys_raise_the_fork_without_lowering_the_honest_chain"),    ("grr: failure counted at any symbol after confirmation", HERE / "src/finality_sim/grr_attack.py",
     "if st < lim and ys[st] >= 0:", "if best[lim - 1] > kk:",
     "tests/test_grr_attack.py::test_attack_on_fine_slots_reproduces_the_lower_bound"),
    ("grr: every honest win in a phase adds depth", HERE / "src/finality_sim/grr_attack.py",
     "                if t - last > delta:", "                if t - last > 0:",
     "tests/test_grr_attack.py::test_attack_on_fine_slots_reproduces_the_lower_bound"),
    ("grr: the lead before the target can go negative", HERE / "src/finality_sim/grr_attack.py",
     "lead = max(0, lead + a - max(d, 0))", "lead = lead + a - max(d, 0)",
     "tests/test_grr_attack.py::test_attack_on_fine_slots_reproduces_the_lower_bound"),
    ("grr: timelines count every honest win", HERE / "src/finality_sim/grr_attack.py",
     "if h and t - last > delta:", "if h:",
     "tests/test_grr_attack.py::test_timelines_replay_the_symbols"),
    ("taktikos: fork choice ignores arrival", HERE / "src/finality_sim/taktikos.py",
     "seen = np.where(arrival[cands, :nb] <= t, key[:nb], neg)",
     "seen = np.where(arrival[cands, :nb] <= np.inf, key[:nb], neg)",
     "tests/test_taktikos.py::test_constant_curve_reproduces_the_engine_orphan_share"),
    ("taktikos: interval counted from the slot after", HERE / "src/finality_sim/taktikos.py",
     "pmf[1:] = survive[:-1] * h[1:]", "pmf[1:] = survive[1:] * h[1:]",
     "tests/test_taktikos.py::test_constant_curve_interval_is_geometric"),
    ("taktikos: ramp measured from the cutoff", HERE / "src/finality_sim/taktikos.py",
     "ramp = self.amp * (d - self.gap) / max(self.cutoff - self.gap, 1)",
     "ramp = self.amp * (d - self.gap) / max(self.cutoff, 1)",
     "tests/test_taktikos.py::test_snowplow_shape"),
    ("taktikos: renewal draws ignore the producer's share", HERE / "src/finality_sim/taktikos.py",
     "    pmf = interval_pmf(curve, share)\n    n = int(", "    pmf = interval_pmf(curve, 1.0)\n    n = int(",
     "tests/test_taktikos.py::test_renewal_slots_keep_the_mean_interval"),
    ("votes: the target must be older than the lag", HERE / "src/finality_sim/votes.py",
     "while b > 0 and tree.slot[b] > t - lag:", "while b > 0 and tree.slot[b] >= t - lag:",
     "tests/test_votes.py::test_target_is_the_latest_block_old_enough"),
    ("votes: a quorum needs one seat more", HERE / "src/finality_sim/votes.py",
     "first = np.argmax(cum >= quorum, axis=0)", "first = np.argmax(cum > quorum, axis=0)",
     "tests/test_votes.py::test_certificate_needs_the_quorum_on_one_block"),
    ("votes: tips ignore arrival", HERE / "src/finality_sim/votes.py",
     "masked = np.where(arrival <= t, key[None, :], -np.inf)",
     "masked = np.where(arrival <= np.inf, key[None, :], -np.inf)",
     "tests/test_votes.py::test_tips_are_the_best_received_blocks"),
    ("votes: later slots win ties in height", HERE / "src/finality_sim/votes.py",
     "key = tree.height * c1 - tree.slot * c2 - np.arange(tree.slot.size)",
     "key = tree.height * c1 + tree.slot * c2 - np.arange(tree.slot.size)",
     "tests/test_votes.py::test_tips_are_the_best_received_blocks"),
    ("areon: a winner references every visible block", HERE / "src/finality_sim/areon.py",
     "tips = np.nonzero(vis & ~has_child)[0] + lo", "tips = np.nonzero(vis)[0] + lo",
     "tests/test_areon.py::test_honest_blocks_reference_the_tips_they_see"),
    ("areon: height from the lowest parent", HERE / "src/finality_sim/areon.py",
     "height[nb] = int(height[parents].max()) + 1", "height[nb] = int(height[parents].min()) + 1",
     "tests/test_areon.py::test_heights_and_arrivals_follow_the_parents"),
    ("areon: a block may arrive before its parents", HERE / "src/finality_sim/areon.py",
     "np.maximum(col, arrival[:, parents].max(axis=1), out=col)", "col = col",
     "tests/test_areon.py::test_heights_and_arrivals_follow_the_parents"),
    ("areon: the premined lead never decays", HERE / "src/finality_sim/areon.py",
     "lead = lead - weight[i] if lead > weight[i] else 0", "lead = lead",
     "tests/test_areon.py::test_race_on_a_chain_is_the_chain_race"),
    ("areon: depth counted from the target's parent", HERE / "src/finality_sim/areon.py",
     "d = height[ih] - height[b]", "d = height[ih] - height[b] + 1",
     "tests/test_areon.py::test_race_on_a_chain_is_the_chain_race"),
    ("areon: the recent window is ignored", HERE / "src/finality_sim/areon.py",
     "            if recent > 0:\n                while win_lo_a", "            if recent < 0:\n                while win_lo_a",
     "tests/test_areon.py::test_recent_window_scores_only_the_last_w_slots"),
    ("areon: a gap of exactly the window weighs nothing", HERE / "src/finality_sim/areon.py",
     "adv_weight[1:] = (np.diff(adv) <= window).astype(np.int64)",
     "adv_weight[1:] = (np.diff(adv) < window).astype(np.int64)",
     "tests/test_areon.py::test_blocks_without_a_short_reference_weigh_nothing"),
    ("areon: long-reference blocks weigh one", HERE / "src/finality_sim/areon.py",
     "weight = (~dag.long_ref).astype(np.int64)", "weight = np.ones(dag.long_ref.size, np.int64)",
     "tests/test_areon.py::test_blocks_without_a_short_reference_weigh_nothing"),
    ("areon: concurrent honest blocks always count", HERE / "src/finality_sim/areon.py",
     "                elif not descendants_only:", "                elif True:",
     "tests/test_areon.py::test_concurrent_honest_blocks_can_be_left_out"),
]


def check(name: str, path: pathlib.Path, old: str, new: str, gate: str) -> bool:
    src = path.read_text()
    if src.count(old) != 1:
        raise SystemExit(f"{name}: anchor not unique in {path}: {old!r}")
    path.write_text(src.replace(old, new))
    try:
        for d in HERE.parent.rglob("__pycache__"):
            shutil.rmtree(d, ignore_errors=True)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        r = subprocess.run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:warnings",
                            "-p", "no:cacheprovider", gate],
                           cwd=HERE, capture_output=True, text=True, env=env)
        return r.returncode != 0
    finally:
        path.write_text(src)


def main() -> None:
    pick = sys.argv[1] if len(sys.argv) > 1 else ""
    bad = []
    for m in MUTATIONS:
        if pick not in m[0]:
            continue
        ok = check(*m)
        print(f"  [{'ok' if ok else 'MISSED'}] {m[0]}  ->  {m[4].split('::')[-1]}")
        if not ok:
            bad.append(m[0])
    if bad:
        raise SystemExit(f"gates missed mutations: {bad}")


if __name__ == "__main__":
    main()
