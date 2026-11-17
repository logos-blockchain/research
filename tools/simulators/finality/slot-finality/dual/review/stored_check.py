"""Item 4(b) from the study's stored curves (runs/b2/curves.csv): is lb(K) > ub(2K) in any cell?"""
import os
import pandas as pd
c = pd.read_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "runs", "b2", "curves.csv"))
m = c.merge(c.assign(depth=c.depth // 2)[c.depth % 2 == 0], on=["adv", "delay_s", "depth"], suffixes=("", "_2k"))
m = m[(m.lb > 1e-300) & (m.ub_2k > 0)]
m["ratio"] = m.ub_2k / m.lb
print("cells compared:", len(m), " violations (lb(K) > ub(2K)):", int((m.ratio < 1).sum()))
print(m.sort_values("ratio")[["adv", "delay_s", "depth", "lb", "ub", "ub_2k", "ratio"]].head(8).to_string())
