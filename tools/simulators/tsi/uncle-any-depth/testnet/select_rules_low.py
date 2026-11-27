"""select_rules.py at a lower broadcast share and with a longer wait, W = 240 and 144."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from select_rules import *
if __name__ == "__main__":
    from multiprocessing import Pool
    per = {"last 7 days": (lo7, HI - 400), "7-14 days ago": (HI - 14 * 86400 + 3600, HI - 7 * 86400)}
    jobs = [(W, rule, p, lo, hi, sd, lag) for lo, hi in per.values() for W in (144, 240) for sd in range(4)
            for rule, p, lag in (("any", 1.0, 0), ("any", 1.0, 15), ("any", 1.0, 300), ("any", 1.0, 900),
                                 ("all", .3, 15), ("all+ref", .3, 15), ("all", .7, 15), ("all+ref", .7, 15), ("all+ref", .7, 300), ("all+ref", .7, 900),
                                 ("all", .5, 15), ("all+ref", .5, 15))]
    with Pool(8) as P: res = P.map(run, jobs, chunksize=1)
    tab = collections.defaultdict(list)
    for (W, rule, p, lo, hi, sd, lag), v in res: tab[(lo, W, rule, p, lag)].append(v)
    for name, (lo, hi) in per.items():
        for W in (144, 240):
            print(name, "W =", W)
            for k in sorted(x[2:] for x in tab if x[0] == lo and x[1] == W):
                v = tab[(lo, W) + k]; m = sum(v) / len(v); sd = (sum((x - m) ** 2 for x in v) / (len(v) - 1)) ** .5
                print(f"    rule {k[0]:8s} broadcast share {k[1]:.1f} wait {k[2]:3d} s: {m:.3f} (standard error {sd/len(v)**.5:.3f})")
