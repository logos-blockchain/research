"""Exact-rational evaluation of the Lean certificate conditions (current ColdCert)."""
from fractions import Fraction as F
import math

def flog10(x):
    """floor(log10(x)) for a positive Fraction, exactly"""
    n, dd = x.numerator, x.denominator
    e = len(str(n)) - len(str(dd))
    if F(10) ** e > x: e -= 1
    if F(10) ** (e + 1) <= x: e += 1
    return e

def rup(x, d=12):
    """round a positive float/Fraction up to d significant digits, as a Fraction"""
    x = F(x)
    if x == 0: return F(0)
    e = flog10(x) - d + 1
    q = F(10) ** e
    return (x / q).__ceil__() * q
def rdn(x, d=12):
    x = F(x)
    if x == 0: return F(0)
    e = flog10(x) - d + 1
    q = F(10) ** e
    return (x / q).__floor__() * q

def band(f, beta, d=12):
    lam = -math.log(1 - f); rh = (1 - beta) * lam
    h = 1 - math.exp(-rh); p1 = rh * math.exp(-rh); a = 1 - (1 - f) ** beta
    # conservative rounding (tiny relative slack 1e-9 covers float error)
    s = 1e-9
    return dict(hhi=rup(h * (1 + s), d), hlo=rdn(h * (1 - s), d), amax=rup(a * (1 + s), d),
                hahi=rup(h * a * (1 + s), d), slo=rdn(p1 * (1 - a) * (1 - s), d),
                hnlo=rdn(h * (1 - a) * (1 - s), d), elo=rdn((1 - h) * (1 - a) * (1 - s), d))

def burst_u(B, D, x, th, d=12):
    """minimal burst solution (floats), rounded up; returns list u[0..D] (u[D] = 1) as Fractions, verified."""
    m = 1 + float(B['amax']) * (x - 1); xh = float(B['hhi']) + (x - 1) * float(B['hahi'])
    al, be = [0.0] * (D + 1), [0.0] * (D + 1)
    al[D], be[D] = 1.0, 0.0
    for q in range(D - 1, -1, -1):
        al[q] = th * (m - xh) * al[q + 1]
        be[q] = th * ((m - xh) * be[q + 1] + xh)
    u0 = al[0] / (1 - be[0])
    u = [al[q] + be[q] * u0 for q in range(D + 1)]
    u[D] = 1.0
    for bump in [1e-10, 1e-9, 1e-8, 1e-7, 1e-6]:
        U = [rup(v * (1 + bump * (D + 1 - q)), d) for q, v in enumerate(u)]
        U[D] = F(1)
        if check_burst(B, D, F(x), F(th), U): return U
    raise Exception('burst solution failed')

def check_burst(B, D, x, th, U):
    m = 1 + B['amax'] * (x - 1); xh = B['hhi'] + (x - 1) * B['hahi']
    for q in range(D + 1):
        if U[q] < 1 or U[q] > U[0]: return False
    for q in range(D):
        if th * (m * U[q + 1] + (U[0] - U[q + 1]) * xh) > U[q]: return False
    return True

def phaseBound(B, x, th, y, u0):
    k = y * u0 - 1
    coef = (B['hhi'] + (x - 1) * B['hahi']) if 1 <= y * u0 else B['hlo']
    return th * ((1 + B['amax'] * (x - 1)) + k * coef)
