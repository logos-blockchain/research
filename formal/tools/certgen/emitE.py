"""Emit a multi-epoch certificate at the specification's parameters as Lean files.

Plans the certificate (`planE.make`, cached in `res_<NAME>.pkl`: the potential's parameters) and
writes the files (`emitF.emit`); the settlement parameters follow their rules:
* `Certs/<name>/Params.lean` every number the search chose;
* `Certs/<name>/Data.lean`   the family's integer bands and each index's seeds and bounds, computed at
                             elaboration time, with the kernel's checks;
* `Certs/<name>.lean`      the chosen numbers, the main checks and the finality theorem.
Usage: python3 emitE.py BETA DELTA DELTA_TSI K N NAME OUTDIR [all|emit] [MU]
(`emit` reuses the saved plan `res_<NAME>.pkl` and rebuilds the family's tables.)
"""
import sys, os, json
import planE

def retable(cfg, T, K):
    """the family, its weakest band and its tables, for the potential the plan chose"""
    from fractions import Fraction as Fr
    from certE import epoch_members, weakest, build_E, lp_in_exact
    from cert2 import lp_exact
    from certnum import rdn
    D = cfg['Delta']
    fam = epoch_members(T, K)
    bands = [m['B'] for m in fam]
    B = weakest(bands)
    c, z, s, kap, d, tau = (Fr(cfg[v]) for v in ['c', 'z', 's', 'kap', 'd', 'tau'])
    P = build_E(bands, D, c, z, s, kap, d, tau)
    P['lp'] = lp_exact(B, D, c, z, s, kap, d, P['e'])
    P['eik'], P['patk'] = [], []
    for kk, Bk in enumerate(bands):
        ek = [Fr(0)] * 19
        for i in P['eIn']: ek[i] = P['eIn'][i][kk]
        P['eik'].append(ek); P['patk'].append(rdn(Bk['slo'] * Bk['elo'] ** D, 13))
    P['lpi'] = max(lp_in_exact(D, c, z, s, kap, d, P['eik'][kk], P['patk'][kk]) for kk in range(len(bands)))
    return fam, B, P


if __name__ == "__main__":
    import pickle
    beta, D, delta, K, N = float(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5])
    name, out_dir = sys.argv[6], sys.argv[7]
    mode = sys.argv[8] if len(sys.argv) > 8 else 'all'
    mu = float(sys.argv[9]) if len(sys.argv) > 9 else 0.0
    pk = f"res_{name}.pkl"
    if mode == 'emit' and os.path.exists(pk):
        cfg, T = pickle.load(open(pk, 'rb'))[:2]
        fam, B, P = retable(cfg, T, K)
    else:
        res = planE.make(beta, D, delta, K, N, mu=mu)
        pickle.dump(res, open(pk, 'wb'))
        cfg, T, fam, B, P, _ = res
    # the settlement parameters follow their rules (`SpecData.derive`, `emitF.spec_rules`)
    import emitF
    fin, tgt, bx = emitF.emit(cfg, T, fam, B, P, name, out_dir)
    json.dump(dict(cfg, settle=str(tgt)), open(f"cfgE_{name}.json", "w"), indent=1)
    print(name, 'settlement', tgt, 'band', bx, 'finality', fin)
