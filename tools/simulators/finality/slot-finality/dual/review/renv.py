# Reviewer's environment: caches inside review/, study read-only.
import os, sys
W = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.join(W, "..", "..", "..")
os.makedirs(W + "/.cache", exist_ok=True)
os.environ["NUMBA_CACHE_DIR"] = W + "/.cache"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["TMPDIR"] = W + "/.cache"
os.environ["OMP_NUM_THREADS"] = "1"
sys.dont_write_bytecode = True
sys.path.insert(0, STUDY + "/src")
