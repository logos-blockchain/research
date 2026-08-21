.PHONY: install calibrate calibrate-withhold evaluate verify cost test lint clean

VENV ?= .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip

# The package is stdlib-only, so every target below works with a bare `python3`
# as well. The venv exists for pytest and ruff, not for the analysis.
RUN ?= PYTHONPATH=src python3 -m pull_confirmation.cli

# Baseline assumptions. Override on the command line:
#   make calibrate PROVIDERS=5000 FRACTION=0.45
PROVIDERS ?= 5000
FRACTION  ?= 0.33
HOLD      ?= 0.99

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

install: $(VENV)
	$(PIP) install -e ".[dev]"

# The headline number: the smallest sample and threshold meeting both bounds,
# across a range of adversarial fractions, assuming the adversary answers
# honestly about transactions it holds.
calibrate:
	$(RUN) calibrate --providers $(PROVIDERS) --hold $(HOLD)

# The number to actually specify. An adversary that refuses to attest cannot
# make a tagged transaction confirm, but it can starve an honest one, so the
# liveness margin has to survive losing its whole share of every sample.
calibrate-withhold:
	$(RUN) calibrate --providers $(PROVIDERS) --hold $(HOLD) --withhold

# Score one candidate configuration. Exits non-zero if either bound is missed:
#   make evaluate SAMPLE=8 ROUNDS=32 THRESHOLD=127
evaluate:
	$(RUN) evaluate --providers $(PROVIDERS) --fraction $(FRACTION) --hold $(HOLD) \
		--sample $(SAMPLE) --rounds $(ROUNDS) --threshold $(THRESHOLD)

# Closed forms against the simulated protocol, at parameters a Monte-Carlo run
# can resolve. This is what licenses trusting the closed forms at 1e-9.
verify:
	$(RUN) verify --providers 500 --trials 100000

# Expected queries and rounds per transaction batch for a chosen configuration.
cost:
	$(RUN) cost --providers $(PROVIDERS) --fraction $(FRACTION) --hold $(HOLD) \
		--sample $(SAMPLE) --rounds $(ROUNDS) --threshold $(THRESHOLD)

test: install
	$(PY) -m pytest

lint: install
	$(VENV)/bin/ruff check src tests

clean:
	rm -rf .pytest_cache .ruff_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
