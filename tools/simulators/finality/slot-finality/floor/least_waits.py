# The least wait at eps under the study's bound (k7_wait.need: wait_needed(wait_curve(1.5e6, alpha,
# delta, f, floor=eps/10, scale), eps)) for every wait the two RFCs quote that is not read off the
# 18-hour curves of chances_and_waits.py. One line per job: label [the value it checks], slots,
# hours.
# Usage: <study's python> least_waits.py <table|edges> <jobs>
import os
import sys
import time

W = os.path.dirname(os.path.abspath(__file__))
for d in (".cache/numba", ".cache/tmp"):
    os.makedirs(os.path.join(W, d), exist_ok=True)
os.environ["NUMBA_CACHE_DIR"] = os.path.join(W, ".cache", "numba")
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
os.environ["TMPDIR"] = os.path.join(W, ".cache", "tmp")
os.environ["JOBLIB_TEMP_FOLDER"] = os.path.join(W, ".cache", "tmp")
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
sys.dont_write_bytecode = True
SRC = os.path.join(W, "..", "..", "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from joblib import Parallel, delayed  # noqa: E402

EPS = 1e-9
T_MAX = 1_500_000
TH = 1 / 3
F30 = 1 / 30


def need(label, alpha, delta, f, scale, eps):
    import sys
    if SRC not in sys.path:
        sys.path.insert(0, SRC)
    from finality_sim.waitbound import wait_curve, wait_needed
    t0 = time.time()
    w = wait_needed(wait_curve(T_MAX, alpha, delta, f, floor=eps / 10, scale=scale), eps)
    return label, alpha, delta, f, scale, eps, w, time.time() - t0


def online(a, u):
    return a / (a + (1 - a) * u)


JOBS = {
    "table": [
        ("A1 30 %, 15 s, deflated [14.2]", 0.30, 15, F30, 1 / 0.7, EPS),
        ("A2 third, 15 s, deflated [35.6]", TH, 15, F30, 1.5, EPS),
        ("A3 30 %, 20 s [16.1]", 0.30, 20, F30, 1.0, EPS),
        ("A4 third, 20 s [33.5]", TH, 20, F30, 1.0, EPS),
        ("B1 third, 11 s, deflated [14.9]", TH, 11, F30, 1.5, EPS),
        ("B2 third, 12 s, deflated [18.2]", TH, 12, F30, 1.5, EPS),
        ("B3 third, 16 s [18 h holds up to 15 s: expect > 18]", TH, 16, F30, 1.0, EPS),
        ("B4 30 %, 16 s [10.4]", 0.30, 16, F30, 1.0, EPS),
        ("B5 30 %, 12 s, deflated [8.6]", 0.30, 12, F30, 1 / 0.7, EPS),
        ("B6 30 %, 13 s, deflated [10.1]", 0.30, 13, F30, 1 / 0.7, EPS),
        ("B7 30 %, 16 s, eps/1.21", 0.30, 16, F30, 1.0, EPS / 1.21),
        ("B8 30 %, 12 s, deflated, eps/1.21", 0.30, 12, F30, 1 / 0.7, EPS / 1.21),
        ("B9 30 %, 13 s, deflated, eps/1.21", 0.30, 13, F30, 1 / 0.7, EPS / 1.21),
        ("B10 third, 11 s, deflated, eps/1.21", TH, 11, F30, 1.5, EPS / 1.21),
        ("B11 third, 12 s, deflated, eps/1.21", TH, 12, F30, 1.5, EPS / 1.21),
        ("B12 third, 16 s, eps/1.21", TH, 16, F30, 1.0, EPS / 1.21),
        ("B13 30 %, 10 s, deflated, eps/1.21 [6.4]", 0.30, 10, F30, 1 / 0.7, EPS / 1.21),
        ("B14 third, 10 s, deflated, eps/1.21 [12.5]", TH, 10, F30, 1.5, EPS / 1.21),
        ("C1 30 %, 90 % of honest online, inferred [8.4]", online(0.30, 0.90), 10, F30, 1.0, EPS),
        ("C2 third, 90 % of honest online, inferred [16.2]", online(TH, 0.90), 10, F30, 1.0, EPS),
        ("C3 third, 95 % of honest online, inferred [12.55]", online(TH, 0.95), 10, F30, 1.0, EPS),
        ("C4 30 %, 90 % online, registered (study 8.40)", online(0.30, 0.90), 10, F30, 0.30 + 0.70 * 0.90, EPS),
        ("C5 third, 90 % online, registered (study 15.99)", online(TH, 0.90), 10, F30, TH + (1 - TH) * 0.90, EPS),
        ("E1 third, 10 s, a block every 20 s [12.5]", TH, 10, 1 / 20, 1.0, EPS),
        ("E2 third, 10 s, a block every 15 s [20.4]", TH, 10, 1 / 15, 1.0, EPS),
        ("E3 third, 10 s, deflated, a block every 40 s [10.3]", TH, 10, 1 / 40, 1.5, EPS),
        ("E4 third, 12 s, a block every 40 s [11.9]", TH, 12, 1 / 40, 1.0, EPS),
        ("E5 third, 10 s, x = 2, a block every 40 s [12.3]", TH, 10, 1 / 40, 2.0, EPS),
        ("E6 third, 95 % online, inferred, a block every 40 s [12.7]", online(TH, 0.95), 10, 1 / 40, 1.0, EPS),
        ("E7 third, 8 s [8.4]", TH, 8, F30, 1.0, EPS),
        ("E8 third, 10 s, x = 2 [19.6]", TH, 10, F30, 2.0, EPS),
        ("E9 third, 10 s, a block every 40 s", TH, 10, 1 / 40, 1.0, EPS),
        ("E10 30 %, 10 s, a block every 20 s (study 6.6)", 0.30, 10, 1 / 20, 1.0, EPS),
        ("E11 30 %, 10 s, a block every 15 s (study 9.5)", 0.30, 10, 1 / 15, 1.0, EPS),
        ("E12 third, 11 s (spec Blend's worst case, study 11.2)", TH, 11, F30, 1.0, EPS),
        ("E13 third, 13 s (study 13.8)", TH, 13, F30, 1.0, EPS),
        ("E14 third, 14 s", TH, 14, F30, 1.0, EPS),
    ],
    "edges": (
        [(f"X third, x = {x:.3f} [edge 1.925 at 18 h = 64800]", TH, 10, F30, x, EPS) for x in (1.924, 1.925, 1.926)]
        + [(f"X 30 %, x = {x:.3f} [edge 2.627 at 18 h = 64800]", 0.30, 10, F30, x, EPS)
           for x in (2.626, 2.627, 2.628, 2.629)]
        + [(f"X 30 %, x = {x:.3f} [edge 2.098 at 10 h = 36000]", 0.30, 10, F30, x, EPS)
           for x in (2.097, 2.098, 2.099)]
        + [(f"X third, x = {x:.3f} [edge 1.52 at 12.5 h = 45000]", TH, 10, F30, x, EPS)
           for x in (1.515, 1.516, 1.517, 1.520)]
    ),
}

if __name__ == "__main__":
    which = sys.argv[1]
    t0 = time.time()
    for label, a, d, f, s, e, w, dt in Parallel(n_jobs=int(sys.argv[2]), return_as="generator")(
            delayed(need)(*j) for j in JOBS[which]):
        print(f"{label:62s}: alpha {a:.5f} delta {d:>2} f 1/{1 / f:.0f} scale {s:.4f} eps {e:.3e} -> "
              f"{w} slots = {w / 3600:.3f} h  ({dt:.0f} s)", flush=True)
    print(f"done in {time.time() - t0:.0f} s")
