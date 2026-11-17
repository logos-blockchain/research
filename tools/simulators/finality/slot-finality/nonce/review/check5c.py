# mix over n using (i) G with hindsight Z (as the study), (ii) only choices complete at the cut-off (Z=0): n = 1 + M0 <= G0
import sys, numpy as np
sys.path.insert(0, ".")
import today_choices as tc
from model import rates
table = tc.log2_tail_table(); n = 4_000_000; grid = np.arange(65)
def mixwait(l2, rows, cap=64):
    l2 = np.minimum(l2, np.quantile(l2, 1-1e-4))
    w = np.bincount(np.clip(np.floor(np.maximum(l2, 0)).astype(int), 0, 64), minlength=65)/l2.size
    for i in range(rows.shape[0]):
        if float((w*rows[i][np.minimum(grid, cap)]).sum()) <= 1e-9: return (i+1)/4
for tag, alpha, delta in (("30_10", .30, 10), ("30_15", .30, 15), ("33_10", 1/3, 10), ("33_15", 1/3, 15)):
    a, h = rates(alpha)
    lg, lm, lm0, zs = tc.sample(n, a, h, delta, 8000, 6000, 999, table)
    rows = np.load(f"attack_today_{tag}.npy")
    g0 = np.log2(1+2.0**np.where(lm0 > -np.inf, lm0, -1e9))
    print(tag, "mix wait with G (hindsight Z):", mixwait(lg, rows), " with 1+M0 (Z=0, realizable at the cut-off):", mixwait(g0, rows),
          " q99.99 of log2:", np.quantile(lg, .9999), np.quantile(g0, .9999), flush=True)
