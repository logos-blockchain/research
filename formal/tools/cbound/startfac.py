"""The failed-check witness with a bounded start factor.

The check starts at an anchor where the margin equals the reach, which the reach potential `cr^ρ`
bounds in expectation (`stat`). A table witness then costs the factor `C = max V(ρ, ρ) / cr^ρ` on the
failed-check term. This finds, for a fixed `λ` and each group of members, the table with the least
`C` (constraint generation over the group's members, as `shared.py`), and the ratios between the
groups' tables.

Usage: python3 startfac.py BETA DELTA DEPTH LAMBDA [CR] [R] [M] [X]
"""
import sys, os, time
import numpy as np
from fractions import Fraction as Fr

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import proto, lp  # noqa: E402
import certE  # noqa: E402


def least_C(fam, lam, cr=1.9, R=12, M=24, x=2.6, tol=1e-6):
    box = proto.Box(R, M, cr, 1.0, 1.9)
    prog = lp.Program(box, 11, x)
    bands = [proto.fband(m['B']) for m in fam]
    active = [0]
    while True:
        ok, V, C = prog.feasible([bands[i] for i in active], lam, cr=cr)
        if not ok:
            return None, None, active
        lams = np.array([np.max(prog.op.apply(V, B) / V) for B in bands])
        worst = int(np.argmax(lams))
        if lams[worst] <= lam + tol or worst in active:
            return C, V, active
        active.append(worst)


if __name__ == "__main__":
    beta, delta, k, lam = float(sys.argv[1]), float(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4])
    cr = float(sys.argv[5]) if len(sys.argv) > 5 else 1.9
    R = int(sys.argv[6]) if len(sys.argv) > 6 else 12
    M = int(sys.argv[7]) if len(sys.argv) > 7 else 24
    x = float(sys.argv[8]) if len(sys.argv) > 8 else 2.6
    certE.set_depth(k)
    T = certE.tband(beta, delta, mu=Fr(13, 100))
    fam = certE.epoch_members(T, 32)
    Vs, Cs = [], []
    for g in range(4):
        t = time.time()
        C, V, act = least_C(fam[8 * g:8 * g + 8], lam, cr, R, M, x)
        if C is None:
            print(f"group {g}: infeasible at λ = {lam}")
            sys.exit(1)
        Vs.append(V); Cs.append(C)
        print(f"group {g}: C = {C:.3f} (binding members {[8 * g + i for i in act]}, {time.time() - t:.0f}s)", flush=True)
    sw = max(max(np.max(Vs[a][Vs[b] > 1e-12] / Vs[b][Vs[b] > 1e-12]) for b in range(4) if b != a) for a in range(4))
    print(f"λ = {lam}: start factor max C = {max(Cs):.3f}, switching factor {sw:.3f}")
