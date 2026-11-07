# The study's tooling. The TSI per-node engine is installed beside this package, editable, and
# consumed as a library (PLAN.md). Every number the study computes comes from one of these
# targets; `make tables` prints the notes' tables from runs/, and `make check-tables` checks that
# each appears verbatim in a note.
.PHONY: install test mutations firstlook mapping a1 b2 b3 b4 b5 b6 b7 recovery c1 c3 c4 d0 d1b d5 d6 e2 \
        e5 further designs j1 j2 j3 k1 k2 k3 k5 k7 k8 k9 l1 l2 l3 l4 l5 m1 m2 m3 m4 m5 m7 \
        n1 n2 n3 n4 n5 n6 all tables \
        check-tables \
        octave-reference clean

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

a1: install                   # RATE.md, A1 (about 10 s), its release round and the convention (about 3 minutes on 4 cores)
	$(PY) scripts/a1_baseline.py
	$(PY) scripts/a1_baseline.py release
	$(PY) scripts/a1_convention.py

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

b4: install                   # SETTLEMENT.md, B4 elapsed time (about a minute; needs a1)
	$(PY) scripts/b4_elapsed.py

b5: install                   # SETTLEMENT.md, B5 (about 3 minutes on 14 cores; needs a1)
	$(PY) scripts/b5_what_k_holds.py

b6: install                   # SETTLEMENT.md, B6 grinding (about 4 minutes on 14 cores; needs a1, b2, b5)
	$(PY) scripts/b6_grinding.py

b7: install                   # SETTLEMENT.md, B7 nonce (about 3 minutes on 14 cores; needs a1, b2)
	$(PY) scripts/b7_nonce.py

recovery: install             # SETTLEMENT.md, B5 automatic recovery (about 30 s; needs a1); the engine's partition about 20 minutes on 4 cores
	$(PY) scripts/b5_recovery.py
	$(PY) scripts/b5_recovery_sweep.py
	$(PY) scripts/b5_partition.py
	$(PY) scripts/b5_partition_engine.py

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

further: install              # FURTHER.md, G1, G3, G4, G6 and G7 (about 30 minutes on 14 cores; needs a1, b2, b7, c1)
	$(PY) scripts/g1_delayed_nonce.py
	$(PY) scripts/g3_blend_delay.py
	$(PY) scripts/g4_density.py
	$(PY) scripts/g6_relays.py
	$(PY) scripts/g7_inference.py

designs: install              # PLAN.md phase H: H.1, H.2, H.3 (about 10 minutes on 14 cores; needs a1, b2, b7)
	$(PY) scripts/h1_attestations.py
	$(PY) scripts/h2_delay.py
	$(PY) scripts/h3_time_rule.py
	$(PY) scripts/i2_discriminant.py

j1: install                   # DAG.md J.1 (seconds; needs circom 2.2.2 and logos-blockchain-circuits v0.5.6)
	$(PY) scripts/j1_circuit.py

j2: install                   # DAG.md J.2 (about 25 minutes on 4 cores; needs b2 and e5)
	$(PY) scripts/j2_attacks.py

j3: install                   # DAG.md J.3 (about 5 minutes on 4 cores)
	$(PY) scripts/j3_regions.py
	$(PY) scripts/j3_bound.py

k1: install                   # SLOTS.md K.1 (about 2 minutes on 6 cores; needs a1, b2)
	$(PY) scripts/k1_settle.py

k2: install                   # SLOTS.md K.2 (about 10 minutes on 6 cores; needs a1, b2, b6, further, designs)
	$(PY) scripts/k2_holds.py

k3: install                   # SLOTS.md K.3 (about a minute; needs a1, b2)
	$(PY) scripts/k3_splits.py

k5: install                   # SLOTS.md K.4, K.5 (about 3 minutes on 4 cores; needs c1, further)
	$(PY) scripts/k5_mapping.py
	$(PY) scripts/k5_rate.py
	$(PY) scripts/k5_further.py

k7: install                   # SLOTS.md K.7 (about 40 minutes on 12 cores; needs a1, k1, k2, k5, b6, designs)
	$(PY) scripts/k7_wait.py

k8: install                   # SLOTS.md K.8 (under a minute; needs a1)
	$(PY) scripts/k8_cap.py

k9: install                   # SLOTS.md K.9 (under a minute; needs a1)
	$(PY) scripts/k9_occupancy.py

l1: install                   # NETWORK.md L.1 (seconds)
	$(PY) scripts/l1_declared.py

l2: install                   # NETWORK.md L.2 (about 5 minutes on 14 cores)
	$(PY) scripts/l2_gadget.py

l3: install                   # NETWORK.md L.3 (about 2 minutes on 14 cores)
	$(PY) scripts/l3_partition.py

l4: install                   # NETWORK.md L.4 (minutes; needs a1, k7)
	$(PY) scripts/l4_hedge.py

l5: install                   # NETWORK.md L.5 (seconds; reads reports/pqc)
	$(PY) scripts/l5_cost.py

m1: install                   # SIGNERS.md M.1 (seconds; needs d0)
	$(PY) scripts/m1_holds.py

m2: install                   # SIGNERS.md M.2 (seconds; needs d0, d6, l2, l4)
	$(PY) scripts/m2_time.py

m3: install                   # SIGNERS.md M.3 (about a minute; needs d0)
	$(PY) scripts/m3_privacy.py

m4: install                   # SIGNERS.md M.4 (seconds; reads reports/pqc)
	$(PY) scripts/m4_cost.py

m5: install                   # SIGNERS.md M.5 (seconds)
	$(PY) scripts/m5_quorum.py

m7: install                   # SIGNERS.md M.7 (about 15 minutes on 12 cores; reads reports/pqc)
	$(PY) scripts/m7_active.py

n1: install                   # UNITS.md N.1 (about 2 minutes on 12 cores)
	$(PY) scripts/n1_committee.py

n2: install                   # UNITS.md N.2 (about 10 minutes on 12 cores)
	$(PY) scripts/n2_registry.py

n3: install                   # UNITS.md N.3 (seconds; needs n1)
	$(PY) scripts/n3_transport.py

n4: install                   # UNITS.md N.4 (seconds on 12 cores; needs n1)
	$(PY) scripts/n4_privacy.py

n5: install                   # UNITS.md N.5 (seconds; needs n1; reads reports/finality/pol-proving)
	$(PY) scripts/n5_cost.py

n6: install                   # UNITS.md N.6 (seconds; needs n1, d6, m2)
	$(PY) scripts/n6_time.py

all: a1 c1 c3 c4 b2 b3 b4 b5 recovery d0 d1b d5 d6 e2 e5 b6 b7 further designs j2 j3 k1 k2 k3 k5 k7 k8 k9 \
     l1 l2 l3 l4 l5 m1 m2 m3 m4 m5 m7 n1 n2 n3 n4 n5 n6

tables: install
	for t in a1 a1release a1conv c1 c1settle c3 c4 b3 b3delay b2 b4 b5 b5rec b5sweep b5part b6 b7 d0 d1b d3 d5 d6 e2 e5 e5balance g1 g3 g4 g6 g7 h1 h2 h3 b5eng i2 j1 j2 j3 j3bound \
	         k1 k1worst k1ratio k1played k2 k2compare k2waits k2absorbs k3horizon k3eclipse k3early k3floor \
	         k3quorum k3detector k3bootstrap k5mapping k5rate k5blend k5relays k7worst k7ratio k7slots k7checks \
	         k7played k7holds k7compare k7waits k7absorbs k7rate k7blend k7floor k8params k8protection \
	         k8stall k8ratio k8deflation k8spec k9floor k9protection k9stall k9quorum \
	         l1today l1frontier l1convention l2departs l2time l3partition l4hedge l5cost \
	         m1anon m1public m1delegation m2budget m2blend m2compare m3privacy m4cost m4blend \
	         m5quorum m7supply m7seats m7wait m7edge m7declared \
	         n1committee n1units n1rounding n2registry n2lottery n3budget n3load n3p2p \
	         n4privacy n4holders n4ceilings n5bytes n5verify n5prove n6time n6layers n6online; do \
		$(PY) scripts/tables.py $$t; done

check-tables: install
	$(PY) scripts/check_tables.py

clean:
	rm -rf $(VENV) .pytest_cache
