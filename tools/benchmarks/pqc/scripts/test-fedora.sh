#!/usr/bin/env bash
# =============================================================================
# make test-fedora — run check/build/test (and with SMOKE=1 a smoke run)
# inside a Fedora container, from a pristine copy of the CURRENT working tree.
#
# WHAT THIS COVERS: the class of bug that Mac + Pi testing structurally cannot
# catch — Red Hat packaging (openssl-devel), the lib64 install layout, dnf
# paths, and degradation on a machine with no governor control, no vcgencmd
# and no Pi-shaped thermal telemetry (the container has none of these, which
# is exactly the machine shape that has broken in the field).
#
# WHAT THIS DOES NOT COVER: measurements. Timings inside a container/VM are
# meaningless and nothing produced here is a benchmark result; runs are NOSUDO
# and land in the container's own copy of the results tree, never in this
# checkout (both host mounts are read-only). On Apple
# Silicon the container is aarch64 Fedora (lib64 reproduces natively);
# ARCH=amd64 forces x86_64 under emulation for compile-and-run checks.
#
# Engine: podman or docker, autodetected. Image: fedora:42.
# =============================================================================
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ENGINE=""
for e in podman docker; do
  command -v "$e" >/dev/null 2>&1 && "$e" info >/dev/null 2>&1 && { ENGINE="$e"; break; }
done
[ -n "$ENGINE" ] || { echo "no working container engine (podman or docker) — install one, e.g. 'brew install podman && podman machine init --now'" >&2; exit 1; }

PLATFORM_ARG=""
[ "${ARCH:-}" = "amd64" ] && PLATFORM_ARG="--platform=linux/amd64"

SMOKE_CMD=""
if [ "${SMOKE:-0}" = "1" ]; then
  SMOKE_CMD='echo "===== make smoke (NOSUDO, container) =====" && NOSUDO=1 make smoke'
fi

# The results tree lives outside the tool (reports/pqc/results), so it is
# mounted separately: the hygiene checks read the published set and the v1
# compatibility fixture from it. Both mounts are read-only and the container
# copies both, so nothing it runs can write into this checkout.
# shellcheck source=setup/lib_platform.sh
source "$HERE/setup/lib_platform.sh"
RESULTS_HOST="$(pqb_results_dir "$HERE")"
[ -d "$RESULTS_HOST" ] || { echo "results tree not found at $RESULTS_HOST — set PQC_RESULTS_DIR" >&2; exit 1; }
RESULTS_HOST="$(cd "$RESULTS_HOST" && pwd)"

echo "[test-fedora] engine=$ENGINE image=fedora:42 ${ARCH:+arch=$ARCH }(source + results trees mounted read-only)"
# shellcheck disable=SC2086
"$ENGINE" run --rm $PLATFORM_ARG -v "$HERE":/src:ro -v "$RESULTS_HOST":/src-results:ro fedora:42 bash -c '
  set -euo pipefail
  echo "== $(grep PRETTY /etc/os-release | cut -d= -f2 | tr -d \") $(uname -m) =="
  dnf install -y -q gcc gcc-c++ make cmake ninja-build git python3 perl \
      openssl openssl-devel pkgconf-pkg-config util-linux rsync
  # pristine copy: never build into the mounted host tree
  rsync -a --exclude vendor/ --exclude "bench/rust/target/" \
        --exclude "bench/rust-tls/target/" --exclude ".work-*" \
        --exclude "setup/versions.lock" \
        --exclude "bench/kem_sig/bench_pq" --exclude "bench/tls/bench_tls" \
        --exclude "bench/tls/pki/" --exclude "*.o" \
        /src/ /work/
  rsync -a --exclude ".work-*" /src-results/ /work-results/
  export PQC_RESULTS_DIR=/work-results
  cd /work
  make check
  make build
  make test
  '"$SMOKE_CMD"'
  echo "[test-fedora] ALL GREEN"
'
