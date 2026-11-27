"""Sanity checks of select_rules.py: with every block of a held branch received by broadcast the rules agree; p = 0 leaves only the
first fork blocks that came by broadcast; and more nodes or other seeds change nothing."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from select_rules import *
if __name__ == "__main__":
    from multiprocessing import Pool
    lo, hi = lo7, HI - 400
    jobs = [(240, rule, p, lo, hi, sd, 15) for sd in (10, 11, 12) for rule, p in (("any", 1.0), ("all", 1.0), ("all+ref", 1.0), ("self", 1.0), ("all", 0.0), ("all+ref", 0.0), ("self", 0.0))]
    with Pool(4) as P: res = P.map(run, jobs, chunksize=1)
    t = collections.defaultdict(list)
    for (W, rule, p, *_), v in res: t[(rule, p)].append(v)
    for k, v in t.items(): print(k, [round(x, 3) for x in v])
    print("canonical blocks alone", round(actual(lo, hi)[1], 3), "with today's real references", round(actual(lo, hi)[0], 3))
