import json, sys, math
from fractions import Fraction as Fr
from emit2 import emit
from certnum import flog10
def rnd(x, n): return Fr(round(x * 10 ** n), 10 ** n)
def make(beta, D, name, out_dir):
    p = json.load(open(f'plan_{beta}_{D}.json'))
    c, z, s, k, d = p['par']
    c, z, s, d = rnd(c, 4), rnd(z, 4), max(Fr(1), rnd(s, 4)), min(Fr(1), rnd(d, 4))
    k = min(rnd(k, 4), z - s)
    cfg = dict(desc=f"f = 1/30, k = 2160, β = {beta}, Δ = {D} slots, one epoch", fNum=1, fDen=30, beta=beta, Delta=D, k=2160,
               N=648000, G=p['G'], Gp=p['Gp'], J=p['J'], Lw=p['Lw'], r=p['r'], T=p['T'], x=str(rnd(p['x'], 3)),
               yy=str(rnd(p['yy'], 2)), c=str(c), z=str(z), s=str(s), kap=str(k), d=str(d), tau=str(Fr(p['tau']).limit_denominator(1000)))
    # find the best power-of-ten target that the exact chains certify
    for texp in range(int(-p['tot']) + 2, 0, -1):
        try:
            text, Ts, lp = emit(cfg, name, Fr(1, 10 ** texp), cfg['desc'])
            break
        except AssertionError as ex:
            continue
    open(f"{out_dir}/{name}.lean", 'w').write(text)
    json.dump(dict(cfg, target=f"1/10^{texp}"), open(f"cfg_{name}.json", 'w'), indent=1)
    print(name, 'target 1e-%d' % texp, 'lp', float(lp), 'total', f"{float(sum(Ts)):.3e}")
if __name__ == "__main__":
    make(float(sys.argv[1]) if '.' in sys.argv[1] else sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4])
