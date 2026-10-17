"""Emit a multi-epoch certificate at the specification's parameters as Lean files.

Plans the certificate (`planE.make`, cached in `res_<NAME>.pkl`), optimizes the settlement
parameters (`optnum`), sets the target and writes the files (`emitF.emit`):
* `Certs/<name>/Data.lean` the band family, the potential's parameters, and each index's seeds and
                           bounds, computed at elaboration time, with its check;
* `Certs/<name>.lean`      the chosen numbers, the main checks and the finality theorem.
Usage: python3 emitE.py BETA DELTA DELTA_TSI K N NAME OUTDIR [all|emit] [MU]
(`emit` reuses the saved plan `res_<NAME>.pkl`.)
"""
import sys, os, json
from certnum import rup
import planE

if __name__ == "__main__":
    import pickle
    beta, D, delta, K, N = float(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    name, out_dir = sys.argv[6], sys.argv[7]
    mode = sys.argv[8] if len(sys.argv) > 8 else 'all'
    mu = float(sys.argv[9]) if len(sys.argv) > 9 else 0.0
    pk = f"res_{name}.pkl"
    if mode == 'emit' and os.path.exists(pk):
        res = pickle.load(open(pk, 'rb'))
    else:
        res = planE.make(beta, D, delta, K, N, mu=mu)
        pickle.dump(res, open(pk, 'wb'))
    cfg, T, fam, B, P, Ts = res
    # the settlement parameters, optimized against the exact terms (`optnum`)
    import optnum
    cand, _ = optnum.optimize(cfg, B, P)
    cfg = dict(cfg, **cand)
    _, Ts, _ = planE.terms(cfg, B, P)
    tot = sum(Ts)
    # the settlement bound's target: the planned total, rounded up to two significant digits
    target = rup(tot, 2)
    import emitF
    fin, tgt, bx = emitF.emit(cfg, T, fam, B, P, name, out_dir, target)
    json.dump(dict(cfg, target=str(tgt)), open(f"cfgE_{name}.json", "w"), indent=1)
    print(name, 'settlement', tgt, 'band', bx, 'finality', fin)
