# The study's tooling. The TSI per-node engine is installed beside this package, editable, and
# consumed as a library (PLAN.md). Every number in the study's notes comes from one of these
# targets; `make tables` prints the notes' tables from runs/, and `make check-tables` checks that
# each appears verbatim in a note.
.PHONY: install test mutations firstlook mapping a1 b2 b3 b4 b5 b6 recovery c1 c3 c4 d0 d1b d5 d6 e2 \
        e5 all tables check-tables octave-reference clean

VENV   ?= .venv
PYTHON ?= $(HOME)/.pyenv/versions/3.13.7/bin/python
PY     := $(VENV)/bin/python
PIP    := $(VENV)/bin/pip

export OMP_NUM_THREADS := 1
export OPENBLAS_NUM_THREADS := 1

$(VENV):
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip

install: $(VENV)
	$(PIP) install -e ../tsi/tsi-sim-pernode -e ".[dev]"

test: install                 # every gate
	$(PY) -m pytest

mutations: install            # every gate must fail on its registered mutation
	$(PY) scripts/check_mutations.py

firstlook:
	python3 firstlook.py

mapping: install              # MAPPING.md
	$(PY) scripts/mapping_numbers.py

a1: install                   # RATE.md, A1 (about 10 s)
	$(PY) scripts/a1_baseline.py

c1: install                   # RATE.md, C1 (about 10 s; needs nothing else)
	$(PY) scripts/c1_rate.py
	$(PY) scripts/c1_settle_surface.py

c3: install                   # RATE.md, C3
	$(PY) scripts/c3_ghost.py

c4: install                   # RATE.md, C4 (about 3 minutes on 14 cores)
	$(PY) scripts/c4_taktikos.py

b2: install                   # SETTLEMENT.md, B2 (about 25 minutes on 14 cores)
	$(PY) scripts/b2_settlement.py
	$(PY) scripts/b2_lower.py

b3: install                   # SETTLEMENT.md, B3 (about 10 minutes on 14 cores)
	$(PY) scripts/b3_race.py
	cd scripts && ../$(PY) b3_delay.py

b4: install                   # SETTLEMENT.md, B4 elapsed time (about 15 s; needs a1)
	$(PY) scripts/b4_elapsed.py

b5: install                   # SETTLEMENT.md, B5 (about 3 minutes on 14 cores; needs a1)
	$(PY) scripts/b5_what_k_holds.py

b6: install                   # SETTLEMENT.md, B6 grinding (about 20 minutes on 14 cores; needs a1, b2, b5)
	$(PY) scripts/b6_grinding.py

recovery: install             # SETTLEMENT.md, B5 automatic recovery (about 30 s; needs a1)
	$(PY) scripts/b5_recovery.py
	$(PY) scripts/b5_recovery_sweep.py

d0: install                   # CERTIFIED.md, D0 and D2
	$(PY) scripts/d0_emission_map.py

d1b: install                  # CERTIFIED.md, D1b
	$(PY) scripts/d1b_committee.py

d5: install                   # CERTIFIED.md, D5 (needs d0)
	$(PY) scripts/d5_privacy.py

d6: install                   # CERTIFIED.md, D6 (about a minute on 14 cores)
	$(PY) scripts/d6_votes.py

e2: install                   # DAG.md, E1 and E2 (about 2 minutes on 14 cores; needs c4)
	$(PY) scripts/e2_areon.py
	$(PY) scripts/e2_fit.py

e5: install                   # DAG.md, E5 (about 20 s)
	$(PY) scripts/e5_delay.py
	$(PY) scripts/e5_balance.py

octave-reference:             # the original LCanalysis in Octave, in the background (hours)
	sh scripts/octave_reference.sh

all: a1 c1 c3 c4 b2 b3 b4 b5 recovery d0 d1b d5 d6 e2 e5 b6

tables: install
	for t in a1 c1 c1settle c3 c4 b3 b3delay b2 b4 b5 b5rec b5sweep b6 d0 d1b d3 d5 d6 e2 e5 e5balance; do \
		$(PY) scripts/tables.py $$t; done

check-tables: install
	$(PY) scripts/check_tables.py

clean:
	rm -rf $(VENV) .pytest_cache
