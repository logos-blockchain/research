# Sweep targets are auto-discovered from configs/*.yaml (see the pattern rule below), so any
# new config becomes runnable as `make <stem>` with no Makefile edit.
SWEEP_CONFIGS := $(patsubst configs/%.yaml,%,$(wildcard configs/*.yaml))
.PHONY: install $(SWEEP_CONFIGS) figures verify test test-slow test-all lint clean

VENV ?= .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip

# Pin BLAS/OpenMP to a single thread so joblib's N worker processes don't oversubscribe
# the cores (numpy in each worker would otherwise each spawn a full BLAS thread pool).
export OMP_NUM_THREADS := 1
export OPENBLAS_NUM_THREADS := 1
export MKL_NUM_THREADS := 1
export NUMEXPR_NUM_THREADS := 1

$(VENV):
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

install: $(VENV)
	$(PIP) install -e ".[dev,accel]"   # accel = numba (per-node measurement speedup)

# Run any sweep config by its file stem, e.g. `make smoke`, `make default`, `make fullscale`
# (or any new configs/<name>.yaml). Each writes results + figures into a fresh dated folder under
# runs/ (runs/<YYYY-MM-DD_HHMMSS>_<label>/) so runs never overwrite. Pass extra flags via
# SWEEP_ARGS, e.g.  make fullscale SWEEP_ARGS="--batch-size 1 --mem-frac 0.6"
$(SWEEP_CONFIGS): install
	$(PY) scripts/run_sweep.py --config configs/$@.yaml --label $@ $(SWEEP_ARGS)

# Re-render figures from a run's parquet into a fresh dated figures/ folder:
#   make figures RESULTS=runs/<dir>/results.parquet
figures: install
	$(PY) scripts/make_figures.py --results $(RESULTS)

# Analytic sanity checks (simulator vs closed-form theory; replicates run across cores).
verify: install
	$(PY) scripts/verify.py

test: install          # fast subset (addopts already excludes slow)
	$(PY) -m pytest
test-slow: install
	$(PY) -m pytest -m slow
test-all: install
	$(PY) -m pytest -m ''

lint: install
	$(VENV)/bin/ruff check src scripts tests

clean:
	rm -rf runs/* results/*.parquet figures/* .pytest_cache .ruff_cache .mypy_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
