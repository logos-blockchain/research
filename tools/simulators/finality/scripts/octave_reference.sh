#!/bin/sh
# Runs the original LCanalysis code (github.com/renling/LCanalysis @ 35cfc83) in Octave at the
# points tests/test_lcbounds.py compares the port with. Each point is a background process that
# appends its values to runs/octave/<point>.csv as they are computed; the slowest takes about ten
# hours. octave/ holds the two pdf functions Octave lacks and the drivers.
set -e
HERE=$(cd "$(dirname "$0")/.." && pwd)
OUT=$HERE/runs/octave
LC=$OUT/LCanalysis
mkdir -p "$OUT"
[ -d "$LC" ] || git clone -q https://github.com/renling/LCanalysis "$LC"
git -C "$LC" checkout -q 35cfc839628899752098fdba761f9122214b6140
# The lower bound with its phase count as an argument; nothing else changes.
sed -e 's/^function Error = PoSMCConfirmLB(K,/function Error = PoSMCConfirmLBSteps(SimulateSteps, K,/' \
    -e 's/^SimulateSteps = 80;$/% SimulateSteps is an argument here/' \
    "$LC/PoSMCConfirmLB.m" > "$OUT/PoSMCConfirmLBSteps.m"
grep -q 'PoSMCConfirmLBSteps(SimulateSteps, K,' "$OUT/PoSMCConfirmLBSteps.m"
grep -q 'SimulateSteps is an argument here' "$OUT/PoSMCConfirmLBSteps.m"

run() {
  name=$1; shift
  rm -f "$OUT/$name.csv"
  nohup octave-cli --no-gui --eval "addpath('$HERE/octave'); addpath('$LC'); addpath('$OUT'); $*" \
    > "$OUT/$name.log" 2>&1 &
}
# Table 1's 20 % column at 2 s (D = 0.1), the code's default alphabet and states.
run table1 "lc_points(0.8, 0.1, 10, 19, [4 8 12 16 20], '$OUT/table1.csv')"
# A quarter of the stake at 10 s and f = 1/30 (D = 1/3).
run quarter "lc_points(0.75, 1/3, 16, 19, [5 10 20], '$OUT/quarter.csv')"
# A third of the stake at 1 s (D = 1/30), depth 60: the original 80 phases, and 240.
run third80 "lc_points(2/3, 1/30, 10, 19, 60, '$OUT/third80.csv')"
run third240 "lc_lower(2/3, 1/30, 10, 19, 60, 240, '$OUT/third240.csv')"
