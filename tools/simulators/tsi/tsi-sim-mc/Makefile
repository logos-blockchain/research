.PHONY: install smoke sweep sweep-fullscale figures verify test test-slow test-all lint clean

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
	$(PIP) install -e ".[dev]"

# Every sweep writes results + figures into a fresh dated folder under runs/ so new
# runs never overwrite old ones (runs/<YYYY-MM-DD_HHMMSS>_<label>/).

# Fast end-to-end check (tiny scaled-k grid); uses all cores across configs.
smoke: install
	$(PY) scripts/run_sweep.py --config configs/smoke.yaml --label smoke

# Full scaled-k parameter sweep (multicore across configs; auto-generates figures).
sweep: install
	$(PY) scripts/run_sweep.py --config configs/default.yaml --label default

# Full-scale (true k) grid; small + heavy, so load-balance one config at a time.
sweep-fullscale: install
	$(PY) scripts/run_sweep.py --config configs/fullscale.yaml --label fullscale --batch-size 1

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
