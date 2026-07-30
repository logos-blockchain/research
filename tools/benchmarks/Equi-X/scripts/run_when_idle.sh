#!/usr/bin/env bash
# Run a command only once the machine is idle — so other workloads can't skew a
# benchmark. This is how the published mining numbers were measured (see
# docs/findings.md §7a): the run starts only after CPU idle stays above a
# threshold for several consecutive polls.
#
#   ./scripts/run_when_idle.sh python3 -m equix_bench run --config configs/mining.toml --out results/mining
#
# Env overrides:
#   IDLE_THRESH=85   required % CPU idle          IDLE_NEED=3   consecutive polls
#   IDLE_POLL=25     seconds between polls        IDLE_MAXWAIT=21600  give-up (s)
set -uo pipefail

[ $# -ge 1 ] || { echo "usage: $0 <command> [args...]" >&2; exit 2; }

THRESH="${IDLE_THRESH:-85}"
NEED="${IDLE_NEED:-3}"
POLL="${IDLE_POLL:-25}"
MAXWAIT="${IDLE_MAXWAIT:-21600}"

cpu_idle() {
  case "$(uname -s)" in
    Darwin) top -l 2 -s 1 -n 0 2>/dev/null | grep 'CPU usage' | tail -1 \
              | sed -E 's/.* ([0-9.]+)% idle.*/\1/' ;;
    Linux)  vmstat 1 2 2>/dev/null | tail -1 | awk '{print $15}' ;;
    *)      echo 100 ;;  # unknown platform: don't block
  esac
}

ok=0; elapsed=0
echo "waiting for idle (>= ${THRESH}% CPU idle x ${NEED} consecutive polls)..."
while :; do
  idle="$(cpu_idle)"; idle="${idle:-0}"
  if awk "BEGIN{exit !(${idle}+0 >= ${THRESH})}"; then ok=$((ok+1)); else ok=0; fi
  echo "  idle=${idle}%  streak=${ok}/${NEED}  (waited ${elapsed}s)"
  [ "$ok" -ge "$NEED" ] && break
  sleep "$POLL"; elapsed=$((elapsed+POLL))
  [ "$elapsed" -ge "$MAXWAIT" ] && { echo "gave up waiting for idle after ${elapsed}s" >&2; exit 3; }
done

echo "system idle; running: $*"
exec "$@"
