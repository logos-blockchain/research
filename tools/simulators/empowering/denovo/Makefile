PY := PYTHONPATH="src:../strategies/src" python3

.PHONY: validate study plots web serve

validate: ## the gate suite: closed forms, invariants, and the pinned properties
	$(PY) -m empowering_denovo_sim.validate

study: ## the scenario matrix, printed
	$(PY) -m empowering_denovo_sim.study

plots: ## the report's five figures
	$(PY) -m empowering_denovo_sim.plots --out ../../../../reports/empowering/denovo/figures

# The calculator re-implements the closed forms in JS, so `web` regenerates its inputs from
# the same source the Python reads and fails on drift rather than leaving it to a reader.
web: ## regenerate the calculator's data and cross-check the JS model
	$(PY) -m empowering_denovo_sim.webexport --out web
	@cd web && node selfcheck.mjs || { \
		echo "  the JS model DISAGREES with the Python, or node is unavailable."; \
		echo "  This is not optional: a silent pass here let the calculator drift once."; \
		exit 1; }

serve: web ## serve the calculator locally
	python3 -m http.server 8749 --directory web
