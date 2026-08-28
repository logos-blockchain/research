# =============================================================================
# blend-header-verification — how many Blend public-header verifications per
# second a node sustains. Executable documentation: `make help` lists
# everything, and these targets are the only supported way to fetch, build and
# run it.
#
# Self-contained: nothing outside this directory is required. `fetch` vendors
# logos-blockchain into vendor/, `build` compiles its verify_public_header
# benchmark, `run` measures it. Anonymous HTTPS is the default remote, so a
# fresh Raspberry Pi with git, cargo and python3 needs no credentials.
#
# Design rules, following tools/benchmarks/pqc:
#   * `check` is READ-ONLY. Nothing here installs a system package; the toolchain
#     is the operator's to provide, and `check` says what is missing.
#   * No stamp files. Skip decisions probe real artifacts, so a deleted vendor
#     tree or a moved REF always re-does the work that depends on it.
#   * Results are NOT kept next to the tool. Every run writes to $(RESULTS), so
#     measurements live with the rest of the reports.
#   * `clean` keeps the fetched source (re-cloning the workspace is expensive);
#     `distclean` removes it too. Neither touches measured results; discarding
#     those is opt-in, via `clean-results`.
# =============================================================================
SHELL := /bin/bash
.DEFAULT_GOAL := help

HERE     := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
VENDOR   ?= $(HERE)/vendor/logos-blockchain
RESULTS  ?= $(abspath $(HERE)/../../../reports/blend/header-verification)

# Where the benchmark comes from. REF may be a branch, tag or commit; it is
# recorded alongside the numbers, because a throughput figure without the commit
# that produced it is not a measurement.
REPO_URL ?= https://github.com/logos-blockchain/logos-blockchain.git
REF      ?= master

PACKAGE  := logos-blockchain-blend-message
BENCH    := verify_public_header

# Knobs forwarded to the wrapper. `make run REPEATS=3 SAMPLE_COUNT=500`.
REPEATS      ?= 5
SAMPLE_COUNT ?= 200
ARGS         ?=

PY := python3

.PHONY: help where check fetch build run smoke clean distclean clean-results

help: ## list targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'
	@echo ""
	@echo "  variables: REF=$(REF) REPEATS=$(REPEATS) SAMPLE_COUNT=$(SAMPLE_COUNT)"
	@echo "             REPO_URL, VENDOR, RESULTS, ARGS"

where: ## print where this tool fetches, builds and writes
	@echo "source : $(REPO_URL) @ $(REF)"
	@echo "vendor : $(VENDOR)"
	@echo "results: $(RESULTS)"
	@echo "binary : $$($(MAKE) --no-print-directory bench-exe 2>/dev/null || echo '(not built)')"

check: ## verify the toolchain is present (read-only; installs nothing)
	@ok=0; \
	for tool in git cargo rustc $(PY); do \
	  if command -v $$tool >/dev/null 2>&1; then \
	    printf '  %-8s %s\n' "$$tool" "$$($$tool --version 2>&1 | head -1)"; \
	  else \
	    printf '  %-8s MISSING\n' "$$tool"; ok=1; \
	  fi; \
	done; \
	if command -v taskset >/dev/null 2>&1; then \
	  printf '  %-8s present (cores are pinned)\n' taskset; \
	else \
	  printf '  %-8s absent — pass ARGS=--no-pin, or results mix cores\n' taskset; \
	fi; \
	printf '  %-8s %s\n' cores "$$($(PY) -c 'import os;print(len(os.sched_getaffinity(0)))' 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo '?')"; \
	gov=$$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo n/a); \
	case "$$gov" in \
	  performance|n/a) note="" ;; \
	  *) note="  <-- not 'performance'; results will be conservative" ;; \
	esac; \
	printf '  %-8s %s%s\n' governor "$$gov" "$$note"; \
	if [ $$ok -ne 0 ]; then \
	  echo ""; \
	  echo "missing tools above. On Raspberry Pi OS:"; \
	  echo "  sudo apt install git python3 build-essential pkg-config libssl-dev"; \
	  echo "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"; \
	  exit 1; \
	fi

# Clone on first use, then move an existing checkout to REF. Kept shallow: the
# benchmark needs one commit, not the workspace's history.
fetch: ## vendor logos-blockchain at REF into vendor/ (clones once, then updates)
	@if [ ! -d "$(VENDOR)/.git" ]; then \
	  echo "==> cloning $(REPO_URL) @ $(REF)"; \
	  mkdir -p "$(dir $(VENDOR))"; \
	  git clone --quiet --depth 1 --branch "$(REF)" "$(REPO_URL)" "$(VENDOR)" 2>/dev/null \
	    || git clone --quiet --filter=blob:none "$(REPO_URL)" "$(VENDOR)"; \
	else \
	  echo "==> updating $(VENDOR) to $(REF)"; \
	  git -C "$(VENDOR)" fetch --quiet --depth 1 origin "$(REF)" 2>/dev/null \
	    || git -C "$(VENDOR)" fetch --quiet origin; \
	fi
	@git -C "$(VENDOR)" checkout --quiet --detach FETCH_HEAD 2>/dev/null \
	  || git -C "$(VENDOR)" checkout --quiet --detach "$(REF)"
	@echo "    at $$(git -C "$(VENDOR)" log -1 --format='%h %s')"
	@test -f "$(VENDOR)/blend/message/benches/$(BENCH).rs" \
	  || { echo "ERROR: $(BENCH).rs absent at $(REF) — pick a REF that has it" >&2; exit 1; }

build: check ## compile the verify_public_header benchmark (fetches if needed)
	@test -d "$(VENDOR)/.git" || $(MAKE) --no-print-directory fetch
	@echo "==> building $(PACKAGE) --bench $(BENCH)"
	@cd "$(VENDOR)" && cargo bench -p $(PACKAGE) --bench $(BENCH) --no-run
	@echo "    -> $$($(MAKE) --no-print-directory bench-exe)"

# Ask cargo where it put the binary rather than guessing at target/ layout.
.PHONY: bench-exe
bench-exe:
	@cd "$(VENDOR)" && cargo bench -p $(PACKAGE) --bench $(BENCH) --no-run \
	    --message-format=json 2>/dev/null \
	  | $(PY) "$(HERE)/scripts/find-exe.py" "$(BENCH)"

smoke: build ## quick end-to-end check that the pipeline works (~1 min, not a measurement)
	@$(PY) "$(HERE)/bench_header_verification.py" \
	  --exe "$$($(MAKE) --no-print-directory bench-exe)" \
	  --repo "$(VENDOR)" --repeats 1 --sample-count 20 \
	  --outdir "$(RESULTS)/smoke" $(ARGS)
	@echo "smoke run only — use 'make run' for numbers worth quoting"

run: build ## the measurement: REPEATS repeats, single-thread and all-cores
	@$(PY) "$(HERE)/bench_header_verification.py" \
	  --exe "$$($(MAKE) --no-print-directory bench-exe)" \
	  --repo "$(VENDOR)" --repeats $(REPEATS) --sample-count $(SAMPLE_COUNT) \
	  --outdir "$(RESULTS)" $(ARGS)

clean: ## remove build output and smoke scratch; keep the vendored source
	@if [ -d "$(VENDOR)/target" ]; then \
	  echo "removing $(VENDOR)/target"; rm -rf "$(VENDOR)/target"; \
	else \
	  echo "no build output to remove"; \
	fi
	@rm -rf "$(HERE)/__pycache__" "$(HERE)/scripts/__pycache__" "$(RESULTS)/smoke"
	@echo "kept the vendored checkout; use distclean to drop that too"

distclean: clean ## additionally remove the vendored checkout (forces a re-fetch)
	@rm -rf "$(HERE)/vendor"
	@echo "removed vendor/; measurements in $(RESULTS) are untouched"

# Deliberately out of reach of clean and distclean: a results tree is measured
# data, and sometimes the only copy of a run on hardware that is not to hand.
clean-results: ## OPT-IN: discard the measured results in RESULTS
	@echo "removing $(RESULTS)"
	@rm -rf "$(RESULTS)"
