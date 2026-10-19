"""A fast mirror of the grouped table certificate's checks (`Prob/TableGCert.lean`, `TableGSpec.lean`).

Lean computes each (group, representative)'s data (`FamCfg.repDataG`) and the kernel checks it; a full
certificate build takes most of an hour. This module computes the same numbers exactly, with the integer
mirrors of `emitZ`, so that a choice of tables, groups or delayed steps can be judged in minutes:

- `rep_data`: a representative's terminal table (`TabQ.gList`), its post- and pre-switch seeds and bounds
  (`eIn`, `eE`), and its members' delayed bounds (`eD`, as `FamCfg.eDListX`);
- `contractions`: `lp` and `lpi` by the rules of `tabLpG` and `tabLpiG`;
- `derive`: the derived numbers and the finality bound (`SpecData.deriveLE`, via `emitF.spec_rules` and
  `powq`).

The per-entry data are cached on disk (`CACHE`), keyed by the table and the entry, and computed in
parallel.

Usage: python3 tabsim.py BETA DELTA K N DEPTH VJ.npy NG R M CW ZC X C Z TAU GAMMA_BIG KSTART RDLY [MODE]
with MODE `own` (each member's own delayed chain), `grp` (the group's, as `chkDlyG`, the default).
"""
import sys, os, pickle, hashlib
from fractions import Fraction as Fr
from multiprocessing import Pool
import numpy as np
import certE, emitF, emitZ, powq
from certnum import rup, rdn
from emitZ import SZ, H, cdiv, fill, g_floor, solve_seeds, seeds_chain, boundz, stepz, M as MZ
from emitT import round_table

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.tabsim_cache')
PAD = 2 ** 8


# ---- the tables over ℚ (`TableQ.lean`, `Table.lean`, `TableSpec.lean`)

def step_o(st, A, Hh, X):
    """`stepO`"""
    r, mu = st
    return (max(r + A - Hh, A), mu + A - Hh if mu < -A else (r - Hh if X else max(r + A - Hh, A)))


def vq(tab, st):
    """`TabQ.VQ`"""
    w, cold, R, M, cw, zc = tab
    r, mu = st
    rn = max(r, 0)
    up = cw ** max(rn - R, 0)
    if mu >= 0:
        return w[min(rn, R)] * up
    d = -mu - 1
    return cold[min(rn, R)][min(d, M - 1)] * up * (1 / zc) ** max(d - (M - 1), 0)


def cr_q(tab, s):
    """`TabQ.crQ`"""
    return vq(tab, step_o(s, 0, 1, False)) - vq(tab, step_o(s, 0, 1, True))


def g_list(tab, s, x):
    """`TabQ.gList`"""
    R, M = tab[2], tab[3]
    AX = R + M + 2
    gmax = lambda b: max([Fr(0)] + [vq(tab, step_o(s, i + 2, 1 if b else 0, False)) / x ** (i + 2) for i in range(AX - 1)])
    gl = [vq(tab, step_o(s, 0, 0, False)), vq(tab, step_o(s, 0, 1, False)), vq(tab, step_o(s, 1, 0, False)) / x,
          vq(tab, step_o(s, 1, 1, False)) / x, gmax(False), gmax(True)]
    return [rup(v, 13) for v in gl]


def ph_of(x, th, gl):
    """`PhZ.ofQ (x, θ, gq)`"""
    x, th = Fr(x), Fr(th)
    gs = {(a, b, u): gl[2 * a + (1 if b else 0)] for a in range(3) for b in (False, True) for u in (False, True)}
    gd = emitZ.lcm([v.denominator for v in gs.values()])
    return dict(xn=x.numerator, xd=x.denominator, tn=th.numerator, td=th.denominator,
                gn={k: int(v * gd) for k, v in gs.items()}, gd=gd)


def reps(R, M):
    """`TabQ.repList`"""
    out = []
    for r in range(R + 2):
        out.append((r, r))
        out += [(r, -(j + 1)) for j in range(M + 1)]
    return out


# ---- a representative's data

def step_tab(Bs, D, Dl, X, v):
    """`stepTabGZ`: one step, the largest over `Bs` and at least 0, rounded up"""
    m = MZ(X, D)
    w = lambda q, a, u: v[(q, a, u)]
    return {(q, a, u): max([0] + [cdiv(stepz(B, D, Dl, X, SZ, w, q, a, u), m) for B in Bs])
            for q in range(Dl) for a in range(3) for u in (False, True)}


def bound_q(B, D, X, v):
    return Fr(boundz(B, D, X, SZ, lambda q, a, u: v[(q, a, u)]), MZ(X, D) * SZ)


def rep_data(args):
    """`repDataG` for one entry, with every member's delayed bounds for each `r ≤ Rmax`, from `vmax`:
    by its own chain (`own`) and by its group's (`grp`)"""
    tab, s, x, gam, famZ, D, Dl, grp_members, Rmax = args
    gl = g_list(tab, s, x)
    X = ph_of(x, gam, gl)
    lo = g_floor(X, SZ)
    floor = [lo(0, a, True) for a in range(3)]
    post = seeds_chain(D, Dl, X, SZ, lo, H, PAD, 3, 2, 200, famZ, floor)
    posts = [fill([B], D, Dl, X, SZ, lo, t) for B, t in zip(famZ, post)]
    vmax = {key: max([0] + [p[key] for p in posts]) for key in posts[0]}
    vlo = lambda q, a, u: vmax[(q, a, u)]
    pre = [solve_seeds([B], D, Dl, X, SZ, vlo, H, PAD, 0, 200, [vmax[(0, a, True)] for a in range(3)]) for B in famZ]
    pres = [fill([B], D, Dl, X, SZ, vlo, t) for B, t in zip(famZ, pre)]
    eIn = [rup(bound_q(B, D, X, po), 13) for B, po in zip(famZ, posts)]
    eEk = [rup(bound_q(B, D, X, pr), 13) for B, pr in zip(famZ, pres)]
    # delayed bounds: own[k][r], grp[k][r] for the group's members
    own, grpb = {}, {}
    for k in grp_members:
        t = vmax; row = []
        for r in range(Rmax + 1):
            row.append(rup(bound_q(famZ[k], D, X, t), 13)); t = step_tab([famZ[k]], D, Dl, X, t)
        own[k] = row
    t = vmax; rows = {k: [] for k in grp_members}
    for r in range(Rmax + 1):
        for k in grp_members: rows[k].append(rup(bound_q(famZ[k], D, X, t), 13))
        t = step_tab([famZ[k] for k in grp_members], D, Dl, X, t)
    grpb = rows
    return dict(g=gl, eIn=eIn, eEk=eEk, eE=max([Fr(0)] + eEk), own=own, grp=grpb)


# ---- the geometric envelope of a member's delayed tables

def lin_step(B, D, Dl, X, Z):
    """the recursion step's linear part (`g` set to 0), times `M · S`, at every entry"""
    X0 = dict(X); X0['gn'] = {k: 0 for k in X['gn']}
    w = lambda q, a, u: Z[(q, a, u)]
    return {(q, a, u): stepz(B, D, Dl, X0, SZ, w, q, a, u) for q in range(Dl) for a in range(3) for u in (False, True)}


def envelope(B, D, Dl, X, P, vmax, mu, n):
    """`envZ`: from `Y0 = (vmax - P)⁺`, the iterates of the step without the terminal table (rounded up, at
    least 0), `Z = Σ_{i<n} Y_i / mu^i` by Horner's rule (rounded up), the least `λ` with `L(Z) ≤ λ Z` and
    `Z`'s phase bound without the terminal table, both rounded up to 13 digits"""
    m = MZ(X, D)
    mu = Fr(mu)
    X0 = dict(X); X0['gn'] = {kk: 0 for kk in X['gn']}
    T = 2 ** 32   # the iterates' finer scale
    L = lambda Y: {k: max(0, cdiv(v, m)) for k, v in lin_step(B, D, Dl, X, Y).items()}
    Y = {k: (max(0, vmax[k] - P[k]) + 1) * T for k in P}
    ys = [Y]
    for _ in range(n): ys.append(L(ys[-1]))
    acc = {k: 0 for k in P}
    for Yi in reversed(ys[:n]):
        acc = {k: Yi[k] + cdiv(acc[k] * mu.denominator, mu.numerator) for k in P}
    Z = {k: cdiv(acc[k], T) for k in P}
    LZ = lin_step(B, D, Dl, X, Z)
    lam = Fr(0)
    for q in range(Dl):
        for a in range(3):
            for u in (False, True):
                k = (q, a, u)
                if Z[k] == 0:
                    if LZ[k] > 0: lam = Fr(1)
                else: lam = max(lam, Fr(LZ[k], Z[k] * m))
    aZ = rup(Fr(boundz(B, D, X0, SZ, lambda q, a, u: Z[(q, a, u)]), m * SZ), 13)
    return rup(lam, 13), aZ


def rep_env(args):
    """each of the group's members' envelope: `(λ, autoBound₀(Z))`"""
    tab, s, x, gam, famZ, D, Dl, grp_members, mu, n = args
    gl = g_list(tab, s, x)
    X = ph_of(x, gam, gl)
    lo = g_floor(X, SZ)
    floor = [lo(0, a, True) for a in range(3)]
    post = seeds_chain(D, Dl, X, SZ, lo, H, PAD, 3, 2, 200, famZ, floor)
    posts = [fill([B], D, Dl, X, SZ, lo, t) for B, t in zip(famZ, post)]
    vmax = {key: max([0] + [p[key] for p in posts]) for key in posts[0]}
    return {k: envelope(famZ[k], D, Dl, X, posts[k], vmax, mu, n) for k in grp_members}


def worst_z(famZ):
    """`worstZ`"""
    return dict(hhi=max(b['hhi'] for b in famZ), hlo=min(b['hlo'] for b in famZ), amax=max(b['amax'] for b in famZ),
                hahi=max(b['hahi'] for b in famZ), alo=min(b['alo'] for b in famZ), halo=min(b['halo'] for b in famZ))


def rep_w(args):
    """`repDataG` as the certificate computes it: the members' in-epoch bounds, the worst band's tables `W`
    and `PW`, the group's largest pre-switch bound `eE`, and each group member's envelope against `W`"""
    tab, s, x, gam, famZ, D, Dl, grp_members, mu, n = args
    gl = g_list(tab, s, x)
    X = ph_of(x, gam, gl)
    lo = g_floor(X, SZ)
    floor = [lo(0, a, True) for a in range(3)]
    post = seeds_chain(D, Dl, X, SZ, lo, H, PAD, 3, 2, 200, famZ, floor)
    posts = {k: fill([famZ[k]], D, Dl, X, SZ, lo, post[k]) for k in range(len(famZ))}
    eIn = [rup(bound_q(famZ[k], D, X, posts[k]), 13) for k in range(len(famZ))]
    BW = worst_z(famZ)
    w = solve_seeds([BW], D, Dl, X, SZ, lo, H, PAD, 3, 200, floor)
    W = fill([BW], D, Dl, X, SZ, lo, w)
    Wlo = lambda q, a, u: W[(q, a, u)]
    pw = solve_seeds([BW], D, Dl, X, SZ, Wlo, H, PAD, 0, 200, [W[(0, a, True)] for a in range(3)])
    PW = fill([BW], D, Dl, X, SZ, Wlo, pw)
    eE = rup(max([Fr(0)] + [bound_q(famZ[k], D, X, PW) for k in grp_members]), 13)
    env = {k: envelope(famZ[k], D, Dl, X, posts[k], W, mu, n) for k in grp_members}
    return dict(eIn=eIn, eE=eE, env=env)


# ---- the certificate

class Cert:
    def __init__(self, beta, delta, K, N, depth, Vfile, ng, R, M, cw, zc, x, c, z, tau, Gam, ks):
        certE.set_depth(depth)
        self.T = certE.tband(beta, delta, mu=Fr(13, 100))
        self.fam = certE.epoch_members(self.T, K)
        self.K, self.N, self.depth, self.ng = K, N, depth, ng
        self.Dl = 11
        self.D, self.famZ = emitZ.fam_z(self.fam)
        self.x, self.c, self.z, self.tau, self.Gam = x, c, z, tau, Gam
        EL = certE.EL
        self.gam = 1 + Fr(1, ks * (EL - 1))
        eUp = Fr(27182818286, 10000000000)
        sU = Fr(int(float(eUp) ** (1 / ks) * 10 ** 9) + 1, 10 ** 9)
        while sU ** ks < eUp: sU += Fr(1, 10 ** 9)
        self.sU = sU
        Vs = np.load(Vfile)
        self.tabs = [round_table(Vs[g], R, M, cw, zc, c, z) + (R, M, cw, zc) for g in range(ng)]
        self.tabs = [(w, cold, R, M, cw, zc) for (w, cold, *_rest) in self.tabs]
        self.reps = reps(R, M)
        self.key = hashlib.sha1(pickle.dumps((beta, delta, K, depth, Vfile and np.load(Vfile).tobytes(), ng, R, M, cw, zc,
                                               x, c, z, ks))).hexdigest()[:16]
        self.pat = [rdn(m['B']['slo'] * m['B']['elo'] ** self.Dl, 13) for m in self.fam]

    def grp_of(self, k): return k * self.ng // self.K

    def members(self, g): return [k for k in range(self.K) if self.grp_of(k) == g]

    def data(self, Rmax, procs=11):
        """every entry's data, cached"""
        os.makedirs(CACHE, exist_ok=True)
        path = os.path.join(CACHE, f"{self.key}_{Rmax}.pkl")
        if os.path.exists(path):
            return pickle.load(open(path, 'rb'))
        jobs = [(self.tabs[g], s, self.x, self.gam, self.famZ, self.D, self.Dl, self.members(g), Rmax)
                for g in range(self.ng) for s in self.reps]
        with Pool(procs) as p:
            res = p.map(rep_data, jobs, chunksize=4)
        out = {(g, s): r for (g, s), r in zip([(g, s) for g in range(self.ng) for s in self.reps], res)}
        pickle.dump(out, open(path, 'wb'))
        return out

    def contractions(self, dat, R, mode='grp'):
        """`tabLpG`, `tabLpiG` (with the delayed bounds at `R` steps), and the worst entries"""
        lp = rup(max(d['eE'] / vq(self.tabs[g], s) for (g, s), d in dat.items()), 13)
        worst = []
        for (g, s), d in dat.items():
            V = vq(self.tabs[g], s); cr = cr_q(self.tabs[g], s)
            for k in self.members(g):
                eD = d[mode][k][R] if R is not None else Fr(0)
                worst.append(((max(d['eIn'][k], eD) - cr * self.pat[k]) / V, (g, s, k)))
        worst.sort(reverse=True)
        return lp, rup(worst[0][0], 13), worst[:5]

    def env(self, mu, n, procs=11):
        """every entry's members' envelopes, cached"""
        os.makedirs(CACHE, exist_ok=True)
        path = os.path.join(CACHE, f"{self.key}_env_{mu.numerator}_{mu.denominator}_{n}.pkl")
        if os.path.exists(path):
            return pickle.load(open(path, 'rb'))
        keys = [(g, s) for g in range(self.ng) for s in self.reps]
        jobs = [(self.tabs[g], s, self.x, self.gam, self.famZ, self.D, self.Dl, self.members(g), mu, n) for g, s in keys]
        with Pool(procs) as p:
            res = p.map(rep_env, jobs, chunksize=4)
        out = dict(zip(keys, res))
        pickle.dump(out, open(path, 'wb'))
        return out

    def contractions_env(self, dat, env, R):
        """`lp`, and `lpi` with each member's envelope bound `eIn + λ^R · aZ` (rounded up to 13 digits)"""
        lp = rup(max(d['eE'] / vq(self.tabs[g], s) for (g, s), d in dat.items()), 13)
        worst = []
        for (g, s), d in dat.items():
            V = vq(self.tabs[g], s); cr = cr_q(self.tabs[g], s)
            for k in self.members(g):
                lam, aZ = env[(g, s)][k]
                eD = rup(d['eIn'][k] + lam ** R * aZ, 13)
                worst.append(((max(d['eIn'][k], eD) - cr * self.pat[k]) / V, (g, s, k)))
        worst.sort(reverse=True)
        return lp, rup(worst[0][0], 13), worst[:5]

    def wdata(self, mu=Fr(9, 10), n=40, procs=11):
        """every entry's data as the certificate computes it (`rep_w`), cached"""
        os.makedirs(CACHE, exist_ok=True)
        path = os.path.join(CACHE, f"{self.key}_w_{mu.numerator}_{mu.denominator}_{n}.pkl")
        if os.path.exists(path):
            return pickle.load(open(path, 'rb'))
        keys = [(g, s) for g in range(self.ng) for s in self.reps]
        jobs = [(self.tabs[g], s, self.x, self.gam, self.famZ, self.D, self.Dl, self.members(g), mu, n) for g, s in keys]
        with Pool(procs) as p:
            res = p.map(rep_w, jobs, chunksize=4)
        out = dict(zip(keys, res))
        pickle.dump(out, open(path, 'wb'))
        return out

    def contractions_w(self, wd, R):
        """`tabLpG` and `tabLpiG` for the certificate's data, with the delayed bounds after `R` steps"""
        lp = rup(max(d['eE'] / vq(self.tabs[g], s) for (g, s), d in wd.items()), 13)
        worst = []
        for (g, s), d in wd.items():
            V = vq(self.tabs[g], s); cr = cr_q(self.tabs[g], s)
            for k in self.members(g):
                lam, aZ = d['env'][k]
                eD = rup(d['eIn'][k] + lam ** R * aZ, 13)
                worst.append(((max(d['eIn'][k], eD) - cr * self.pat[k]) / V, (g, s, k)))
        worst.sort(reverse=True)
        return lp, rup(worst[0][0], 13), worst[:5]

    def index_dats(self):
        """the switching indices' data (0, 1, 2, 17)"""
        args = (self.c, self.z, Fr(1), Fr(1), self.tau)
        return [emitF.index_data(i, self.famZ, self.D, self.Dl, emitZ.ph_z(i, *args)) if emitF.is_sw(i)
                else dict(eE=Fr(0), eS=Fr(0), eIn=[]) for i in range(19)]

    def derive(self, lp, lpi, ccap, dats=None):
        """`SpecData.deriveLE` with `e2 · sU` and `Ccap = ccap(G)`"""
        dats = dats or self.index_dats()
        e, lr, b = emitF.derived(dats)
        e = list(e); e2 = e[2] * self.sU
        B = certE.weakest([m['B'] for m in self.fam])
        cfg = dict(Delta=self.Dl, k=self.depth, N=self.N, c=self.c, z=self.z, tau=self.tau)
        ee = list(e); ee[2] = e2
        rl = emitF.spec_rules(cfg, B, ee, lr, b, lpi, emitF.EPS)
        Lw, J, x, G, Gp, r, Tg, yy = (rl[v] for v in ['Lw', 'J', 'x', 'G', 'Gp', 'r', 'T', 'yy'])
        EL, PERIOD, D, N, k = certE.EL, certE.PERIOD, self.Dl, self.N, self.depth
        M = N + G + Gp + D + 2
        Ne = M // EL + 1
        nb = (EL - PERIOD - D - 3 - G + D) // (Tg + D)
        ne = (N + 2) // EL
        tgt = rup(powq.settle_q(powq.D_POW, D, B, e[17], self.tau, lp, e2, b, lr, self.c, lpi, x, yy, k, ne, nb,
                                ccap(G), N, G, Gp, J, Lw, r, Tg), 2)
        bx = rup(powq.band_q(powq.D_POW, powq.N_EXP, certE.tband_derived(self.T), self.T['delta'], PERIOD), 4)
        return dict(Lw=Lw, J=J, G=G, Gp=Gp, r=r, T=Tg, Ne=Ne, tgt=tgt, bx=bx, fin=rup(tgt + Ne * bx, 2))


if __name__ == "__main__":
    a = sys.argv[1:]
    cert = Cert(Fr(a[0]), Fr(a[1]), int(a[2]), int(a[3]), int(a[4]), a[5], int(a[6]), int(a[7]), int(a[8]),
                *(Fr(v) for v in a[9:16]), int(a[16]))
    Rd = int(a[17]); mode = a[18] if len(a) > 18 else 'grp'
    import time
    t0 = time.time()
    dat = cert.data(max(Rd, 40))
    print(f"data: {time.time() - t0:.0f}s, {len(dat)} entries")
    dats = cert.index_dats()
    for R in [None, 13, 16, 20, 24, 30, 40]:
        if R is not None and R > max(Rd, 40): continue
        for md in (['grp', 'own'] if R is not None else ['grp']):
            lp, lpi, worst = cert.contractions(dat, R, md)
            d = cert.derive(lp, lpi, (lambda G: G) if R is None else (lambda G, R=R: R), dats)
            print(f"R={R} {md}: lp={float(lp):.7f} lpi={float(lpi):.7f} G={d['G']} J={d['J']} tgt={float(d['tgt']):.3g} "
                  f"bx={float(d['bx']):.3g} fin={float(d['fin']):.3g}")
