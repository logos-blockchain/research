"""As depth_fast.py, against 30 % (the K row's share since 2026-11-17), deflated by its own share."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import env  # noqa: E402,F401
from joblib import Parallel, delayed  # noqa: E402
import bounds  # noqa: E402

if __name__ == "__main__":
    jobs = [(f"30 % d={d} scale={s:.4f}", 0.30, d, s) for s in (1.0, 1 / 0.7) for d in (10, 12, 15)]
    with open("out/depth_fast30.txt", "w") as o:
        for r in Parallel(n_jobs=int(sys.argv[1]), return_as="generator")(delayed(bounds.point)(*j) for j in jobs):
            line = (f"{r['label']:24s} depth(slot reading) at 2,160: code's count {r['depth_slot_at_k_code']:.2g}, text's count {r['depth_slot_at_k_paper']:.2g}; "
                    f"blocks needed: code {r['depth_slot_need_code']}, text {r['depth_slot_need_paper']}; wait needed {r['wait_need_h']:.2f} h; after 18 h {r['wait_at_K18']:.2g}")
            print(line, flush=True); o.write(line + "\n"); o.flush()
