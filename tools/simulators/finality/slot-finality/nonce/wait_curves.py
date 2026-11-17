# The finality study's wait bound (finality_sim.waitbound, SLOTS.md K.7), computed once per share and
# delay down to 1e-42 and saved, so that every factor of this study is read off one curve:
# wait(factor) = the first wait at which curve <= 1e-9 / factor.
# Usage: python wait_curves.py   (writes wait_curve_<share>_<delay>.npy; share 30 or 33)
import os
import sys
import numpy as np
from joblib import Parallel, delayed

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "src"))
F = 1 / 30


def run(alpha, delta):
    from finality_sim.waitbound import wait_curve
    c = wait_curve(2_500_000, alpha, delta, F, floor=1e-42)
    name = f"wait_curve_{'30' if alpha == 0.30 else '33'}_{delta}.npy"
    np.save(name, c)
    return name, c.size


if __name__ == "__main__":
    for r in Parallel(n_jobs=4)(delayed(run)(a, d) for a in (0.30, 1 / 3) for d in (10, 15)):
        print(r)
