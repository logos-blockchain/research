# =============================================================================
# pqc — post-quantum cryptography benchmark. Executable documentation:
# `make help` lists everything, and these targets are the ONLY supported way to
# check, build, test and run it on any supported platform.
#
# Design rules (docs/history behind them: the cold-read round):
#   * `check` is READ-ONLY; `deps` is the only target that installs anything.
#   * No stamp files — skip decisions use live probes and real artifacts
#     (an upgraded OpenSSL or deleted toolchain always triggers a rebuild).
#   * `smoke`/`run` depend on `build` only: `test`'s hygiene checks must never
#     block a 30-minute measurement. Run `make test` before trusting results.
#   * All test artifacts live in /tmp — never in the results tree or
#     bench/tls/pki/.
#   * Results are NOT kept next to the tool: every run writes its JSON to
#     $(RESULTS) and figures to $(FIGURES), so measurements live with the rest
#     of the reports. PQC_RESULTS_DIR / PQC_FIGURES_DIR override both.
# =============================================================================
SHELL := /bin/bash
.DEFAULT_GOAL := help

RESULTS ?= $(abspath $(dir $(lastword $(MAKEFILE_LIST)))../../../reports/pqc/results)
FIGURES ?= $(abspath $(dir $(lastword $(MAKEFILE_LIST)))../../../reports/pqc/figures)
# Exported so run.sh, the selftest and the container gate all resolve the same
# directories — `make RESULTS=/somewhere run` redirects every target at once.
export PQC_RESULTS_DIR := $(RESULTS)
export PQC_FIGURES_DIR := $(FIGURES)

.PHONY: help check deps build test test-fedora smoke run merge figures dashboard where clean distclean

help: ## list targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

where: ## print where this tool reads and writes results and figures
	@echo "results: $(RESULTS)"
	@echo "figures: $(FIGURES)"

check: ## verify the environment (read-only; prints per-platform install hints)
	@scripts/check-env.sh

deps: ## OPT-IN: install missing system deps (brew/apt/dnf); add RUST=1 for rustup
	@scripts/install-deps.sh

build: check ## C toolchain (liboqs/OpenSSL/oqs-provider) + bench binaries + Rust harnesses
	@scripts/build-toolchain.sh

test: build ## fast verification gate (~1-2 min): correctness blocks, hygiene warns
	@scripts/selftest.sh

test-fedora: ## check/build/test in a Fedora container (Red Hat paths/packages/degradation; SMOKE=1 adds a smoke run; not a benchmark)
	@scripts/test-fedora.sh

smoke: build ## all-four-groups smoke benchmark (1 rep, 50 handshakes/cell)
	@scripts/bench-run.sh --smoke

run: build ## full benchmark run (~30 min Pi / ~36 min M3); sudo handled per-platform
	@scripts/bench-run.sh

merge: ## regenerate dashboard/data/merged.json from the published_runs manifest
	python3 analyze/merge.py

figures: ## export PNG figures from the merged dataset into reports/pqc/figures
	python3 analyze/plot.py dashboard/data/merged.json

dashboard: ## serve the dashboard over HTTP (does NOT touch merged.json; see 'merge')
	@echo "serving http://localhost:8000 (Ctrl-C to stop)"
	@cd dashboard && python3 -m http.server 8000

clean: ## remove bench binaries and Rust target trees
	$(MAKE) -C bench/kem_sig clean
	$(MAKE) -C bench/tls clean
	rm -rf bench/rust/target bench/rust-tls/target

distclean: clean ## additionally remove the vendored C toolchain (forces full rebuild)
	rm -rf vendor setup/versions.lock
