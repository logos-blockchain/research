VENV ?= .venv
PY := $(VENV)/bin/python
STAMP := $(VENV)/.installed

# Keep numpy/scipy BLAS single-threaded so joblib process parallelism doesn't oversubscribe.
export OMP_NUM_THREADS := 1
export OPENBLAS_NUM_THREADS := 1
export MKL_NUM_THREADS := 1
export NUMEXPR_NUM_THREADS := 1

.PHONY: install smoke sweep sweep-fullscale redundancy percolation correlated-churn timing figures verify test lint clean

# The stamp is the real install; targets below depend on it so `make sweep` (etc.) auto-installs
# on a fresh checkout and re-installs whenever pyproject.toml changes.
$(STAMP): pyproject.toml
	python3 -m venv $(VENV)
	$(PY) -m pip install -U pip
	$(PY) -m pip install -e ".[dev]"
	@touch $(STAMP)

install: $(STAMP)

smoke: $(STAMP) ## fast end-to-end (seconds): tiny N, few rounds/seeds
	$(PY) -m blend.sweep --config configs/smoke.yaml

sweep: $(STAMP)
	$(PY) -m blend.sweep --config configs/default.yaml

sweep-fullscale: $(STAMP)
	$(PY) -m blend.sweep --config configs/fullscale.yaml

redundancy: $(STAMP) ## messaging redundancy R=1..4 (delivery vs deanonymization, time-to-link)
	$(PY) -m blend.sweep --config configs/redundancy.yaml

percolation: $(STAMP) ## churn threshold: coverage collapse at u_c = 1 - 1/(degree-1)
	$(PY) -m blend.sweep --config configs/percolation.yaml

timing: $(STAMP) ## release designs under a timing attack (jitter vs clock tick)
	$(PY) -m blend.sweep --config configs/timing.yaml

correlated-churn: $(STAMP) ## correlated AS/region outages vs uniform churn, matched fractions
	$(PY) -m blend.sweep --config configs/correlated-churn.yaml

figures: $(STAMP) ## make figures RUN=runs/<dir>
	$(PY) -m blend.plotting.make_figures --run $(RUN)

verify: $(STAMP)
	$(PY) -m blend.verify

test: $(STAMP)
	$(PY) -m pytest

lint: $(STAMP)
	$(VENV)/bin/ruff check src scripts tests

clean:
	rm -rf runs/* figures/* .pytest_cache .ruff_cache .mypy_cache
