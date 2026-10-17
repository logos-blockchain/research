"""A member's band: the slot law's bounds for an honest exponent in [ylo, yhi] and an adversarial one at
most ahi, as `memberOfQ` (`Prob/CertGen.lean`) computes them, with the specification's lottery
constants."""
from fractions import Fraction as Fr
from certnum import rup, rdn

P_SPEC = 0x30644E72E131A029B85045B68181585D2833E84879B9709143E1F593F0000001
T0 = 0x1a3fb997fd5838f2a1585ee090a95c88129ab25cc4d2e2d28f1a95f81d85465
LAM = Fr(T0, P_SPEC)
ETA, ZETA = Fr(1, 10 ** 70), Fr(1, 10 ** 16)

def errLo(Y): return 2 * (ETA * Y ** 2 + ZETA)
def errHi(Y): return 2 * (Fr(2, 9) * Y ** 3 + ETA * Y ** 2 + ZETA)
def Elo(y): return 1 - y + y * y / 2 - Fr(2, 9) * y ** 3
def Ehi(y): return 1 - y + y * y / 2

def member_band(ylo, yhi, ahi, d=13):
    P0lo = Elo(yhi) * (1 - errLo(yhi)); P0hi = Ehi(ylo) * (1 + 2 * errHi(yhi))
    amax = rup(1 - Elo(ahi) * (1 - errLo(ahi)), d)
    hhi = rup(1 - P0lo, d); hlo = rdn(1 - P0hi, d)
    return dict(hhi=hhi, hlo=hlo, amax=amax, alo=amax, hahi=rup(hhi * amax, d), halo=rdn(hlo * amax, d),
                slo=rdn(P0lo * (ylo - errHi(yhi)) * (1 - amax), d), hnlo=rdn(hlo * (1 - amax), d),
                elo=rdn(P0lo * (1 - amax), d))
