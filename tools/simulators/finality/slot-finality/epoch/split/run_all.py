"""Reruns the scripts of this folder in order and stores each output beside it as out_<name>.txt.

Usage: <finality study's python> -B run_all.py   (from any folder)
- displace.py runs first. exposure.py, and the scripts that import it, read out_displace.txt.
- r2_repair.py reads the curves U that ../proofs/genesis/g07_states.py caches in ../proofs/genesis/.cache. If one is missing,
  g07_states.py runs first and its output is discarded.
- The last run is ../schedule/simulate.py at a window of 4K with learning rates 1 and 1/2, stored as out_simulate_branch_4k2k.txt.
"""
import os
import subprocess
import sys
import time

H = os.path.dirname(os.path.abspath(__file__))
GEN = os.path.join(H, "..", "proofs", "genesis")
U = [os.path.join(GEN, ".cache", f"U_a{a:.6f}_d{d}_t160000_s{s:.6f}.npy")          # the five curves of r2_repair.py's CUR
     for a, d, s in ((0.3, 10, 1.0), (0.3, 15, 1.0), (0.3 / 0.93, 10, 1.0), (0.3 / 0.93, 10, 0.93), (0.3, 10, 1 / 0.7))]
SCRIPTS = ("displace", "exposure", "halt", "betacost", "rules", "genesis_u", "forkloss", "forkloss2", "forkloss3", "gossip",
           "r3_final", "r2_repair", "split_chain", "extra", "printed", "floor", "floor_half", "gamma_check")


def run(name, cmd, env=None):
    t = time.time()
    with open(os.path.join(H, f"out_{name}.txt"), "w") as out:
        r = subprocess.run(cmd, stdout=out, stderr=subprocess.STDOUT, env=env)
    print(f"{name}: exit {r.returncode}, {time.time() - t:.0f} s", flush=True)


for s in SCRIPTS:
    if s == "r2_repair" and not all(os.path.exists(u) for u in U):
        print("g07_states: caching U", flush=True)
        subprocess.run([sys.executable, "-B", os.path.join(GEN, "g07_states.py")], stdout=subprocess.DEVNULL, check=True)
    run(s, [sys.executable, "-B", os.path.join(H, s + ".py")])
run("simulate_branch_4k2k", [sys.executable, "-B", os.path.join(H, "..", "schedule", "simulate.py"), "branch", "A", "B", "C", "D"],
    dict(os.environ, WINDOW="144000", EPOCH_H="60", GAP_H="20", BETAS="1,1/2"))
