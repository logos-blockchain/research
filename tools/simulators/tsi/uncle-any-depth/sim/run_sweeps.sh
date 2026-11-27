#!/bin/sh
# Reruns the simulator sweeps of this study: sh run_sweeps.sh [label ...] (all labels without arguments).
# Builds a copy of ../../tsi-sim-pernode with id-only.diff applied in work/, runs each sweep there and copies its
# results to results/<label>.parquet. PY selects the interpreter; the default is the simulator's own environment.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
SIM="$HERE/../../tsi-sim-pernode"
PY="${PY:-$SIM/.venv/bin/python}"
WORK="$HERE/work"

rm -rf "$WORK"
mkdir -p "$WORK" "$HERE/results"
cp -R "$SIM/src" "$SIM/scripts" "$WORK/"
patch -s -p1 -d "$WORK" < "$HERE/id-only.diff"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH="$WORK/src"

# The rules of id-only.diff, chosen by environment variable:
#   IDONLY_WAIT=1       a block waits until the node holds every block its entries name (with their branches)
#   IDONLY_BROADCAST=1  a proposer names a fork block only if every block of its branch reached it by broadcast;
#                       its own blocks count once their broadcast came back to it
#   IDONLY_TM=<s>       and only <s> seconds after it received each of them
DRAFTED="IDONLY_WAIT=1 IDONLY_BROADCAST=1 IDONLY_TM=15"

run() {
    label=$1; config=$2; shift 2
    echo "$(date '+%H:%M:%S') $label"
    (cd "$WORK" && env "$@" "$PY" scripts/run_sweep.py --config "$HERE/configs/$config" --label "$label" --no-figures \
        > "$WORK/$label.log" 2>&1)
    cp "$(ls -d "$WORK"/runs/*_"$label" | tail -1)/results.parquet" "$HERE/results/$label.parquet"
}

sweep() {
    case $1 in
        healthy-w12)                 run "$1" healthy-w12.yaml $DRAFTED ;;
        healthy-w12-tm0)             run "$1" healthy-w12.yaml IDONLY_WAIT=1 IDONLY_BROADCAST=1 ;;
        healthy-w12-depth)           run "$1" healthy-w12-depth.yaml IDONLY_WAIT=1 ;;
        healthy-w12-depth-truncated) run "$1" healthy-w12-depth-truncated.yaml ;;
        healthy-w240)                run "$1" healthy-w240.yaml $DRAFTED ;;
        coalition-fork-point)        run "$1" coalition-fork-point.yaml $DRAFTED ;;
        coalition-own-slot)          run "$1" coalition-own-slot.yaml $DRAFTED ;;
        coalition-today)             run "$1" coalition-today.yaml ;;
        coalition-w240)              run "$1" coalition-w240.yaml $DRAFTED ;;
        *) echo "unknown label $1" >&2; exit 1 ;;
    esac
}

if [ $# -eq 0 ]; then
    set -- healthy-w12 healthy-w12-tm0 healthy-w12-depth healthy-w12-depth-truncated healthy-w240 \
        coalition-fork-point coalition-own-slot coalition-today coalition-w240
fi
for label in "$@"; do sweep "$label"; done
echo "$(date '+%H:%M:%S') done"
