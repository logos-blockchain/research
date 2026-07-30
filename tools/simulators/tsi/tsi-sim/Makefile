.PHONY: install smoke sweep figures verify test lint clean

VENV ?= .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

install: $(VENV)
	$(PIP) install -e ".[dev]"

# Every sweep writes results + figures into a fresh dated folder under runs/ so new runs
# never overwrite old ones (runs/<YYYY-MM-DD_HHMMSS>_<label>/).

# Fast end-to-end check (tiny scaled-k grid); auto-generates figures.
smoke: install
	$(PY) scripts/run_sweep.py --config configs/smoke.yaml --label smoke

# Full scaled-k parameter sweep (auto-generates figures).
sweep: install
	$(PY) scripts/run_sweep.py --config configs/default.yaml --label default

# Re-render figures from an existing run's parquet into a fresh dated figures/ folder.
figures: install
	$(PY) scripts/make_figures.py --results $(RUN)/results.parquet

# Analytic sanity checks (simulator vs closed-form theory)
verify: install
	$(PY) scripts/verify.py

test: install
	$(PY) -m pytest

lint: install
	$(VENV)/bin/ruff check src scripts tests

clean:
	rm -rf runs/* results/*.parquet figures/* .pytest_cache .ruff_cache .mypy_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
