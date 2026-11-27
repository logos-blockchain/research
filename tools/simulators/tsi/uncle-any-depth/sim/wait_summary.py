"""Summarise a sweep without a coalition: D^/D, the blocks that hold an entry, the blocks that make nodes wait, and the fork
blocks per k chain blocks, k(1 - q)/q, which a node that syncs the last k blocks downloads.

Usage: wait_summary.py <results/<label>.parquet>
The second half of each run's epochs is read. A sweep run without IDONLY_WAIT records no waits, and counts in
blocks_with_entries only the entries whose parent lies off the chain.
"""
import sys
import numpy as np
import pandas as pd

d = pd.read_parquet(sys.argv[1])
K = int(d.k.iloc[0])
# post burn-in: second half of each trajectory's epochs
d["n_ep"] = d.groupby(["blend_delay_max", "uncle_depth", "replicate"])["epoch"].transform("max") + 1
post = d[d.epoch >= d.n_ep // 2].copy()
post["waiting_blocks"] = post.parent_wait_block_share * post.parent_wait_late_share   # share of canonical window blocks
rows = []
for (dm, dep), g in post.groupby(["blend_delay_max", "uncle_depth"]):
    per = g.groupby("replicate").agg(ratio=("mean_ratio", "mean"), q=("mean_q", "mean"),
                                     blk=("parent_wait_block_share", "mean"),
                                     wb=("waiting_blocks", "mean"))
    allg = d[(d.blend_delay_max == dm) & (d.uncle_depth == dep)]
    late = g[g.parent_wait_late_share > 0]
    rows.append(dict(
        delay=dm, depth=dep, reps=len(per),
        ratio=per.ratio.mean(), ratio_sem=per.ratio.std(ddof=1) / np.sqrt(len(per)),
        q=per.q.mean(),
        fork_blocks_per_k=K * (1 - per.q.mean()) / per.q.mean(),
        blocks_with_entries=per.blk.mean(),
        waiting_blocks_pct=100 * per.wb.mean(),
        epochs_with_wait=f"{int((allg.parent_wait_late_share > 0).sum())}/{len(allg)}",
        nodes_per_waiting_block=(late.parent_wait_node_share / late.parent_wait_late_share).mean() if len(late) else np.nan,
        wait_mean=late.parent_wait_mean.mean() if len(late) else np.nan,
        wait_max=allg.parent_wait_max.max(),
    ))
pd.set_option("display.width", 200)
print(pd.DataFrame(rows).to_string(index=False, float_format=lambda x: f"{x:.4f}"))
