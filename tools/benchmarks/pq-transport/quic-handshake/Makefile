# =============================================================================
# quic-handshake — what a hybrid key exchange costs a QUIC handshake.
# `make help` lists everything.
#
# Design rules:
#   * The two arms differ in `kx_groups` and nothing else. TLS version, cipher
#     suites, certificate and ALPN are held identical, so any delta is
#     attributable to the key exchange.
#   * `trace` is the load-bearing target, not `run`. Datagram counts and flight
#     structure are protocol-determined and reproduce anywhere; wall-clock on
#     loopback does not (see README) and is reported for completeness only.
#   * Results are committed, so a re-run is a visible diff rather than a silent
#     drift.
# =============================================================================
SHELL := /bin/bash
.DEFAULT_GOAL := help

MACHINE ?= $(shell if [ "$$(uname -s)" = "Darwin" ]; then echo mac; \
                   elif grep -qi raspberry /proc/cpuinfo 2>/dev/null; then echo rpi5; \
                   else echo "$$(uname -m)-$$(uname -s | tr A-Z a-z)"; fi)
REPS    ?= 300

.PHONY: help where check build run trace record clean

help: ## list targets
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  make %-9s %s\n", $$1, $$2}'
	@echo
	@echo "  MACHINE=$(MACHINE)  REPS=$(REPS)"

where: ## print what this tool writes
	@echo "  results   $(abspath results)/$(MACHINE).txt"
	@echo "  machine   $(MACHINE)"

check: ## verify the environment (read-only)
	@if command -v cargo >/dev/null; then echo "  ok    cargo  $$(cargo --version)"; \
	 else echo "  MISS  cargo  install rustup: https://rustup.rs"; exit 1; fi
	@if command -v cc >/dev/null || command -v gcc >/dev/null; then echo "  ok    cc"; \
	 else echo "  MISS  cc     aws-lc-rs needs a C toolchain (apt-get install build-essential)"; exit 1; fi

build: ## compile (release, pinned toolchain)
	cargo build --release

run: build ## both arms + packet trace, to stdout
	./target/release/quic-handshake-bench $(REPS)

trace: run ## alias — the packet trace is the point

record: build ## write the run into results/$(MACHINE).txt
	@mkdir -p results
	@{ echo "# quic-handshake — $(MACHINE)"; \
	   echo "# $$(date -u +%Y-%m-%dT%H:%M:%SZ)"; \
	   if [ -r /proc/cpuinfo ]; then echo "# cpu: $$(grep -m1 -E 'model name|Model' /proc/cpuinfo | cut -d: -f2- | sed 's/^ *//')"; \
	   else echo "# cpu: $$(sysctl -n machdep.cpu.brand_string)"; fi; \
	   echo "# $$(rustc --version)"; echo; \
	   ./target/release/quic-handshake-bench $(REPS); } | tee results/$(MACHINE).txt
	@echo; echo "  wrote results/$(MACHINE).txt"

clean: ## remove build artifacts
	cargo clean
