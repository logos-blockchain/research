#!/usr/bin/env bash
# Auto-select the FASTEST optimization flags for the MAIN C runner on THIS
# machine, then install the winner as build/runners/c/equix_runner (the path the
# `equix-c` adapter uses). So the main benchmark always runs the fastest build
# this host can produce, rather than a hard-coded guess.
#
# It builds a few candidate flag sets with the default C compiler, benchmarks the
# JIT solve path (which dominates PoW cost) with enough reps for a stable median,
# ranks them, and copies the fastest binary over the main runner. Each rep solves
# a FRESH challenge derived from the seed (a SHA-256 chain), so tuning spans the
# same varied-challenge distribution the main solve benchmark measures — not one
# fixed challenge. The seed is deterministic, so every candidate sees the IDENTICAL
# challenge stream, keeping the flag comparison a fair apples-to-apples A/B.
# Idempotent: candidate build dirs are reused, so re-runs are cheap.
#
# Tunables (env):
#   CC                        compiler to tune (default: cc)
#   EQUIX_AUTOTUNE_REPS       timed solves per candidate (default: 1000)
#   EQUIX_AUTOTUNE_WARMUP     warmup solves per candidate (default: 8)
#   EQUIX_AUTOTUNE_SEED       challenge SEED hex (default: deadbeef); each rep
#                             solves the next SHA-256-derived challenge in the chain
#   EQUIX_AUTOTUNE_EPSILON    if plain -O3 is within this fraction of the best,
#                             prefer -O3 (portable, no native/LTO lock-in on a
#                             sub-noise win). Default: 0.01 (1%). Set 0 for strict.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Ctrl+C mid-tune: exit cleanly (130) instead of a bare SIGINT kill. Nothing to
# roll back — candidate build dirs are reused and the main runner is only ever
# replaced by the atomic mv at the very end, so an interrupt leaves it untouched.
trap 'echo; echo "autotune: interrupted (Ctrl+C); main runner left unchanged." >&2; exit 130' INT

CC="${CC:-cc}"
REPS="${EQUIX_AUTOTUNE_REPS:-1000}"
WARMUP="${EQUIX_AUTOTUNE_WARMUP:-8}"
# Accept the legacy EQUIX_AUTOTUNE_CHALLENGE name as a fallback for the seed.
SEED="${EQUIX_AUTOTUNE_SEED:-${EQUIX_AUTOTUNE_CHALLENGE:-deadbeef}}"
EPS="${EQUIX_AUTOTUNE_EPSILON:-0.01}"
NPROC="$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)"
EQUIX_COMMIT="$(git -C vendored/equix rev-parse --short HEAD 2>/dev/null || echo unknown)"

command -v "$CC" >/dev/null 2>&1 || { echo "autotune: compiler '$CC' not found"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "autotune: python3 required"; exit 1; }

# Candidate flag sets on the default compiler. -O0/-O1 are excluded on purpose
# (the flag sweep shows ~2x regression); these are the fast-tier contenders.
CANDIDATES=(
  "o2|-O2 -DNDEBUG"
  "o3|-O3 -DNDEBUG"
  "o3-native|-O3 -march=native -DNDEBUG"
  "o3-lto|-O3 -flto -DNDEBUG"
)

# Median solve wall-time (ns) for a runner binary, or non-zero exit if unusable.
# NB: the Python script is passed via -c so the runner's piped JSON reaches its
# stdin (a heredoc would be consumed as the script instead).
measure() {
  printf '{"schema_version":1,"operation":"solve","runtime":"try-compile","repetitions":%d,"warmup":%d,"challenge_seed_hex":"%s"}' \
    "$REPS" "$WARMUP" "$SEED" | "$1" 2>/dev/null | python3 -c '
import sys, json, statistics
try:
    d = json.loads(sys.stdin.read().splitlines()[-1])
    assert d.get("ok") and d.get("runs")
    runs = d["runs"]
    walls = [r["wall_ns"] for r in runs if r.get("wall_ns", 0) > 0]
    # Sanity: every rep must be validly timed, and the build must really solve
    # SOMETHING across the stream. Under the varied-challenge seed, individual
    # derived challenges legitimately yield 0 solutions (~17% of them), so the
    # guard is total-solutions>0, not the old per-rep all(>0) which this breaks.
    assert len(walls) == len(runs)
    assert sum(r.get("solutions", 0) for r in runs) > 0
    print(int(statistics.median(walls)))
except BaseException:   # incl. KeyboardInterrupt on Ctrl+C: exit quietly, no stray traceback
    sys.exit(1)
'
}

# Parallel indexed arrays (macOS ships bash 3.2, which has no associative arrays).
echo "autotune: compiler=$CC  reps=$REPS  warmup=$WARMUP  seed=$SEED (challenge varied per rep)"
# NB: candidates are built with the plain version "1.0.0" — the winner becomes
# the MAIN runner, and a tuning-suffixed version would leak machine-specific
# provenance into published results. The chosen flags are recorded separately
# in build/runners/c/equix_runner.flags and build/provenance.json.
NAMES=(); OKFLAGS=(); MEDIANS=()
for entry in "${CANDIDATES[@]}"; do
  IFS='|' read -r name flags <<<"$entry"
  bdir="build/autotune/$name"
  log="build/autotune/$name.log"
  mkdir -p build/autotune
  # A copied/moved repo carries a CMake cache with old absolute paths; clean it.
  if [ -f "$bdir/CMakeCache.txt" ]; then
    recorded="$(sed -n 's/^CMAKE_CACHEFILE_DIR:INTERNAL=//p' "$bdir/CMakeCache.txt" | head -1)"
    if [ -n "$recorded" ] && [ "$recorded" != "$(cd "$bdir" && pwd)" ]; then
      rm -rf "$bdir"
    fi
  fi
  if ! cmake -S runners/c -B "$bdir" \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_C_COMPILER="$CC" \
        -DCMAKE_C_FLAGS_RELEASE="$flags" \
        -DCMAKE_POLICY_VERSION_MINIMUM=3.10 \
        -DEQUIX_C_COMMIT="$EQUIX_COMMIT" \
        -DEQUIX_C_VERSION="1.0.0" >/dev/null 2>"$log" \
     || ! cmake --build "$bdir" -j"$NPROC" --target equix_runner >>"$log" 2>&1; then
    echo "  skip $name ($flags): build failed (see $log)"
    continue
  fi
  if ! median="$(measure "$bdir/equix_runner")"; then
    echo "  skip $name ($flags): benchmark failed / no solutions"
    continue
  fi
  NAMES+=("$name"); OKFLAGS+=("$flags"); MEDIANS+=("$median")
  printf '  %-10s %-26s median %s ms\n' "$name" "$flags" \
    "$(python3 -c "print(f'{$median/1e6:.3f}')")"
done

[ "${#NAMES[@]}" -gt 0 ] || { echo "autotune: no candidate usable; keeping existing runner"; exit 1; }

# Pick the minimum-median candidate; find plain -O3's index for the tie-break.
best_i=0; o3_i=-1
for i in "${!NAMES[@]}"; do
  [ "${MEDIANS[$i]}" -lt "${MEDIANS[$best_i]}" ] && best_i=$i
  [ "${NAMES[$i]}" = "o3" ] && o3_i=$i
done

# Tie-break: if plain -O3 is within EPS of the winner, prefer it -- avoids
# locking the main runner into a native/LTO build over a sub-noise difference.
if [ "$o3_i" -ge 0 ] && [ "${NAMES[$best_i]}" != "o3" ] \
   && awk "BEGIN{exit !(${MEDIANS[$o3_i]} <= ${MEDIANS[$best_i]}*(1+$EPS))}"; then
  echo "  note: -O3 within ${EPS} of best (${NAMES[$best_i]}); preferring -O3 for portability"
  best_i=$o3_i
fi

best_name="${NAMES[$best_i]}"; best_flags="${OKFLAGS[$best_i]}"; best_median="${MEDIANS[$best_i]}"
mkdir -p build/runners/c
# Install atomically: copy to a temp path, then rename over the live runner, so a
# Ctrl+C during the copy can never leave a half-written (corrupt) main binary.
cp -f "build/autotune/$best_name/equix_runner" build/runners/c/equix_runner.tmp
mv -f build/runners/c/equix_runner.tmp build/runners/c/equix_runner
printf '%s' "$best_flags" > build/runners/c/equix_runner.flags
echo "==> fastest flags on this machine: '$best_flags' ($best_name), median $(python3 -c "print(f'{$best_median/1e6:.3f}')") ms"
echo "    installed as build/runners/c/equix_runner (used by the 'equix-c' main run)"
