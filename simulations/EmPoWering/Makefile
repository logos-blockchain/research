VENV ?= .venv
PY := $(VENV)/bin/python
STAMP := $(VENV)/.installed
CONFIG ?= configs/specified.toml
FIGURES ?= ../../reports/EmPoWering/tokenomics/figures
REPORT  ?= ../../reports/EmPoWering/tokenomics/tokenomics-model.md

.PHONY: install all fee emission rewards blend exhaustion security volume sampled fees sweeps sweeps-full web lepta verify check report-numbers notation plots pi5 bench-poseidon2 clean

# Stdlib-only package; the venv exists so `make` works identically here and in CI,
# and re-installs whenever pyproject.toml changes.
$(STAMP): pyproject.toml
	python3 -m venv $(VENV)
	$(PY) -m pip install -q -U pip
	$(PY) -m pip install -q -e .
	@touch $(STAMP)

install: $(STAMP)

# Plotting pulls matplotlib; kept out of the base install so the analyses stay stdlib-only.
$(VENV)/.plots: pyproject.toml | $(STAMP)
	$(PY) -m pip install -q -e '.[plots]'
	@touch $@

plots: $(VENV)/.plots ## the validation figures behind report section 4.7
	$(PY) -m empowering.plots --config $(CONFIG) --out $(FIGURES)

all: $(STAMP) ## every analysis section against $(CONFIG)
	$(PY) -m empowering --config $(CONFIG)

fee: $(STAMP) ## the claim transaction's fee, from the wire format and gas table
	$(PY) -m empowering --config $(CONFIG) fee

emission: $(STAMP) ## supply vs the fee schedule: where the deflationary phase begins
	$(PY) -m empowering --config $(CONFIG) emission

rewards: $(STAMP) ## steady state, headroom, builder edge, endowment ramps
	$(PY) -m empowering --config $(CONFIG) rewards

blend: $(STAMP) ## the admission threshold, on the bench machine and the Pi 5
	$(PY) -m empowering --config $(CONFIG) blend

exhaustion: $(STAMP) ## stopping conditions and their margins
	$(PY) -m empowering --config $(CONFIG) exhaustion

security: $(STAMP) ## adversarial stake accumulation during bootstrap
	$(PY) -m empowering --config $(CONFIG) security

volume: $(STAMP) ## PoW claim share of transaction volume against beta_PoW
	$(PY) -m empowering --config $(CONFIG) volume

sampled: $(STAMP) ## A2's Poisson arrivals, run rather than replaced by their mean
	$(PY) -m empowering --config $(CONFIG) sampled

fees: $(STAMP) ## the working fee range, and the mixes that produce it
	$(PY) -m empowering --config $(CONFIG) fees

sweeps: $(STAMP) ## the parameter sweeps behind report 4.4.1-4.4.3
	$(PY) -m empowering --config $(CONFIG) sweep-target sweep-share sweep-rho

sweeps-full: $(STAMP) ## section 6's full sweep programme, all axes
	$(PY) -m empowering --config $(CONFIG) sweeps-full

lepta: $(STAMP) ## exact-integer confirmation at lepton granularity
	$(PY) -m empowering.lepta --config $(CONFIG)

verify: $(STAMP) ## closed forms vs simulation, and the config's invariants
	$(PY) -m empowering.verify --config $(CONFIG)
	$(PY) -m empowering.lepta --config $(CONFIG)

LIPS ?= ../../../logos-lips
report-numbers: $(STAMP) ## every number the report quotes, against the model
	$(PY) -m empowering.report_numbers --config $(CONFIG) --report $(REPORT)

notation: $(STAMP) ## the report's symbol/name contract (§1.0)
	$(PY) -m empowering.notation --config $(CONFIG) --report $(REPORT)

check: $(STAMP) ## config vs the specification tree (set LIPS=path to logos-lips)
	$(PY) -m empowering.spec_sync --config $(CONFIG) --lips $(LIPS)

pi5: ## hands-off Pi 5 measurement: guarded runs, medians, pi5.toml, derivation table
	./scripts/run_pi5.sh

bench-poseidon2: ## measure the candidate rate (requires Rust and ../logos-blockchain)
	cd bench-poseidon2 && cargo run --release

# The panel re-implements the model in JS, so `web` regenerates its inputs from the
# same config AND fails if the two implementations disagree on the golden grid.
web: $(STAMP) ## regenerate the browser panel's data and cross-check the JS model
	$(PY) -m empowering.webexport --config $(CONFIG) --out web
	@cd web && node selfcheck.mjs || { \
		echo '  the JS model DISAGREES with the Python, or node is unavailable.'; \
		echo '  Not optional: the old "|| echo skipped" swallowed real drift AND real'; \
		echo '  failures alike -- the same silent pass the de-novo calculator shipped with.'; \
		exit 1; }

clean:
	rm -rf $(VENV) src/*.egg-info $(shell find . -name __pycache__)
