#!/usr/bin/env bash
# Hands-off Raspberry Pi 5 measurement for the EmPoWering Blend threshold.
#
#   make pi5          (from simulations/EmPoWering)
#
# Does everything: preflight (arch, tools, sibling checkout), a pinned single-core
# benchmark run three times with thermal guards, median extraction, a generated
# configs/pi5.toml, the threshold re-derivation table, and a local results commit
# on a dated branch. Push is attempted and failure tolerated.
#
# PI5_DEV=1 bypasses the Pi-specific checks so the pipeline itself can be tested
# on a development machine; results produced that way are labelled dev.
set -euo pipefail
cd "$(dirname "$0")/.."

RUNS=${RUNS:-3}
CORE=${CORE:-3}
TEMP_LIMIT_C=${TEMP_LIMIT_C:-80}
COOL_TO_C=${COOL_TO_C:-65}
DEV=${PI5_DEV:-0}
STAMP=$(date +%Y%m%d-%H%M)
OUT=bench-poseidon2/results
mkdir -p "$OUT"
LOG="$OUT/pi5-$STAMP.log"

say() { printf '%s\n' "$*" | tee -a "$LOG"; }

# ---------- preflight ----------
say "== preflight =="
if [ "$DEV" != 1 ]; then
  [ "$(uname -m)" = aarch64 ] || { say "FATAL: need a 64-bit OS (uname -m = $(uname -m))"; exit 1; }
  grep -qi 'raspberry pi 5' /proc/device-tree/model 2>/dev/null \
    && say "board: $(tr -d '\0' </proc/device-tree/model)" \
    || say "WARN: not a Pi 5 by device tree; continuing, results will say so"
fi
command -v cargo >/dev/null || {
  say "installing rust (non-interactive)"
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y >>"$LOG" 2>&1
  . "$HOME/.cargo/env"
}
[ -d ../../../logos-blockchain/zk/poseidon2 ] || {
  say "cloning sibling logos-blockchain (shallow, https)"
  git clone --depth 1 https://github.com/logos-blockchain/logos-blockchain.git ../../../logos-blockchain >>"$LOG" 2>&1
}

temp_c() {
  local t=0 f
  for f in /sys/class/thermal/thermal_zone*/temp; do
    [ -r "$f" ] && read -r v <"$f" && [ "$v" -gt "$t" ] && t=$v
  done 2>/dev/null || true
  echo $((t / 1000))
}
governor=$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo unknown)
say "governor: $governor   temp: $(temp_c) C   runs: $RUNS on core $CORE"

# ---------- build once ----------
say "== building benchmark (first build compiles arkworks; minutes on a Pi) =="
( cd bench-poseidon2 && cargo build --release >>"../$LOG" 2>&1 )

PIN=""
if command -v taskset >/dev/null; then PIN="taskset -c $CORE"; else say "WARN: no taskset; unpinned"; fi

# ---------- guarded runs ----------
declare -a FILES=()
attempt=0
while [ "${#FILES[@]}" -lt "$RUNS" ]; do
  attempt=$((attempt + 1)); [ $attempt -le $((RUNS * 3)) ] || { say "FATAL: too many invalid runs"; exit 1; }
  if [ "$DEV" != 1 ]; then
    while [ "$(temp_c)" -gt "$COOL_TO_C" ]; do say "cooling: $(temp_c) C > $COOL_TO_C C"; sleep 20; done
  fi
  t0=$(temp_c)
  f="$OUT/pi5-$STAMP-run$attempt.txt"
  say "-- run $attempt (start ${t0} C)"
  $PIN ./bench-poseidon2/target/release/pow-bench >"$f" 2>&1 || { say "run failed, see $f"; exit 1; }
  t1=$(temp_c)
  if [ "$DEV" != 1 ] && [ "$t1" -gt "$TEMP_LIMIT_C" ]; then
    say "   DISCARDED: finished at ${t1} C > ${TEMP_LIMIT_C} C (throttle risk)"
  else
    say "   ok (end ${t1} C)"; FILES+=("$f")
  fi
done

# ---------- medians, config, derivation, commit ----------
say "== results =="
python3 - "$STAMP" "$DEV" "${FILES[@]}" <<'PY' | tee -a "$LOG"
import re, statistics, sys, pathlib, subprocess, datetime
stamp, dev, files = sys.argv[1], sys.argv[2] == "1", sys.argv[3:]
keys = ["one_permutation_ns", "blend_naive_ns", "blend_opt_ns", "reward_naive_ns", "reward_opt_ns"]
runs = []
for f in files:
    txt = pathlib.Path(f).read_text()
    vals = {k: float(re.search(rf"MACHINE {k}=(\d+)", txt).group(1)) for k in keys}
    runs.append(vals)
med = {k: statistics.median(r[k] for r in runs) for k in keys}
spread = {k: (max(r[k] for r in runs) - min(r[k] for r in runs)) / med[k] for k in keys}
label = "dev-machine" if dev else "raspberry-pi-5"
for k in keys:
    flag = "  (!! spread >5%, consider rerunning)" if spread[k] > 0.05 else ""
    print(f"  {k:<22} median {med[k]:>10,.0f} ns   spread {spread[k]:.1%}{flag}")

# generated config: specified values with the measured [work]
base = pathlib.Path("configs/specified.toml").read_text()
def setk(text, key, val):
    return re.sub(rf"(?m)^({key}\s*=\s*)\S+", rf"\g<1>{val}", text)
out = base
out = setk(out, "seconds_per_candidate", f"{med['blend_naive_ns']/1e9:.6e}")
out = setk(out, "seconds_per_candidate_opt", f"{med['blend_opt_ns']/1e9:.6e}")
out = setk(out, "seconds_per_candidate_reward", f"{med['reward_naive_ns']/1e9:.6e}")
out = setk(out, "seconds_per_permutation", f"{med['one_permutation_ns']/1e9:.6e}")
for k in ("pi5_slowdown", "pi5_slowdown_low", "pi5_slowdown_high"):
    out = setk(out, k, "1.0")   # measured on the target itself; the band is retired
out = out.replace("# ASSUMED  midpoint of the 4-8x band", "# 1.0: measured on the target itself")
out = out.replace('name = "specified"', f'name = "pi5-{stamp}"', 1)
out = out.replace('description = "The parameter set as specified in the EmPoWering RFC"',
                  f'description = "Specified set with [work] MEASURED on {label}, {stamp}"', 1)
pathlib.Path("configs/pi5.toml").write_text(out)
print(f"\n  wrote configs/pi5.toml  ({label})")

# the re-derivation table the whole exercise exists for
n = med["blend_naive_ns"] / 1e9
print(f"\n  threshold re-derivation (naive basis {n*1e6:.1f} us/candidate):")
print(f"  {'k':>6} {'sec/msg 1 core':>15} {'msgs/day 1 core':>16} {'sec/msg 4 cores':>16}")
for k in range(18, 25):
    s = (2**k) * n
    print(f"  {'p/2^'+str(k):>6} {s:>15,.0f} {86400/s:>16,.0f} {s/4:>16,.0f}")
import math
for target, basis, cores in ((60, "one core", 1), (60, "whole board", 4)):
    kk = round(math.log2(target * cores / n))
    print(f"  ~60 s per message on {basis}: p/2^{kk}")
print("\n  next: make blend CONFIG=configs/pi5.toml ; then decide the reference basis")
print("  and, if the exponent moves, update BLEND_DIFFICULTY_BASE in the Mantle spec.")
PY

# ---------- local commit on a dated branch; push attempted, failure tolerated ----------
if [ "$DEV" = 1 ]; then
  say "dev mode: skipping commit and push (results in $OUT, config at configs/pi5.toml)"
  say "== done: log at $LOG =="
  exit 0
fi
BR="pi5-measurement-$STAMP"
git add "$OUT" configs/pi5.toml
git checkout -q -b "$BR" 2>/dev/null || git checkout -q "$BR"
git commit -q -m "EmPoWering: Pi 5 measurement $STAMP (raw runs + generated config)" || true
git push -u origin "$BR" >>"$LOG" 2>&1 && say "pushed branch $BR" \
  || say "push failed (no credentials?): branch $BR is committed locally — push it when convenient"
say "== done: log at $LOG =="
