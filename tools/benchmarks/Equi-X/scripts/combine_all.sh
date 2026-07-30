#!/usr/bin/env bash
# Combine benchmark results collected from MULTIPLE devices into ONE report with
# figures drawn from all of them. Point it at a tree that holds every device's
# run outputs (each device's `results/` copied/rsync'd under it, in any layout):
#
#   results-by-device/
#     laptop-x1/main/{raw/results.json, concurrency.csv, mining.csv, ...}
#     server-epyc/main/{raw/results.json, ...}
#     rpi5/results/main/{raw/results.json, ...}
#
# Discovery is layout-agnostic: any directory containing raw/results.json is a
# run, and each run's DEVICE identity comes from inside its records (CPU model +
# OS), so folder names are free-form and two devices never get conflated. Re-runs
# of the same device are de-duplicated (newest wins). Every core plot is faceted
# per device; cross-device `xdev_*` charts compare CPUs directly; the concurrency
# and mining sections/figures are carried across all devices too.
#
# Usage:
#   ./scripts/combine_all.sh [ROOT] [--out DIR]
#     ROOT      tree to scan for runs        (default: results-by-device, else results)
#     --out DIR combined report directory    (default: <ROOT>/combined or results/combined)
set -uo pipefail

ROOT_ARG=""
OUT=""
while [ $# -gt 0 ]; do
  case "$1" in
    --out) [ $# -ge 2 ] || { echo "error: --out needs a directory" >&2; exit 2; }; OUT="$2"; shift ;;
    --out=*) OUT="${1#*=}" ;;
    -h|--help) sed -n '2,25p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) echo "unknown option: $1" >&2; exit 2 ;;
    *) ROOT_ARG="$1" ;;
  esac
  shift
done

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"

# Default ROOT: a dedicated per-device collection dir if present, else results/.
ROOT="$ROOT_ARG"
if [ -z "$ROOT" ]; then
  if [ -d results-by-device ]; then ROOT="results-by-device"; else ROOT="results"; fi
fi
[ -d "$ROOT" ] || { echo "error: ROOT '$ROOT' is not a directory" >&2; exit 2; }
[ -n "$OUT" ] || OUT="$ROOT/combined"

# Prefer the venv from setup.sh (harness installed, PEP-668-proof).
PY="python3"
[ -x "$REPO/.venv/bin/python" ] && PY="$REPO/.venv/bin/python"
export PYTHONPATH="$REPO/harness${PYTHONPATH:+:$PYTHONPATH}"

echo "==> Combining all runs under '$ROOT' -> '$OUT'"
$PY -m equix_bench combine --root "$ROOT" --out "$OUT" || {
  echo "error: combine failed" >&2; exit 1;
}
echo "    report:  $OUT/report.md"
echo "    figures: $OUT/plots/*.png   data: $OUT/results.csv"
