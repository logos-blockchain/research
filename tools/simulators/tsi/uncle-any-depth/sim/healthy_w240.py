"""D^/D without a coalition at k = 2160: W = 12 against W = 240, both under the drafted selection, paired by replicate.

Usage: healthy_w240.py <results/healthy-w12.parquet> <results/healthy-w240.parquet>
Run with PYTHONPATH pointing at the simulator's src (run_sweeps.sh builds it in work/src).
"""
import sys
import pandas as pd
from tsi_sim.config import SimConfig
from tsi_sim.plotting.figures_pernode import CONFIG_COLS, equilibrium, rho_for, sem


def load(p):
    d = pd.read_parquet(p); default = SimConfig()
    for c in CONFIG_COLS:
        if c not in d.columns: d[c] = getattr(default, c)
    return d


a, b = load(sys.argv[1]), load(sys.argv[2])
delays = sorted(b.blend_delay_max.unique()); rho = dict(zip(delays, rho_for(a, delays)))
for dl in delays:
    x = equilibrium(a[a.blend_delay_max == dl]).set_index("replicate").mean_ratio
    y = equilibrium(b[b.blend_delay_max == dl]).set_index("replicate").mean_ratio
    r = sorted(set(x.index) & set(y.index)); g = (y.loc[r] - x.loc[r]).to_numpy()
    print(f"delay {dl} (rho {rho[dl]:.2f}): W=12 {x.loc[r].mean():.4f}, W=240 {y.loc[r].mean():.4f}, "
          f"paired gap {100 * g.mean():+.2f} ± {100 * sem(g):.2f} pp (n = {len(r)})")
