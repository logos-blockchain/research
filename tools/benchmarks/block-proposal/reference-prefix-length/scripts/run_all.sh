#!/usr/bin/env bash
# Run the whole reference-prefix measurement suite and drop every result under
# results/<machine>/.
#
#   ./scripts/run_all.sh mac
#   ./scripts/run_all.sh rpi5
#
# The machine name is only a label for the output directory and the CSV rows;
# the code executed is identical on every machine.

set -euo pipefail

MACHINE="${1:-}"
if [[ -z "$MACHINE" ]]; then
  echo "usage: $0 <machine-label>   (e.g. mac, rpi5)" >&2
  exit 1
fi

cd "$(dirname "$0")/.."
OUT="results/${MACHINE}"
mkdir -p "$OUT"

echo "==> toolchain"
rustc --version | tee "$OUT/toolchain.txt"
cargo --version | tee -a "$OUT/toolchain.txt"

echo
echo "==> machine"
{
  echo "label: ${MACHINE}"
  echo "date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "uname: $(uname -a)"
  if [[ -r /proc/cpuinfo ]]; then
    echo "cpu: $(grep -m1 -E 'model name|Model' /proc/cpuinfo | cut -d: -f2- | sed 's/^ *//')"
    echo "cores: $(nproc)"
    if [[ -r /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor ]]; then
      echo "governor: $(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)"
    fi
  elif command -v sysctl >/dev/null; then
    echo "cpu: $(sysctl -n machdep.cpu.brand_string)"
    echo "cores: $(sysctl -n hw.ncpu)"
  fi
} | tee "$OUT/machine.txt"

echo
echo "==> harness self-check (the shortcut must agree with the real hash path)"
cargo test --release --quiet

echo
echo "==> 1/4  R_gen, single core (criterion)"
cargo bench --bench candidate_generation 2>&1 | tee "$OUT/candidate_generation.txt"

echo
echo "==> 2/4  aggregate generation throughput vs. thread count"
cargo run --release --quiet --bin throughput -- \
  --machine "$MACHINE" --seconds 5 --out "$OUT/throughput.csv"

echo
echo "==> 3/4  birthday model validation on real mantle_txhash output"
cargo run --release --quiet --bin birthday -- \
  --machine "$MACHINE" --trials 24 --out "$OUT/birthday.csv"

echo
echo "==> 4/4  reconstruction latency vs. collision multiplicity"
# k-max 15 is 32768 combinations; on a slow machine the budget stops it sooner.
cargo run --release --quiet --bin reconstruction -- \
  --machine "$MACHINE" --block-sizes 1024,128 --k-max 15 --repeats 5 \
  --budget-secs 60 --out "$OUT/reconstruction.csv"

echo
echo "==> done. results in $OUT/"
ls -la "$OUT"
