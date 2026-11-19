"""CHECK.md, item 3: the gap of GENESIS 7.2's second bound under GENESIS's own hypothesis 2K <= G + 1.

Runs c4_sim.one_config at K = 12 and G = 23 (= 2K - 1), 24 and 36, and prints the counters of the
reduction, of the 7.2 extension and of GENESIS's Step 2 witness, with one example of the gap.
Usage: python c4_extra.py [runs] > out_c4_extra.txt
"""
import os
import sys
from multiprocessing import Pool

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c4_sim  # noqa: E402

WANT = ("passes ending outside G", "MISS", "VIOLATION", "7.2 second", "crossing", "H choices with S", "runs")

if __name__ == "__main__":
    runs = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
    jobs = [({"K": 12, "G": G}, runs // 4, 990_000 + G * 10 + p) for G in (23, 24, 36) for p in range(4)]
    with Pool(min(12, os.cpu_count() or 1)) as pool:
        res = pool.map(c4_sim.one_config, jobs)
    agg, exs = {}, {}
    for cfgd, st, v, ex, dt in res:
        a = agg.setdefault(cfgd["G"], {})
        for k, x in st.items():
            a[k] = a.get(k, 0) + x
        for k, x in ex.items():
            exs.setdefault(cfgd["G"], {}).setdefault(k, x)
        for x in v:
            print(f"VIOLATION EXAMPLE (G = {cfgd['G']}): {x}")
    for G in sorted(agg):
        print(f"\nK = 12, G = {G} (2K <= G + 1: {24 <= G + 1})")
        for k in sorted(agg[G]):
            if any(w in k for w in WANT):
                print(f"  {k}: {agg[G][k]}")
        for k, x in sorted(exs.get(G, {}).items()):
            print(f"  example, {k}: {x}")
