"""Generate a Lean certificate for settleEps (Cryptarchia/Prob/Tail.lean) with the current ColdCert."""
import math, sys, json
from fractions import Fraction as F
from certnum import rup, rdn, band, burst_u, check_burst, phaseBound

def lean_q(x):
    x = F(x)
    if x.denominator == 1: return f"({x.numerator} : ℝ)"
    return f"({x.numerator} / {x.denominator} : ℝ)"

def chain(beta, n, upper, d=14, name='ch', hbeta='hβ'):
    """Lean lines proving beta^n <= P (upper) or P <= beta^n; returns (lines, P)."""
    beta = F(beta)
    bits = bin(n)[2:]
    lines = []
    m = 1
    P = rup(beta, d) if upper else rdn(beta, d)
    if upper:
        lines.append(f"  have {name}0 : {lean_q(beta)} ^ 1 ≤ {lean_q(P)} := pow_one_le (by norm_num)")
    else:
        lines.append(f"  have {name}0 : {lean_q(P)} ≤ {lean_q(beta)} ^ 1 := pow_one_ge (by norm_num)")
    for i, bch in enumerate(bits[1:], 1):
        b = int(bch)
        m2 = 2 * m + b
        val = P * P * beta ** b
        P2 = rup(val, d) if upper else rdn(val, d)
        if upper:
            lines.append(f"  have {name}{i} : {lean_q(beta)} ^ {m2} ≤ {lean_q(P2)} := by\n"
                         f"    have h := pow_bit_le (by norm_num) {name}{i-1} {b} (P' := {lean_q(P2)}) (by norm_num)\n"
                         f"    rwa [show 2 * {m} + {b} = {m2} from rfl] at h")
        else:
            lines.append(f"  have {name}{i} : {lean_q(P2)} ≤ {lean_q(beta)} ^ {m2} := by\n"
                         f"    have h := pow_bit_ge (by norm_num) (by norm_num) {name}{i-1} {b} (P' := {lean_q(P2)}) (by norm_num)\n"
                         f"    rwa [show 2 * {m} + {b} = {m2} from rfl] at h")
        m, P = m2, P2
    assert m == n
    return lines, P, f"{name}{len(bits)-1}"

def ufun(name, U, D):
    s = f"noncomputable def {name} : ℕ → ℝ\n"
    for q in range(D):
        s += f"  | {q} => {lean_q(U[q])}\n"
    s += "  | _ => 1\n"
    return s

def burst_thm(name, uname, D, x, th):
    xs = x if isinstance(x, str) else lean_q(x)
    return (f"theorem {name} : BurstSol B {D} {xs} {lean_q(th)} {uname} where\n"
            f"  one_le := by intro q hq; interval_cases q <;> norm_num [{uname}]\n"
            f"  le_zero := by intro q hq; interval_cases q <;> norm_num [{uname}]\n"
            f"  step := by intro q hq; interval_cases q <;> norm_num [{uname}, B]\n")

def generate(cfg):
    f = F(cfg['fNum'], cfg['fDen']); beta = cfg['beta']; D = cfg['Delta']; k = cfg['k']
    N, G, Lw, r, T = cfg['N'], cfg['G'], cfg['Lw'], cfg['r'], cfg['T']
    W = Lw - 2 * G; M = N + G + D + 2
    c, z, s, th, x, yy = (F(cfg[v]) for v in ['c', 'z', 's', 'theta', 'x', 'yy'])
    B = band(float(f), beta)
    u1 = burst_u(B, D, float(c), float(th)); u2 = burst_u(B, D, float(c * z), float(th))
    u3 = burst_u(B, D, float(z), 1.0); u4 = burst_u(B, D, float(c), 1.0)
    # exact check of the burst solutions with the rounded parameters
    for U, xx, tt in [(u1, c, th), (u2, c * z, th), (u3, z, F(1)), (u4, c, F(1))]:
        assert check_burst(B, D, xx, tt, U)
    pat = th ** (D + 1) * B['slo'] * B['elo'] ** D
    w1 = phaseBound(B, c, th, 1 / c, u1[0])
    w0 = phaseBound(B, c, th, F(1), u1[0]) - (1 - s / z) * pat
    cd = phaseBound(B, c * z, th, 1 / s, u2[0]) - (1 / s - 1 / z) * pat
    lp = rup(max(w1, w0, cd))
    lr = rup(phaseBound(B, c, F(1), 1 / c, u4[0])); b = rup(phaseBound(B, c, F(1), F(1), u4[0]))
    mz = rup(phaseBound(B, z, F(1), F(1), u3[0]))
    assert lp < 1 and lr < 1 and b >= 1 and s <= z, (float(lp), float(lr), float(b))
    out = {}
    lines = []
    # T2: theta^W >= R
    l2, R, h2 = chain(th, W, False, name='tw')
    stat = 1 + (b - 1) / (1 - lr)
    T2 = (N + 1) * mz / (R * (1 - lp)) * stat
    # T1
    base1 = 1 - (1 - B['hhi']) ** D
    T1 = (N + 1) * base1 ** (G // D)
    # T3: (1+(x-1)(1-elo))^Lw / x^(k+1)
    base3 = 1 + (x - 1) * (1 - B['elo'])
    l3a, U3, h3a = chain(base3, Lw, True, name='wa')
    l3b, L3, h3b = chain(x, k + 1, False, name='wb')
    T3 = (N + 1) * U3 / L3
    # T4
    l4, L4, h4 = chain(c, r + 1, False, name='rc')
    T4 = (N + G + 1) * stat / L4
    # T5
    epl = cfg['epochLength']; nonce = cfg['nonceOffset']
    grow = epl - nonce - D - 3 - G
    nbD = (grow + D) // (T + D)
    nEp = (N + 2) // epl
    PT = 1 - (1 - B['hlo']) ** T
    base5 = 1 + (yy - 1) * PT
    l5a, U5, h5a = chain(base5, nbD, True, name='da')
    l5b, L5, h5b = chain(yy, k + r, False, name='db')
    T5 = nEp * U5 / L5
    tot = T1 + T2 + T3 + T4 + T5
    return dict(B=B, u=(u1, u2, u3, u4), lp=lp, lr=lr, b=b, mz=mz, W=W, M=M, R=R, T=(T1, T2, T3, T4, T5),
                total=tot, chains=(l2, l3a, l3b, l4, l5a, l5b), hyp=(h2, h3a, h3b, h4, h5a, h5b),
                bases=(base1, base3, base5, PT), nbD=nbD, nEp=nEp, U3=U3, L3=L3, L4=L4, U5=U5, L5=L5)

if __name__ == "__main__":
    cfg = json.loads(sys.argv[1])
    g = generate(cfg)
    from certnum import flog10
    print('terms log10 (floor):', [flog10(t) if t > 0 else None for t in g['T']], 'total', flog10(g['total']))
    print('lp', float(g['lp']), 'lr', float(g['lr']), 'b', float(g['b']), 'mz', float(g['mz']))
