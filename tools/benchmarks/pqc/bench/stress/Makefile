# Build the role-asymmetry stress harness against the pinned liboqs.
#
# Same contract as bench/kem_sig: paths and flags default to the vendored
# toolchain and are overridable so the orchestrator can pass the exact values
# from setup/versions.lock (single source of truth):
#   make LIBOQS_PREFIX=... OPENSSL_PREFIX=... BENCH_CFLAGS="-O3 -mcpu=cortex-a76"
#
# OpenSSL is linked for the classical X25519/Ed25519 baselines, which are
# measured under the same role model so the migration comparison is like for
# like — the same reason bench/kem_sig links it.

ROOT          := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))../..)
LIBOQS_PREFIX ?= $(ROOT)/vendor/install
# OpenSSL: prefer the pinned keg-only Homebrew openssl@3.5 on macOS, else system.
OPENSSL_PREFIX ?= $(shell brew --prefix openssl@3.5 2>/dev/null || echo /usr)
BENCH_CFLAGS  ?= -O3

CC     ?= cc
CFLAGS := $(BENCH_CFLAGS) -std=c11 -Wall -Wextra -pthread \
          -I$(LIBOQS_PREFIX)/include -I$(OPENSSL_PREFIX)/include
LDFLAGS := -L$(LIBOQS_PREFIX)/lib -L$(OPENSSL_PREFIX)/lib \
           -Wl,-rpath,$(LIBOQS_PREFIX)/lib -Wl,-rpath,$(OPENSSL_PREFIX)/lib
LDLIBS  := -loqs -lcrypto -lm -pthread

.DEFAULT_GOAL := stress_roles

# Same hard guard as bench/kem_sig: a system liboqs would silently change what
# is measured, and role ratios from an unpinned library are not comparable with
# the published ones.
liboqs-guard:
	@if ! test -f "$(LIBOQS_PREFIX)/include/oqs/oqs.h" || ! ls "$(LIBOQS_PREFIX)"/lib/liboqs.* >/dev/null 2>&1; then \
	  echo "ERROR: pinned vendored liboqs not found. Looked for BOTH of:"; \
	  echo "  $(LIBOQS_PREFIX)/include/oqs/oqs.h"; \
	  echo "  $(LIBOQS_PREFIX)/lib/liboqs.*"; \
	  echo "Run 'make build' from the tool root first (see README)."; \
	  exit 1; \
	fi

stress_roles: stress_roles.c | liboqs-guard
	$(CC) $(CFLAGS) -o $@ $< $(LDFLAGS) $(LDLIBS)

clean:
	rm -f stress_roles

.PHONY: clean liboqs-guard
