#!/usr/bin/env bash
# =============================================================================
# stress.sh — sender/receiver (encoder/decoder) asymmetry sweep.
#
# Runs bench/stress/stress_roles over the config.yaml candidate list and writes
# one self-describing results file to the report tree, next to the measurement
# runs but under its own `stress-` prefix.
#
# WHAT THIS ANSWERS, and why it is a separate run from ./run.sh:
#   run.sh measures one operation at a time on one pinned core, because that is
#   how you get a comparable per-operation number. This asks the opposite
#   question — when both sides of an exchange run flat out at once, who pays?
#   That needs every core, so the two protocols are incompatible by design:
#     * NO core pinning (pinning to one core would cap the concurrency being
#       measured, which is the entire point)
#     * NO cycle counting, no thermal gating on the result
#     * governor still set where possible, for the same reason as ever: a
#       moving clock turns a ratio into noise
#   Results are therefore stamped is_stress_grade, never is_baseline_grade —
#   they are not, and must never be mistaken for, reference measurements.
#
# Usage:
#   ./stress.sh                          # full sweep, 2 s per phase-leg
#   ./stress.sh --smoke                  # 250 ms legs: pipeline check only
#   ./stress.sh --duration-ms 5000       # longer legs, tighter numbers
#   ./stress.sh --threads 4              # cap saturation width
#   ./stress.sh --alg ML-KEM-768         # one algorithm (repeatable)
#
# Prefer `make stress`, which passes the toolchain paths from versions.lock.
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STRESS_TOOL_VERSION="0.1.0"
# shellcheck source=setup/lib_platform.sh
source "$ROOT/setup/lib_platform.sh"
# shellcheck source=setup/versions.env
source "$ROOT/setup/versions.env"
LOCK="$ROOT/setup/versions.lock"
# shellcheck disable=SC1090
[ -f "$LOCK" ] && source "$LOCK" || pqb_warn "no versions.lock — run 'make build' first"

pqb_detect_platform
set -E
trap 'pqb_err "stress.sh aborted at line $LINENO while running: $BASH_COMMAND"' ERR

DURATION_MS=2000
THREADS=""
SMOKE=0
ONLY_ALGS=()
# `set -u` turns a missing option value into an "unbound variable" abort with no
# useful message; check for it and say what was wrong instead.
need_value() { [ $# -ge 2 ] || { pqb_err "$1 needs a value"; exit 2; }; }
while [ $# -gt 0 ]; do
  case "$1" in
    --smoke) SMOKE=1 ;;
    --duration-ms) need_value "$@"; DURATION_MS="$2"; shift ;;
    --threads) need_value "$@"; THREADS="$2"; shift ;;
    --alg) need_value "$@"; ONLY_ALGS+=("$2"); shift ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) pqb_err "unknown arg: $1"; exit 2 ;;
  esac
  shift
done
case "$DURATION_MS" in ''|*[!0-9]*) pqb_err "--duration-ms must be a number"; exit 2 ;; esac
if [ "$SMOKE" = 1 ]; then DURATION_MS=250; fi

BIN="$ROOT/bench/stress/stress_roles"
[ -x "$BIN" ] || { pqb_err "stress harness not built — run 'make build'"; exit 1; }

HOST="$(pqb_resolve_hostname)"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
WORK="$ROOT/.work-stress-$HOST-$TS"
RESULTS="$(pqb_results_dir "$ROOT")"
mkdir -p "$WORK" "$RESULTS"
RESULTS="$(cd "$RESULTS" && pwd)"
ROWS="$WORK/rows.jsonl"; : > "$ROWS"
META="$WORK/meta.env"
WARN_ACC=""
add_warn() { WARN_ACC="${WARN_ACC:+$WARN_ACC||}$1"; pqb_warn "$1"; }

# ---- governor ---------------------------------------------------------------
# The one privileged step, and it matters more here than anywhere: these are
# throughput ratios, and a clock that moves during one leg but not another
# corrupts the ratio rather than just widening the error bars.
GOV_BEFORE="$(pqb_get_governor)"
GOV_AFTER="$(pqb_set_governor_performance || true)"
if [ "$GOV_AFTER" != "performance" ]; then
  add_warn "governor is '$GOV_AFTER', not 'performance' — role ratios measured under a moving clock; see reports/pqc/sudo-and-measurement-conditions.md"
fi

# ---- idle check -------------------------------------------------------------
# This measures saturation throughput, so a busy machine does not merely add
# noise: load arriving during one role's leg and not the other's shifts that
# algorithm's ratio. Recorded at both ends and warned about up front, because
# the mistake is easy to make and invisible afterwards otherwise.
LOAD_BEFORE="$(pqb_loadavg)"
if [ -n "$LOAD_BEFORE" ] && awk "BEGIN{exit !($LOAD_BEFORE > 1.0)}"; then
  add_warn "system load is $LOAD_BEFORE at start — this machine is not idle, and role ratios measured under competing load are not trustworthy"
fi

# Deliberately NOT pinned: see the header. Recorded so the file says so.
# 0 means "let the harness use every online CPU".
if [ -z "$THREADS" ]; then THREADS=0; fi

if [ "$THREADS" = 0 ]; then THREADS_LABEL="auto (every online CPU)"; else THREADS_LABEL="$THREADS"; fi
pqb_log "stress sweep: duration=${DURATION_MS}ms/leg threads=$THREADS_LABEL host=$HOST"
if [ "$SMOKE" = 1 ]; then
  pqb_warn "SMOKE MODE: 250 ms legs — pipeline test only, NOT measurement data"
fi

# ---- sweep ------------------------------------------------------------------
ARGS=(--duration-ms "$DURATION_MS")
if [ "$THREADS" != 0 ]; then ARGS+=(--threads "$THREADS"); fi

wanted() {
  if [ ${#ONLY_ALGS[@]} -eq 0 ]; then return 0; fi
  local a
  for a in "${ONLY_ALGS[@]}"; do [ "$a" = "$1" ] && return 0; done
  return 1
}

while IFS=$'\t' read -r kind alg _classical; do
  [ -n "${alg:-}" ] || continue
  wanted "$alg" || continue
  pqb_log "  $kind $alg"
  if ! "$BIN" --kind "$kind" --alg "$alg" "${ARGS[@]}" >> "$ROWS"; then
    add_warn "stress harness failed for $kind/$alg"
  fi
done < <(python3 "$ROOT/bench/lib/list_algs.py" kemsig "$ROOT/config.yaml")

[ -s "$ROWS" ] || { pqb_err "no algorithms measured"; exit 1; }

# ---- provenance -------------------------------------------------------------
pqb_host_probe
{
  echo "STRESS_TOOL_VERSION=$STRESS_TOOL_VERSION"
  echo "HOSTNAME=$HOST"
  echo "OS=$PQB_OS"
  echo "ARCH=$PQB_ARCH"
  echo "KERNEL=$PQB_KERNEL"
  echo "OS_PRETTY=\"$PQB_OS_PRETTY\""
  echo "IS_RPI=$PQB_IS_RPI"
  echo "RPI_MODEL=\"$PQB_RPI_MODEL\""
  echo "CPU_BRAND=\"$PQB_CPU_BRAND\""
  echo "NCPU=$PQB_NCPU"
  echo "RAM_BYTES=$PQB_RAM_BYTES"
  echo "LOAD_BEFORE=$LOAD_BEFORE"
  echo "LOAD_AFTER=$(pqb_loadavg)"
  echo "GOVERNOR_BEFORE=$GOV_BEFORE"
  echo "GOVERNOR_AFTER=$GOV_AFTER"
  echo "DURATION_MS=$DURATION_MS"
  echo "THREADS_REQUESTED=$THREADS"
  echo "SMOKE=$SMOKE"
  echo "TS_UTC=$TS"
  echo "WARNINGS=\"$WARN_ACC\""
} > "$META"

OUT="$RESULTS/stress-${HOST}-${TS}.json"
python3 "$ROOT/bench/lib/assemble_stress.py" \
  --meta "$META" --lock "$LOCK" --rows "$ROWS" --out "$OUT" >/dev/null

echo
pqb_log "============== STRESS RUN COMPLETE =============="
python3 "$ROOT/analyze/asymmetry.py" "$OUT"
pqb_log "results: $OUT"
pqb_log "keep raw work dir? -> $WORK (safe to delete)"
