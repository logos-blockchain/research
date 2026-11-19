#!/bin/sh
# Regenerates every output of PROOF.md. Writes only into this folder.
# LIPS_REPO names a clone of logos-lips that holds 83596b6e (t1_schedule.py reads the specification).
cd "$(dirname "$0")" || exit 1
PY=${PY:-../../../../../.venv/bin/python}
export NUMBA_CACHE_DIR="$PWD/.cache/numba" PYTHONDONTWRITEBYTECODE=1
"$PY" t1_schedule.py > out_1_schedule.txt
"$PY" t2_terms.py > out_2_terms.txt
"$PY" t3_inference.py > out_3_inference.txt
"$PY" t4_checks.py > out_4_checks.txt
