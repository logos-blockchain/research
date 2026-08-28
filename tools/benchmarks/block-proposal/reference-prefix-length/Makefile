# =============================================================================
# reference-prefix-length — measurements behind REFERENCE_PREFIX_LENGTH for the
# compressed block proposal (logos-lips#389). Executable documentation:
# `make help` lists everything, and these targets are the supported way to
# check, build, test and run the suite on any machine.
#
# Design rules:
#   * `check` is READ-ONLY. It reports what is missing and how to install it;
#     it never installs anything itself.
#   * Every measuring target depends on `build`, not on `test`, so a failing
#     hygiene check can never block a long run. Run `make test` before
#     trusting numbers — it is the gate that proves the harness still agrees
#     with the real logos-blockchain code path.
#   * MACHINE labels the run and nothing else. The code executed is identical
#     everywhere; the label only selects the results directory, so a Mac run
#     and an RPi5 run stay separable and comparable.
#   * Results are committed. `run` overwrites results/$(MACHINE)/ in place, so
#     a re-run is a deliberate act with a visible diff, not a silent drift.
#   * The toolchain is pinned in rust-toolchain.toml and the dependency is
#     pinned by commit in Cargo.toml. Neither is overridable here — that is
#     what makes two machines comparable.
# =============================================================================
SHELL := /bin/bash
.DEFAULT_GOAL := help

# Label for this run: selects results/$(MACHINE)/. Defaults to the platform,
# so `make run` on the Pi lands in results/rpi5/ without being told.
MACHINE ?= $(shell if [ "$$(uname -s)" = "Darwin" ]; then echo mac; \
                   elif grep -qi raspberry /proc/cpuinfo 2>/dev/null; then echo rpi5; \
                   else echo "$$(uname -m)-$$(uname -s | tr A-Z a-z)"; fi)

RESULTS := results/$(MACHINE)
REPORT  := ../../../../reports/block-proposal

# Python for the analysis step. PEP-668 systems refuse a global install, so
# `make venv` builds one here and every python target prefers it when present.
VENV   := .venv
PYTHON := $(shell if [ -x "$(VENV)/bin/python" ]; then echo "$(VENV)/bin/python"; else echo python3; fi)

.PHONY: help where check build test bench run analyse venv figures clean distclean

help: ## list targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'
	@echo
	@echo "  MACHINE=$(MACHINE) (override to label a run: make run MACHINE=rpi5)"

where: ## print what this tool reads and writes
	@echo "  results   $(abspath $(RESULTS))"
	@echo "  report    $(abspath $(REPORT))"
	@echo "  machine   $(MACHINE)"
	@echo "  toolchain $$(grep -o '"[0-9.]*"' rust-toolchain.toml | tr -d '"') (pinned)"

check: ## verify the environment (read-only; prints install hints)
	@fail=0; \
	if command -v cargo >/dev/null; then \
	  echo "  ok    cargo    $$(cargo --version)"; \
	else \
	  echo "  MISS  cargo    install rustup: https://rustup.rs"; fail=1; \
	fi; \
	if command -v cc >/dev/null || command -v gcc >/dev/null; then \
	  echo "  ok    cc       $$(command -v cc || command -v gcc)"; \
	else \
	  echo "  MISS  cc       apt-get install build-essential"; fail=1; \
	fi; \
	if $(PYTHON) -c 'import matplotlib' 2>/dev/null; then \
	  echo "  ok    matplotlib ($(PYTHON))"; \
	else \
	  echo "  warn  matplotlib  missing — 'make analyse' prints tables but no plot; 'make venv' fixes it"; \
	fi; \
	exit $$fail

build: ## compile the harness and benches (release, pinned toolchain)
	cargo build --release --all-targets

test: build ## the gate: assert the harness still matches the real code path
	cargo test --release

bench: build ## criterion: candidate generation and mempool admission
	cargo bench --bench candidate_generation

run: build ## full suite -> results/<machine>/  (~15-30 min after the build)
	./scripts/run_all.sh $(MACHINE)

analyse: ## regenerate the report's tables and figure from results/
	$(PYTHON) scripts/analyse.py

venv: ## create .venv with matplotlib, for machines that refuse a global install
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --quiet --upgrade pip matplotlib
	@echo "  created $(VENV) — 'make analyse' will now use it"

figures: analyse ## copy the regenerated figure into the report
	@mkdir -p $(REPORT)/figures
	cp results/reconstruction-latency.png $(REPORT)/figures/
	@echo "  copied into $(REPORT)/figures/"

clean: ## remove build artifacts (keeps results)
	cargo clean

distclean: clean ## additionally remove the local venv
	rm -rf $(VENV)
