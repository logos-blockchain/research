"""The depth bound and the wait bound at a lottery 1.5 times fast (a third deflated the inference),
against a third, by delay. Uses bounds.point of this study. Usage: python depth_fast.py <jobs>
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import env  # noqa: E402,F401
from joblib import Parallel, delayed  # noqa: E402
import bounds  # noqa: E402

if __name__ == "__main__":
    jobs = [(f"third d={d} scale={s}", 1 / 3, d, s) for s in (1.0, 1.5) for d in (6, 8, 10, 12, 15)]
    with open("out/depth_fast.txt", "w") as o:
        for r in Parallel(n_jobs=int(sys.argv[1]), return_as="generator")(delayed(bounds.point)(*j) for j in jobs):
            line = (f"{r['label']:24s} depth(slot reading) at 2,160: code's count {r['depth_slot_at_k_code']:.2g}, text's count {r['depth_slot_at_k_paper']:.2g}; "
                    f"blocks needed: code {r['depth_slot_need_code']}, text {r['depth_slot_need_paper']}; wait needed {r['wait_need_h']:.2f} h; after 18 h {r['wait_at_K18']:.2g}")
            print(line, flush=True); o.write(line + "\n"); o.flush()
