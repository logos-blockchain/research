"""The final gossip leg of the uncle study's network: 1,000 nodes, degree 6, mean link latency 0.5 s, its own topology code."""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "tsi", "tsi-sim-pernode", "src"))
import numpy as np
from tsi_sim.config import SimConfig
from tsi_sim.topology import build_path_latency

cfg = SimConfig(n_nodes=1000, degree=6, topology="blend", link_latency_mean=0.5, link_latency_dist="geo", k=2160)
pl = build_path_latency(cfg, np.random.default_rng(0))
x = pl[~np.eye(1000, dtype=bool)]
print("mean %.4f sd %.4f" % (x.mean(), x.std()), "quantiles 0, 1, 5, 25, 50, 75, 95, 99, 100 %:",
      [round(float(v), 3) for v in np.quantile(x, (0, .01, .05, .25, .5, .75, .95, .99, 1))])
# how two blocks broadcast from two random relays differ at one node
r = np.random.default_rng(1)
d = []
for _ in range(200):
    a, b = r.choice(1000, 2, replace=False)
    d.append(pl[a] - pl[b])
d = np.concatenate(d)
print("difference of two relays' distance to a node: sd %.4f" % d.std())
