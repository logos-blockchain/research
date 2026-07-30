#!/usr/bin/env bash
# Bootstrap the Equi-X benchmark: install/compile any missing dependencies, fetch
# the vendored reference implementation, and build both runners. Idempotent.
#
#   ./scripts/setup.sh          # install missing deps (best effort) + build
#   ./scripts/setup.sh --check  # only report what's present/missing, install nothing
#   EQUIX_NO_AUTO_INSTALL=1 ./scripts/setup.sh   # never auto-install; fail with guidance
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

CHECK_ONLY=0
[ "${1:-}" = "--check" ] && CHECK_ONLY=1
: "${EQUIX_NO_AUTO_INSTALL:=0}"

NPROC="$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)"
have() { command -v "$1" >/dev/null 2>&1; }

# clean_stale_cmake_dir <build-dir>: CMake caches record ABSOLUTE paths, so a
# repo that was copied/moved (e.g. rsync'd to another machine) fails to
# configure with "CMakeCache.txt directory ... is different". Detect a cache
# created at a different path and remove the build dir so cmake starts fresh.
clean_stale_cmake_dir() {
  local dir="$1" cache="$1/CMakeCache.txt" recorded
  [ -f "$cache" ] || return 0
  recorded="$(sed -n 's/^CMAKE_CACHEFILE_DIR:INTERNAL=//p' "$cache" | head -1)"
  if [ -n "$recorded" ] && [ "$recorded" != "$(cd "$dir" && pwd)" ]; then
    echo "    (stale CMake cache from '$recorded'; cleaning $dir)"
    rm -rf "$dir"
  fi
}

# Minimum Rust toolchain the runner's dependency tree needs to compile.
RUST_MIN="1.91.0"

# rust_version_ok <have> <min> -> 0 if have >= min (compares major.minor.patch).
# Pre-release suffixes ("1.91.0-nightly", "1.91.1-beta.2") are stripped first;
# without that, a non-numeric patch component errors the [ -ge ] comparison.
rust_version_ok() {
  local have="${1%%-*}" min="${2%%-*}" IFS=.
  # shellcheck disable=SC2086
  set -- $have; local h_maj=${1:-0} h_min=${2:-0} h_pat=${3:-0}
  # shellcheck disable=SC2086
  set -- $min;  local m_maj=${1:-0} m_min=${2:-0} m_pat=${3:-0}
  [ "$h_maj" -ne "$m_maj" ] && { [ "$h_maj" -gt "$m_maj" ]; return; }
  [ "$h_min" -ne "$m_min" ] && { [ "$h_min" -gt "$m_min" ]; return; }
  [ "$h_pat" -ge "$m_pat" ]
}

# --- dependency provisioning -------------------------------------------------

SUDO=""
if [ "$(id -u)" -ne 0 ] && have sudo; then SUDO="sudo"; fi

PM=""
for pm in apt-get dnf yum pacman zypper brew; do
  if have "$pm"; then PM="$pm"; break; fi
done

pm_install() { # pm_install <pkg...>
  case "$PM" in
    apt-get) $SUDO apt-get update -qq && $SUDO apt-get install -y "$@" ;;
    dnf|yum) $SUDO "$PM" install -y "$@" ;;
    pacman)  $SUDO pacman -Sy --noconfirm "$@" ;;
    zypper)  $SUDO zypper install -y "$@" ;;
    brew)    brew install "$@" ;;
    *) return 1 ;;
  esac
}

# pkg name for the current package manager: ensure <cmd> <apt> <dnf> <pacman> <brew>
ensure() {
  local cmd="$1" apt="$2" dnf="$3" pac="$4" brew="$5" pkg=""
  if have "$cmd"; then echo "    ok: $cmd"; return 0; fi
  echo "    MISSING: $cmd"
  [ "$CHECK_ONLY" = 1 ] && { MISSING=1; return 0; }
  if [ "$EQUIX_NO_AUTO_INSTALL" = 1 ] || [ -z "$PM" ]; then
    echo "    -> please install '$cmd' (no package manager auto-install available)"
    MISSING=1; return 0
  fi
  case "$PM" in
    apt-get) pkg="$apt" ;; dnf|yum) pkg="$dnf" ;; pacman) pkg="$pac" ;;
    zypper) pkg="$dnf" ;; brew) pkg="$brew" ;;
  esac
  # An empty package name means "not installable via this PM" (e.g. cc/pip3 on
  # macOS come from the Xcode CLT / python): don't run a bare `$PM install`.
  if [ -z "$pkg" ]; then
    case "$cmd" in
      cc)  echo "    -> please install the Xcode Command Line Tools: xcode-select --install" ;;
      *)   echo "    -> please install '$cmd' manually (not packaged for $PM here)" ;;
    esac
    MISSING=1; return 0
  fi
  echo "    -> installing $pkg via $PM"
  if pm_install $pkg; then echo "    installed: $cmd"; else echo "    FAILED to install $cmd"; MISSING=1; fi
}

MISSING=0
echo "==> [1/6] Checking dependencies (package manager: ${PM:-none})"
ensure git    git          git           git       git
ensure cmake  cmake        cmake         cmake     cmake
ensure cc     build-essential 'gcc gcc-c++ make' base-devel ""   # clang ships with Xcode CLT on macOS
ensure python3 python3      python3       python    python
ensure pip3   python3-pip  python3-pip   python-pip ""

# Rust toolchain via rustup when missing, and kept at >= RUST_MIN.
# (A distro/rustup rustc that is too old — e.g. 1.87 vs the 1.91 the deps need —
#  fails the build just like a missing one, so treat both the same way.)
# NB: must return 0 when the file is absent — a bare `[ -f ] && .` one-liner
# returns 1 there, and under `set -e` a plain call would silently kill setup.
maybe_source_cargo_env() {
  # shellcheck disable=SC1091
  if [ -f "$HOME/.cargo/env" ]; then . "$HOME/.cargo/env"; fi
}

if have cargo; then
  RUSTC_VER="$(rustc --version 2>/dev/null | awk '{print $2}')"
  if rust_version_ok "${RUSTC_VER:-0.0.0}" "$RUST_MIN"; then
    echo "    ok: cargo (rustc ${RUSTC_VER})"
  elif [ "$CHECK_ONLY" = 1 ]; then
    echo "    OUTDATED: rustc ${RUSTC_VER:-unknown} < ${RUST_MIN}"; MISSING=1
  elif [ "$EQUIX_NO_AUTO_INSTALL" = 1 ]; then
    echo "    -> rustc ${RUSTC_VER:-unknown} < ${RUST_MIN}; please update Rust (https://rustup.rs)"; MISSING=1
  elif have rustup; then
    echo "    -> rustc ${RUSTC_VER:-unknown} < ${RUST_MIN}; updating via 'rustup update stable'"
    if rustup update stable && rustup default stable; then
      maybe_source_cargo_env
      RUSTC_VER="$(rustc --version 2>/dev/null | awk '{print $2}')"
      rust_version_ok "${RUSTC_VER:-0.0.0}" "$RUST_MIN" \
        || { echo "    FAILED: rustc still ${RUSTC_VER:-unknown} < ${RUST_MIN} after update"; MISSING=1; }
    else
      echo "    FAILED to update Rust via rustup"; MISSING=1
    fi
  else
    # cargo present but not managed by rustup (e.g. a distro package): install
    # rustup so we can get a current toolchain, then re-check.
    echo "    -> rustc ${RUSTC_VER:-unknown} < ${RUST_MIN} and no rustup; installing rustup"
    if have curl && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable; then
      maybe_source_cargo_env
      RUSTC_VER="$(rustc --version 2>/dev/null | awk '{print $2}')"
      rust_version_ok "${RUSTC_VER:-0.0.0}" "$RUST_MIN" \
        || { echo "    FAILED: rustc still ${RUSTC_VER:-unknown} < ${RUST_MIN}; ensure ~/.cargo/bin precedes the system rustc on PATH"; MISSING=1; }
    else
      echo "    FAILED to install rustup (need curl + network)"; MISSING=1
    fi
  fi
elif [ "$CHECK_ONLY" = 1 ]; then
  echo "    MISSING: cargo"; MISSING=1
elif [ "$EQUIX_NO_AUTO_INSTALL" = 1 ]; then
  echo "    -> please install Rust (https://rustup.rs)"; MISSING=1
else
  echo "    -> installing Rust via rustup"
  if have curl && curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable; then
    maybe_source_cargo_env
  else
    echo "    FAILED to install cargo (need curl + network)"; MISSING=1
  fi
fi

if [ "$CHECK_ONLY" = 1 ]; then
  [ "$MISSING" = 0 ] && echo "==> All dependencies present." || echo "==> Some dependencies missing (see above)."
  exit "$MISSING"
fi
[ "$MISSING" = 0 ] || { echo "ERROR: missing dependencies above; install them and re-run."; exit 1; }

# --- build -------------------------------------------------------------------

echo "==> [2/6] Initializing vendored submodules (equix + hashx)"
git submodule update --init --recursive

EQUIX_COMMIT="$(git -C vendored/equix rev-parse --short HEAD)"
HASHX_COMMIT="$(git -C vendored/equix/hashx rev-parse --short HEAD 2>/dev/null || echo unknown)"
echo "    equix @ ${EQUIX_COMMIT}, hashx @ ${HASHX_COMMIT}"

echo "==> [3/6] Building the C runner (compiles libequix + libhashx)"
# Baseline build with explicit, known-fast flags -- `-O3 -DNDEBUG` (no -O0/-O1,
# no -march=native). This guarantees a working runner and is the fallback if
# autotune is disabled or fails.
MAIN_C_FLAGS="-O3 -DNDEBUG"
# A copied/moved repo carries CMake caches with the old absolute paths — clean
# them or cmake refuses to configure.
clean_stale_cmake_dir build/runners/c
for d in build/autotune/* build/variants/*; do
  if [ -d "$d" ]; then clean_stale_cmake_dir "$d"; fi
done
# If a previous autotune installed a winner built with DIFFERENT flags, the
# incremental build below would be a no-op (the copied binary is newer than the
# sources) and rewriting the .flags file would misdescribe the binary. Force a
# clean rebuild in that case so binary and provenance always agree.
CLEAN_ARG=""
if [ -f build/runners/c/equix_runner.flags ] \
   && [ "$(cat build/runners/c/equix_runner.flags)" != "${MAIN_C_FLAGS}" ]; then
  CLEAN_ARG="--clean-first"
fi
cmake -S runners/c -B build/runners/c \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_C_FLAGS_RELEASE="${MAIN_C_FLAGS}" \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.10 \
  -DEQUIX_C_COMMIT="${EQUIX_COMMIT}" \
  -DEQUIX_C_VERSION="1.0.0" >/dev/null
cmake --build build/runners/c -j"$NPROC" --target equix_runner ${CLEAN_ARG}
printf '%s' "${MAIN_C_FLAGS}" > build/runners/c/equix_runner.flags
echo "    -> build/runners/c/equix_runner  (baseline flags: ${MAIN_C_FLAGS})"

# Then pick the fastest optimization flags on THIS machine and install the winner
# as the main runner, so the benchmark runs the fastest build the host can make
# (solve is JIT-dominated, so the win is usually small, but it is now measured,
# not assumed). Set EQUIX_NO_AUTOTUNE=1 to skip (keeps the baseline above).
if [ "${EQUIX_NO_AUTOTUNE:-0}" = 1 ]; then
  echo "    (autotune disabled via EQUIX_NO_AUTOTUNE; using ${MAIN_C_FLAGS})"
else
  echo "==> [3b/6] Auto-selecting the fastest C flags for the main runner"
  ./scripts/autotune_c_flags.sh || echo "    (autotune failed; keeping the ${MAIN_C_FLAGS} baseline)"
fi

echo "==> [4/6] Building the Rust runner (pinned via Cargo.lock)"
cargo build --locked --release --manifest-path runners/rust/Cargo.toml
echo "    -> runners/rust/target/release/equix_runner"

echo "==> [5/6] Installing the Python harness into a project venv (.venv)"
# A project virtualenv is the robust fix for the Linux failure "pytest not
# importable / externally-managed-environment": PEP-668 interpreters (Debian,
# Homebrew) reject a plain `pip install` into the system site-packages, but a
# venv has its own writable site-packages, so pip (matplotlib/numpy/pytest) just
# works and stays isolated from the system Python. It is stdlib-only — no pyenv
# or extra tooling required. run_all.sh and the Makefile auto-prefer .venv/bin.
VENV_DIR=".venv"
if [ ! -x "$VENV_DIR/bin/python" ]; then
  if ! python3 -m venv "$VENV_DIR" >/dev/null 2>&1; then
    # Debian/Ubuntu split venv into the python3-venv package; provision and retry.
    if [ "$PM" = apt-get ] && [ "$EQUIX_NO_AUTO_INSTALL" != 1 ]; then
      echo "    (python3 -m venv unavailable; installing python3-venv)"
      pm_install python3-venv >/dev/null 2>&1 || true
      python3 -m venv "$VENV_DIR" >/dev/null 2>&1 || true
    fi
  fi
fi
if [ -x "$VENV_DIR/bin/python" ]; then
  VENV_PY="$VENV_DIR/bin/python"
  "$VENV_PY" -m pip install -q --upgrade pip >/dev/null 2>&1 || true
  if "$VENV_PY" -m pip install -q -e ./harness pytest; then
    echo "    -> equix_bench + pytest installed into $VENV_DIR"
    echo "       (run via: $VENV_DIR/bin/python -m equix_bench ...; run_all.sh / make use it automatically)"
  else
    echo "    (pip install into $VENV_DIR failed; see errors above)"
  fi
else
  # No venv possible (e.g. locked-down host): fall back through system pip modes.
  echo "    (could not create $VENV_DIR; falling back to system pip)"
  if python3 -m pip install -e ./harness >/dev/null 2>&1 \
     || python3 -m pip install --user -e ./harness >/dev/null 2>&1 \
     || python3 -m pip install --break-system-packages -e ./harness >/dev/null 2>&1; then
    echo "    -> equix_bench installed (system interpreter)"
  else
    echo "    (could not pip install automatically; run: python3 -m pip install -e ./harness)"
  fi
fi

echo "==> [6/6] Writing provenance"
mkdir -p build
cat > build/provenance.json <<EOF
{
  "equix_commit": "${EQUIX_COMMIT}",
  "hashx_commit": "${HASHX_COMMIT}",
  "rust_equix": "0.7.0",
  "rust_hashx": "0.9.0",
  "cc": "$( (cc --version 2>/dev/null || echo n/a) | head -1)",
  "cc_flags": "$(cat build/runners/c/equix_runner.flags 2>/dev/null || echo n/a)",
  "rustc": "$(rustc --version 2>/dev/null | awk '{print $2}' || echo n/a)"
}
EOF
cat build/provenance.json

echo "==> Done. Try:"
PY_HINT="python3"; [ -x "$VENV_DIR/bin/python" ] && PY_HINT="$VENV_DIR/bin/python"
echo "    $PY_HINT -m equix_bench run --config configs/smoke.toml --out results/"
