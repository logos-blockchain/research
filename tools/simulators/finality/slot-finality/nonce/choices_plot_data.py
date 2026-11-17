# Data for a plot of the choices at a cut-off: for each coalition size and delay, the share
# of epochs in which the coalition holds at least x nonces, counting the choices complete at the
# cut-off (1 + the largest set of chains from one fork point; the coalition holds these for certain).
# Usage: python choices_plot_data.py > choices_plot_data.out   (also writes choices_plot_data.npy)
import numpy as np
from model import rates
from today_choices import log2_tail_table, sample

SHARES = (0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 1 / 3)
XS = [1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 20, 24, 28, 32]          # log2 of the number of nonces
table = log2_tail_table()
out = np.zeros((len(SHARES), 2, len(XS)))
print("share | delay | share of epochs with at least 2^x nonces, x = " + ", ".join(str(x) for x in XS))
for i, alpha in enumerate(SHARES):
    a, h = rates(alpha)
    for j, delta in enumerate((10, 15)):
        lg, lm, lm0, zs = sample(4_000_000, a, h, delta, 8000, 6000, 999, table)
        n0 = np.log2(1.0 + 2.0 ** np.minimum(lm0, 300.0))
        for k, x in enumerate(XS):
            out[i, j, k] = np.mean(n0 >= x - 1e-9)
        who = "a third" if alpha > 0.33 else f"{int(round(alpha * 100))} %"
        print(f"{who:8s} | {delta} s | " + ", ".join(f"{v:.3g}" for v in out[i, j]), flush=True)
np.save("choices_plot_data.npy", out)
