# Environment for the dual-finality study of 2026-11-17.
# Every cache and temp file stays inside this directory. Nothing is written beside the finality
# study's sources. Import this module FIRST in every script of this directory.
#
# STUDY is the finality study, two folders up (tools/simulators/finality). These runs used its
# commit 741dc0b. It is read only.
import os
import sys

W = os.path.dirname(os.path.abspath(__file__))
STUDY = os.environ.get(
    "FINALITY_STUDY", os.path.join(W, "..", ".."))
SRC = STUDY + "/src"

for d in (".cache/numba", ".cache/tmp", "out"):
    os.makedirs(os.path.join(W, d), exist_ok=True)
os.environ["NUMBA_CACHE_DIR"] = os.path.join(W, ".cache", "numba")
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["TMPDIR"] = os.path.join(W, ".cache", "tmp")
os.environ["JOBLIB_TEMP_FOLDER"] = os.path.join(W, ".cache", "tmp")
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
sys.dont_write_bytecode = True
if SRC not in sys.path:
    sys.path.insert(0, SRC)
