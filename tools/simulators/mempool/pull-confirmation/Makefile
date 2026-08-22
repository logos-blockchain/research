.PHONY: install calibrate calibrate-withhold evaluate verify cost test lint clean

VENV ?= .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip

# The package is stdlib-only, so every target below works with a bare `python3`
# as well. The venv exists for pytest and ruff, not for the analysis.
RUN ?= PYTHONPATH=src python3 -m pull_confirmation.cli

# Baseline assumptions, matching the documented operating point. Override on
# the command line — every variable below reaches the CLI on every target that
# uses it:
#   make evaluate SAMPLE=32 ROUNDS=8 THRESHOLD=133 WITHHOLD=1
#   make calibrate PROVIDERS=2000 FRACTIONS="0.25 0.45"
# FRACTION is a decimal; the adversary count rounds up, so 0.33333334
# reproduces "one third of 5000" = 1667 exactly.
PROVIDERS ?= 5000
FRACTION  ?= 0.33333334
HOLD      ?= 0.99
TRIALS    ?= 100000

# WITHHOLD: set non-empty (e.g. WITHHOLD=1) to model an adversary that refuses
# to attest. It cannot make a tagged transaction confirm, but it starves honest
# ones, so the documented constants are calibrated WITH it — reproduce the
# headline numbers with WITHHOLD=1.
WITHHOLD_FLAG = $(if $(WITHHOLD),--withhold)
# FRACTIONS: optional space-separated list for the calibrate sweep; the CLI's
# default list is used when unset.
FRACTIONS_FLAG = $(if $(FRACTIONS),--fractions $(FRACTIONS))

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

install: $(VENV)
	$(PIP) install -e ".[dev]"

# The headline number: the smallest stably-safe sample and threshold, across a
# range of adversarial fractions, assuming the adversary answers honestly.
calibrate:
	$(RUN) calibrate --providers $(PROVIDERS) --hold $(HOLD) $(WITHHOLD_FLAG) $(FRACTIONS_FLAG)

# The number to actually specify: the same search against a withholding
# adversary. Equivalent to `make calibrate WITHHOLD=1`.
calibrate-withhold:
	$(RUN) calibrate --providers $(PROVIDERS) --hold $(HOLD) --withhold $(FRACTIONS_FLAG)

# Score one candidate configuration. Exits non-zero if either bound is missed:
#   make evaluate SAMPLE=32 ROUNDS=8 THRESHOLD=133 WITHHOLD=1
evaluate:
	$(RUN) evaluate --providers $(PROVIDERS) --fraction $(FRACTION) --hold $(HOLD) \
		$(WITHHOLD_FLAG) --sample $(SAMPLE) --rounds $(ROUNDS) --threshold $(THRESHOLD)

# Closed forms against the simulated protocol, at parameters a Monte-Carlo run
# can resolve. This is what licenses trusting the closed forms at 1e-9.
verify:
	$(RUN) verify --providers $(PROVIDERS) --hold $(HOLD) $(WITHHOLD_FLAG) --trials $(TRIALS)

# Expected queries and rounds per transaction batch for a chosen configuration.
cost:
	$(RUN) cost --providers $(PROVIDERS) --fraction $(FRACTION) --hold $(HOLD) \
		$(WITHHOLD_FLAG) --sample $(SAMPLE) --rounds $(ROUNDS) --threshold $(THRESHOLD)

test: install
	$(PY) -m pytest

lint: install
	$(VENV)/bin/ruff check src tests

clean:
	rm -rf .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
