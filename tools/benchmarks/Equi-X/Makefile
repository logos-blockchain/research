# Equi-X benchmark — make wrapper around the scripts/ + harness entry points.
#
#   make setup            bootstrap deps, build both runners, autotune C flags
#   make check            report which dependencies are present (installs nothing)
#   make test             run the harness unit tests (skips cleanly if pytest missing)
#   make benchmark        main C-vs-Rust benchmark, quick profile   (depends: setup test)
#   make benchmark-full   deep sweep incl. concurrency + mining     (depends: setup test)
#   make compiler-flags   build the gcc/clang -O matrix and compare (depends: setup)
#   make mining           standalone mining sweep, idle-gated       (depends: setup)
#   make control          difficulty-controller simulation demo
#   make combine          merge per-device runs under ROOT into one faceted report
#   make everything       full pipeline via scripts/run_all.sh --full
#   make clean            remove C build trees + generated variant manifests
#   make distclean        clean + Rust target/ + results/
#
# Variables:  OUT=results   make benchmark OUT=/tmp/out
#             ROOT=results-by-device  make combine   (tree of per-device runs)
#             EQUIX_NO_AUTOTUNE=1 make setup     (skip flag autotuning)

SHELL   := /usr/bin/env bash
OUT     ?= results
ROOT    ?= $(OUT)
# Prefer the project venv scripts/setup.sh creates (harness + pytest installed,
# PEP-668-proof); fall back to system python3 when it is absent.
PY      := $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
export PYTHONPATH := $(CURDIR)/harness$(if $(PYTHONPATH),:$(PYTHONPATH),)

.PHONY: all help setup check test benchmark benchmark-full compiler-flags \
        mining control combine everything clean distclean

all: benchmark

help:
	@sed -n '2,17p' Makefile | sed 's/^# \{0,1\}//'

setup:
	./scripts/setup.sh

check:
	./scripts/setup.sh --check

# Tests are a soft dependency: run when pytest is available, skip loudly (but
# without failing the chain) when it is not — mirroring scripts/run_all.sh.
test: setup
	@if $(PY) -c 'import pytest' >/dev/null 2>&1; then \
	  $(PY) -m pytest -q harness/tests; \
	else \
	  echo "WARNING: pytest not importable; skipping unit tests." >&2; \
	  echo "  fix: re-run ./scripts/setup.sh (creates .venv with pytest)," >&2; \
	  echo "       or: python3 -m pip install pytest (or --break-system-packages)" >&2; \
	fi

benchmark: setup test
	$(PY) -m equix_bench run --config configs/smoke.toml --out $(OUT)/main

benchmark-full: setup test
	$(PY) -m equix_bench run --config configs/full.toml --out $(OUT)/main

compiler-flags: setup
	./scripts/build_variants.sh
	$(PY) -m equix_bench run --config configs/compiler_flags.toml --out $(OUT)/compiler_flags

mining: setup
	./scripts/run_when_idle.sh $(PY) -m equix_bench run --config configs/mining.toml --out $(OUT)/mining

control:
	$(PY) -m equix_bench.difficulty_control --out $(OUT)/control

# Merge every run found under ROOT (each device's results, in any layout) into
# one faceted, per-device report. ROOT defaults to OUT; OUT names the report dir.
combine:
	$(PY) -m equix_bench combine --root $(ROOT) --out $(OUT)/combined
	@echo "combined report -> $(OUT)/combined/report.md"

everything:
	./scripts/run_all.sh --full --out $(OUT)

clean:
	rm -rf build/runners/c build/autotune build/variants adapters/generated
	@echo "cleaned C build trees + generated manifests (Rust target/ and $(OUT)/ kept; use distclean)"

distclean: clean
	rm -rf runners/rust/target $(OUT) combined build
