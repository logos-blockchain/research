"""4K + 2K: the noise of D and the floor premise, with the research study's chain.py (exact Markov chain).

Window 4K = 144,000 slots, beta 1 and 1/2, the specification's rule (f_hat = 0.033) and an exact rule (1/30);
today's window (388,800, beta 1) and the branch's (108,000, beta 3/4) beside them.
Prints P(S/D > 1.094) per epoch, the sd of D/S, the mean chance that fewer than 689 occupied slots follow a block
within K at 15 s, and the largest floor at 1e-9.
Usage: <finality study's python> -B split_chain.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "schedule"))
sys.dont_write_bytecode = True
import chain  # noqa: E402

for P, beta in ((388800, 1.0), (108000, 0.75), (144000, 1.0), (144000, 0.5)):
    for name, fh in chain.RULES:
        lo, hi = (0.80, 1.25)
        xs, pi = chain.stationary(P, beta, fh, lo=lo, hi=hi)
        mean = (pi * xs).sum()
        sd = math.sqrt((pi * (xs - mean) ** 2).sum()) / mean
        n = chain.PHI
        while chain.mean_miss(n, xs, pi) > 1e-9:
            n -= 1
        print(f"window {P / 3600:5.1f} h, beta {beta:.4f}, {name}: mean D/S {mean:.5f} | P(S/D > 1.094) {pi[(1 / xs) > chain.LIMIT].sum():.3e}"
              f" | sd {100 * sd:.3f} % | P(miss floor {chain.PHI}) {chain.mean_miss(chain.PHI, xs, pi):.3e} | floor at 1e-9 {n}", flush=True)
