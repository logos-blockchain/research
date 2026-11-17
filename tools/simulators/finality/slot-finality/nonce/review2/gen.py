# Re-run the author's sampler with another seed and keep the paired samples (for checks 1 and 2).
import sys, numpy as np
sys.path.insert(0, "..")
from model import rates
from today_choices import log2_tail_table
from d2_fallback import sample, SUB
table = log2_tail_table()
n = 4_000_000
for alpha, an in ((0.30, "30"), (1/3, "33")):
    for delta in (10, 15):
        a, h = rates(alpha)
        lg, lg2 = sample(n, a, h, delta, SUB + 2000, 6000, 5_000_000, table)
        np.save(f"pair_{an}_{delta}.npy", np.stack([lg, lg2]).astype(np.float32))
        print(an, delta, "done", flush=True)
