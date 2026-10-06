# =============================================================================
# pol-proving — how long the node takes to prove leadership, the circuit a vote
# would reuse (tools/simulators/finality/CERTIFIED.md, D3). Executable
# documentation: `make help` lists everything.
#
# Self-contained, following tools/benchmarks/blend-header-verification: `fetch`
# vendors logos-blockchain into vendor/, `build` compiles its `prove` benchmark,
# `run` measures it. Anonymous HTTPS is the default remote, so a fresh Raspberry
# Pi with git, cargo and python3 needs no credentials.
#
#   * `check` is READ-ONLY. Nothing here installs a system package.
#   * Results are not kept next to the tool. Every run writes to $(RESULTS).
#   * `clean` keeps the fetched source; `distclean` removes it too. Neither
#     touches measured results.
# =============================================================================
SHELL := /bin/bash
.DEFAULT_GOAL := help

HERE     := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
VENDOR   ?= $(HERE)/vendor/logos-blockchain
RESULTS  ?= $(abspath $(HERE)/../../../reports/finality/pol-proving)

# The commit the finality study reads the node at. A proving time without the
# commit that produced it is not a measurement, so the wrapper records it.
REPO_URL ?= https://github.com/logos-blockchain/logos-blockchain.git
REF      ?= 4e0405d519d1d3428feb0e118fa651fb4e18ca05

PACKAGE  := logos-blockchain-pol
BENCH    := prove

REPEATS      ?= 3
SAMPLE_COUNT ?= 20
ARGS         ?=

PY := python3

# The node's .cargo/config.toml links with rust-lld on macOS, which fails on some
# toolchains. An empty RUSTFLAGS overrides it there; Linux is unaffected.
ifeq ($(shell uname -s),Darwin)
export RUSTFLAGS ?=
endif

.PHONY: help where check fetch build run smoke clean distclean clean-results bench-exe

help: ## list targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-14s %s\n", $$1, $$2}'
	@echo ""
	@echo "  variables: REF=$(REF)"
	@echo "             REPEATS=$(REPEATS) SAMPLE_COUNT=$(SAMPLE_COUNT) REPO_URL VENDOR RESULTS ARGS"

where: ## print where this tool fetches, builds and writes
	@echo "source : $(REPO_URL) @ $(REF)"
	@echo "vendor : $(VENDOR)"
	@echo "results: $(RESULTS)"

check: ## verify the toolchain is present (read-only; installs nothing)
	@ok=0; \
	for tool in make cc git cargo rustc curl unzip $(PY); do \
	  if command -v $$tool >/dev/null 2>&1; then \
	    case $$tool in unzip) v=$$(unzip -v 2>&1 | head -1) ;; *) v=$$($$tool --version 2>&1 | head -1) ;; esac; \
	    printf '  %-8s %s\n' "$$tool" "$$v"; \
	  else \
	    printf '  %-8s MISSING\n' "$$tool"; ok=1; \
	  fi; \
	done; \
	if command -v taskset >/dev/null 2>&1; then \
	  printf '  %-8s present (the one-core run is pinned)\n' taskset; \
	else \
	  printf '  %-8s absent (the one-core run is skipped)\n' taskset; \
	fi; \
	gov=$$(cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor 2>/dev/null || echo n/a); \
	case "$$gov" in \
	  performance|n/a) note="" ;; \
	  *) note="  <-- not 'performance'; results will be conservative" ;; \
	esac; \
	printf '  %-8s %s%s\n' governor "$$gov" "$$note"; \
	if [ $$ok -ne 0 ]; then \
	  echo ""; \
	  echo "missing tools above. On Raspberry Pi OS (64-bit):"; \
	  echo "  sudo apt install git curl unzip python3 build-essential pkg-config libssl-dev"; \
	  echo "  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"; \
	  exit 1; \
	fi

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
	@git -C "$(VENDOR)" checkout --quiet --detach "$(REF)" 2>/dev/null \
	  || git -C "$(VENDOR)" checkout --quiet --detach FETCH_HEAD
	@echo "    at $$(git -C "$(VENDOR)" log -1 --format='%h %s')"
	@test -f "$(VENDOR)/zk/proofs/pol/benches/$(BENCH).rs" \
	  || { echo "ERROR: zk/proofs/pol/benches/$(BENCH).rs absent at $(REF)" >&2; exit 1; }

build: check ## compile the prove benchmark (fetches if needed)
	@test -d "$(VENDOR)/.git" || $(MAKE) --no-print-directory fetch
	@echo "==> building $(PACKAGE) --bench $(BENCH)"
	@cd "$(VENDOR)" && cargo bench --locked -p $(PACKAGE) --bench $(BENCH) --no-run
	@echo "    -> $$($(MAKE) --no-print-directory bench-exe)"

bench-exe:
	@cd "$(VENDOR)" && cargo bench --locked -p $(PACKAGE) --bench $(BENCH) --no-run \
	    --message-format=json 2>/dev/null \
	  | $(PY) "$(HERE)/scripts/find-exe.py" "$(BENCH)"

smoke: build ## quick end-to-end check that the pipeline works (not a measurement)
	@$(PY) "$(HERE)/bench_pol_proving.py" \
	  --exe "$$($(MAKE) --no-print-directory bench-exe)" \
	  --repo "$(VENDOR)" --repeats 1 --sample-count 3 \
	  --outdir "$(RESULTS)/smoke" $(ARGS)
	@echo "smoke run only — use 'make run' for numbers worth quoting"

run: build ## the measurement: REPEATS repeats, on all cores and pinned to one
	@$(PY) "$(HERE)/bench_pol_proving.py" \
	  --exe "$$($(MAKE) --no-print-directory bench-exe)" \
	  --repo "$(VENDOR)" --repeats $(REPEATS) --sample-count $(SAMPLE_COUNT) \
	  --outdir "$(RESULTS)" $(ARGS)

clean: ## remove build output and smoke scratch; keep the vendored source
	@rm -rf "$(VENDOR)/target" "$(HERE)/__pycache__" "$(HERE)/scripts/__pycache__" "$(RESULTS)/smoke"
	@echo "kept the vendored checkout; use distclean to drop that too"

distclean: clean ## additionally remove the vendored checkout (forces a re-fetch)
	@rm -rf "$(HERE)/vendor"
	@echo "removed vendor/; measurements in $(RESULTS) are untouched"

clean-results: ## OPT-IN: discard the measured results in RESULTS
	@echo "removing $(RESULTS)"
	@rm -rf "$(RESULTS)"
