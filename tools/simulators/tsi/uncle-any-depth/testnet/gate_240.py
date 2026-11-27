"""gate_sim.py at W = 240, a window of 7,200 slots. The last T of 60,000 slots leaves 5 windows after the warm-up."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gate_sim import run
from multiprocessing import Pool
def job(a): g, kw, s = a; return g, kw, run(g, s, W=7200, T=60000, **dict(kw))
if __name__ == "__main__":
    KW = [(), (("attempt", 3.0),), (("attempt", 10.0), ("ask", 1)), (("ask", 16),)]
    jobs = [(g, kw, s) for kw in KW for g in (False, True) for s in range(4)]
    with Pool(4) as P: res = P.map(job, jobs, chunksize=1)
    for kw in KW:
        for g in (False, True):
            R = [x for gg, k, x in res if gg == g and k == kw]
            print("gate" if g else "none", dict(kw), {k: round(sum(x[k] for x in R) / len(R), 3) for k in R[0]}, flush=True)
