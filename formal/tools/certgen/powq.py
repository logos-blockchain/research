"""Mirrors of `Cryptarchia/Prob/PowQ.lean`: powers by binary powering rounded outward to `d`
significant digits, and the settlement and band bounds computed with them. The generator uses
them to check that the bounds the kernel computes stay below a certificate's targets."""
from fractions import Fraction as Fr
from certnum import rup, rdn

D_POW = 14       # digits the certificates round powers to
N_EXP = 4096     # the exponent `n` of `exp (-a) ≤ 1 / (1 + a / n) ^ n`


def pow_up(d, x, n, f=64):
    """`powUpF`"""
    if f == 0: return Fr(x) ** n
    if n == 0: return Fr(1)
    y = pow_up(d, x, n // 2, f - 1)
    return rup(y * y * (x if n % 2 == 1 else 1), d)


def pow_dn(d, x, n, f=64):
    """`powDnF`"""
    if f == 0: return Fr(x) ** n
    if n == 0: return Fr(1)
    y = pow_dn(d, x, n // 2, f - 1)
    return rdn(y * y * (x if n % 2 == 1 else 1), d)


def settle_q(d, Dl, B, e17, tau, lp, e2, b, lr, c, lpi, x, yy, k, ne, nb, Ccap, N, G, Gp, J, Lw, r, T):
    """`settleEps3EQ`, with its sign checks (`settleChkQ`)"""
    F = 1 + (b - 1) / (1 - lr)
    pt = 1 - (1 - B['hhi']) ** T if 1 <= yy else 1 - (1 - B['hlo']) ** T
    b1, b5, b7 = 1 - (1 - B['hhi']) ** Dl, 1 + (x - 1) * (1 - B['elo']), 1 + (yy - 1) * pt
    dt, dx, dc, dy = pow_dn(d, tau, Lw + 1), pow_dn(d, x, k + 1), pow_dn(d, c, r + 1), pow_dn(d, yy, k + r)
    assert all(v >= 0 for v in (b1, 1 - B['hlo'], e17, lpi, lp / lpi, e2, F, b5, b7, yy, tau, x, c))
    assert all(v > 0 for v in (dt, dx, dc, dy))
    return ((N + Gp + 1) * pow_up(d, b1, G // Dl) + (N + 1) * pow_up(d, 1 - B['hlo'], Gp) +
            (N + Gp + 1) * (pow_up(d, e17, J + 1) / dt) +
            (N + Gp + 1) * (pow_up(d, lpi, J) * pow_up(d, lp / lpi, Ccap) * e2 * F) +
            (N + 1) * (pow_up(d, b5, Lw) / dx) + (N + G + 1) * (F / dc) + ne * (pow_up(d, b7, nb) / dy))


def band_q(d, n, dv, delta, P):
    """`bandEpsQ`, with its sign checks (`bandChkQ`): `dv` the band's derived constants"""
    m = (P - 1) * dv['ylo'] * dv['clo']
    a1 = m * delta ** 2 / 2; a2 = m * delta ** 2 * (Fr(1, 2) - Fr(2, 9) * delta)
    q1, q2 = pow_dn(d, 1 + a1 / n, n), pow_dn(d, 1 + a2 / n, n)
    assert a1 >= 0 and a2 >= 0 and q1 > 0 and q2 > 0
    return 1 / q1 + 1 / q2
