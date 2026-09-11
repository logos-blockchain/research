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
# MAJORITY: calibrate the sample size under a majority-of-sample rule.
# RESAMPLE: on verify and cost, draw from the whole set each round instead of an urn.
# SEQUENTIAL: on verify, check the sequential walk instead of the closed forms.
# THRESHOLD: omit on evaluate/cost to score a majority of the sample.
# MIN_SAMPLE: on evaluate/cost, the specification's rule — a majority of everyone
# asked, from this many answers on, checked after every round.
MAJORITY_FLAG   = $(if $(MAJORITY),--majority)
RESAMPLE_FLAG   = $(if $(RESAMPLE),--resample)
SEQUENTIAL_FLAG = $(if $(SEQUENTIAL),--sequential)
THRESHOLD_FLAG  = $(if $(THRESHOLD),--threshold $(THRESHOLD))
MIN_SAMPLE_FLAG = $(if $(MIN_SAMPLE),--min-sample $(MIN_SAMPLE))
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
	$(RUN) calibrate --providers $(PROVIDERS) --hold $(HOLD) $(WITHHOLD_FLAG) $(MAJORITY_FLAG) $(FRACTIONS_FLAG)

# The number to actually specify: the same search against a withholding
# adversary. Equivalent to `make calibrate WITHHOLD=1`.
calibrate-withhold:
	$(RUN) calibrate --providers $(PROVIDERS) --hold $(HOLD) --withhold $(FRACTIONS_FLAG)

# Score one candidate configuration. Exits non-zero if either bound is missed:
#   make evaluate SAMPLE=16 ROUNDS=16 MIN_SAMPLE=128 WITHHOLD=1   (the specification)
#   make evaluate SAMPLE=32 ROUNDS=8 THRESHOLD=133 WITHHOLD=1     (a fixed threshold)
evaluate:
	$(RUN) evaluate --providers $(PROVIDERS) --fraction $(FRACTION) --hold $(HOLD) \
		$(WITHHOLD_FLAG) --sample $(SAMPLE) --rounds $(ROUNDS) $(THRESHOLD_FLAG) $(MIN_SAMPLE_FLAG)

# Closed forms against the simulated protocol, at parameters a Monte-Carlo run
# can resolve. This is what licenses trusting the closed forms at 1e-9.
# SEQUENTIAL=1 checks the sequential walk the same way, and then runs the
# protocol as specified beside its urn approximation.
verify:
	$(RUN) verify --providers $(PROVIDERS) --hold $(HOLD) $(WITHHOLD_FLAG) $(RESAMPLE_FLAG) \
		$(SEQUENTIAL_FLAG) --trials $(TRIALS)

# Expected queries and rounds per transaction batch for a chosen configuration.
# RESAMPLE=1 draws from the whole set each round, as the specification does.
cost:
	$(RUN) cost --providers $(PROVIDERS) --fraction $(FRACTION) --hold $(HOLD) \
		$(WITHHOLD_FLAG) --sample $(SAMPLE) --rounds $(ROUNDS) $(THRESHOLD_FLAG) \
		$(MIN_SAMPLE_FLAG) $(RESAMPLE_FLAG)

test: install
	$(PY) -m pytest

lint: install
	$(VENV)/bin/ruff check src tests

clean:
	rm -rf .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
