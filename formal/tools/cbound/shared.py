"""One table witness for every member of a band family, by constraint generation.

A failed check's window can cross an epoch boundary, where the member changes. One table `V` that
passes every member's check needs no switching factor. Stacking all members' constraints makes a
large program, so this solves for a few members, checks every member against the solution with
the operator (`proto.Operator`), adds the worst violator, and repeats.

Usage: python3 shared.py BETA DELTA DEPTH [R] [M] [X]
"""
import sys, os, time
import numpy as np
from fractions import Fraction as Fr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proto, lp  # noqa: E402
import certE  # noqa: E402  (on the path through proto)


def shared(fam, R=12, M=24, x=2.6, start=(0,), lo=0.9960, hi=0.9985, tol=1e-5, out=None):
    box = proto.Box(R, M, 1.9, 1.0, 1.9)
    prog = lp.Program(box, 11, x)
    bands = [proto.fband(m['B']) for m in fam]
    active = list(start)
    while True:
        t = time.time()
        lam, V = lp.best_lambda(prog, [bands[i] for i in active], lo=lo, hi=hi, tol=tol)
        if V is None:
            print(f"members {active}: infeasible below {hi}")
            return None, None, active
        lams = np.array([np.max(prog.op.apply(V, B) / V) for B in bands])
        worst = int(np.argmax(lams))
        print(f"members {active}: λ = {lam:.6f}; all members: max {lams[worst]:.6f} at {worst} ({time.time() - t:.0f}s)",
              flush=True)
        if lams[worst] <= lam + 2 * tol or worst in active:
            if out:
                np.save(out, V)
            return lam, V, active
        active.append(worst)
        lo = lam  # adding constraints can only raise λ


if __name__ == "__main__":
    beta, delta, k = float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3])
    R = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    M = int(sys.argv[5]) if len(sys.argv) > 5 else 24
    x = float(sys.argv[6]) if len(sys.argv) > 6 else 2.6
    certE.set_depth(k)
    T = certE.tband(beta, delta, mu=Fr(13, 100))
    fam = certE.epoch_members(T, 32)
    lam, V, active = shared(fam, R, M, x, out=os.environ.get("WITNESS_OUT"))
    print(f"shared table: λ = {lam:.6f} for all {len(fam)} members, binding {active}")
