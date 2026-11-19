"""Definitions shared by the scripts of SURVIVAL.md. Nothing here prints.

The lottery model of SURVIVAL.md, section 2. In each slot the honest stake that builds wins with
chance h = 1 - (1 - f)^x_h and the coalition wins with chance a = 1 - (1 - f)^x_a, all wins
independent. Slot 0 holds H0. tau_0 = 0 and tau_i is the first slot after tau_{i-1} + d that honest
stake wins (the greedy d-isolated honest wins, section 4). N(u) = #{i >= 1 : tau_i <= u},
A(t) = #{1 <= s <= t : the coalition wins s}, X(t) = A(t) - N(t - d).

Q(T)  = P(some t >= T has X(t) >= 0): the bound of Theorem 6.1 on the survival of review 9.3.
Q1(T) = P(some t >= T has X(t) >= 1): the strict version, used in section 9 from below.

Computation (section 7):
- the law of M, the all-time maximum of the walk with steps Y - 1 (Lemma 6.3), from below and from
  above by the Lindley recursion (Lemma 6.4), started at 0 and at the Lundberg bound;
- the forward recursion of (X'(t), phase) over slots (Lemma 6.5), with X'(t) = X(t) for t >= d;
- q(x, k), the chance of reaching the threshold from (x, k) (Lemma 6.6);
- the closed-form tail bound of Lemma 6.7.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for _var in ("NUMBA_CACHE_DIR", "TMPDIR", "JOBLIB_TEMP_FOLDER"):
    os.environ.setdefault(_var, os.path.join(HERE, ".cache"))
os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
sys.dont_write_bytecode = True

import numpy as np                                    # noqa: E402
from scipy.optimize import brentq, minimize_scalar   # noqa: E402
from scipy.stats import binom                        # noqa: E402

F = 1 / 30            # slot activation coefficient, protocol 102
EPS = 1e-9            # the target of review 9.4 and of Finality Floor, protocol 531
H = 3600              # slots in an hour (one slot is one second, protocol 106)
STUDY_SRC = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", "src"))   # tools/simulators/finality/src
REVIEW_DIR = os.path.normpath(os.path.join(HERE, "..", ".."))

# key, label, x_h, x_a, d, the review's w_B, its line in the review's out_08_buffer.txt
STATES = (
    ("none", "no disturbance, 10 s", 0.7, 0.3, 10, 12242, 14),
    ("late", "every honest block 15 s late", 0.7, 0.3, 15, 16579, 25),
    ("off", "a tenth of the honest stake offline, inference corrected, 10 s", 0.63 / 0.93, 0.3 / 0.93, 10, 17215, 36),
    ("defl", "deflated inference, 10 s", 1.0, 0.3 / 0.7, 10, 11126, 47),
    ("late_off", "15 s and a tenth offline, corrected (base pair)", 0.63 / 0.93, 0.3 / 0.93, 15, 24645, 58),
    ("late_defl", "15 s and a deflated inference (base pair)", 1.0, 0.3 / 0.7, 15, 18081, 69),
    ("off_defl", "a tenth offline and a deflated inference, 10 s (base pair)", 1.0, 0.3 / 0.63, 10, 16452, 80),
    ("off_b", "a tenth offline before the inference corrects, 10 s", 0.63, 0.3, 10, 17654, 113),
    ("late_off_b", "15 s and a tenth offline before the inference corrects", 0.63, 0.3, 15, 24471, 124),
)
STATE = {s[0]: s for s in STATES}

Y_MAX = 400           # support kept for the laws of Y and R_0
M_MAX = 600           # support kept for the law of M


def win(x: float, f: float = F) -> float:
    """1 - (1 - f)^x: the chance that a share x of D wins a slot (Lemma 2.1)."""
    return -math.expm1(x * math.log1p(-f))


def rates(x_h: float, x_a: float, f: float = F):
    return win(x_h, f), win(x_a, f)


def study_params(x_h: float, x_a: float):
    """The study's (f', alpha) with 1 - (1 - f')^alpha = a and 1 - (1 - f')^(1 - alpha) = h."""
    tot = x_h + x_a
    return -math.expm1(tot * math.log1p(-F)), x_a / tot


def geo_ratio(h: float, a: float) -> float:
    """r of Lemma 6.2: the coalition's wins in the slots up to the first honest win, not counting
    the slot of that win, are Geometric(r) on {0, 1, ...}."""
    return a * (1 - h) / (a * (1 - h) + h)


def _bin_geo(n_bin: int, a: float, r: float, size: int):
    """pmf of Bin(n_bin, a) + Geo(r) on 0..size-1, and the exact mass above size-1."""
    b = binom.pmf(np.arange(n_bin + 1), n_bin, a)
    g = (1 - r) * r ** np.arange(size)
    pmf = np.convolve(b, g)[:size]
    # P(sum >= size) = sum_j P(B = j) P(Geo >= size - j) = sum_j P(B = j) r^(size - j)
    tail = float(np.sum(b * r ** (size - np.arange(n_bin + 1))))
    return pmf, tail


def y_law(h, a, d, size=Y_MAX + 1):
    """Y, the coalition's wins in one gap of d + G slots: Bin(d + 1, a) + Geo(r) (Lemma 6.2)."""
    return _bin_geo(d + 1, a, geo_ratio(h, a), size)


def r0_law(h, a, d, size=Y_MAX + 1):
    """R_0, the coalition's wins from T + 1 to the slot before the next count, in phase 0:
    Bin(d, a) + Geo(r) (Lemma 6.6)."""
    return _bin_geo(d, a, geo_ratio(h, a), size)


def log_mgf_step(theta, h, a, d):
    """log E[exp(theta (Y - 1))]."""
    r = geo_ratio(h, a)
    return ((d + 1) * math.log1p(a * math.expm1(theta)) + math.log1p(-r)
            - math.log1p(-r * math.exp(theta)) - theta)


def theta_star(h, a, d):
    """The positive root of E[exp(theta (Y - 1))] = 1 (Lemma 6.4)."""
    r = geo_ratio(h, a)
    top = -math.log(r) - 1e-12
    return brentq(lambda t: log_mgf_step(t, h, a, d), 1e-9, top, xtol=1e-15, rtol=1e-15)


def max_law(h, a, d, m_max=M_MAX, tol=1e-12, check_to=300, max_iter=400_000):
    """P(M >= m) for m = 0..m_max, from below and from above (Lemma 6.4).

    Below: the Lindley recursion W <- (W + Y - 1)^+ from W = 0, mass leaving the support dropped.
    Above: the same recursion from P(W >= m) = exp(-theta m), theta just below theta*, with every
    mass that leaves the support kept in a state above every level. Returns (low, up, iterations)."""
    y, y_tail = y_law(h, a, d)
    th = theta_star(h, a, d) * (1 - 1e-9)
    lo = np.zeros(m_max + 1)
    lo[0] = 1.0
    up = -math.expm1(-th) * np.exp(-th * np.arange(m_max + 1))
    up_inf = math.exp(-th * (m_max + 1))

    def step(w):
        z = np.convolve(w, y)               # index j: W + Y = j
        new = np.empty(m_max + 1)
        new[0] = z[0] + z[1]                 # (W + Y - 1)^+ = 0
        new[1:] = z[2:m_max + 2]
        return new, float(z[m_max + 2:].sum())

    def tails(w, extra):
        return np.cumsum(w[::-1])[::-1] + extra

    it = 0
    for it in range(1, max_iter + 1):
        lo, _ = step(lo)
        new, over = step(up)
        up_inf = up_inf + over + float(up.sum()) * y_tail
        up = new
        if it % 200 == 0:
            tl, tu = tails(lo, 0.0), tails(up, up_inf)
            gap = np.max((tu[:check_to] - tl[:check_to]) / tu[:check_to])
            if gap <= tol:
                break
    return tails(lo, 0.0), tails(up, up_inf), it


def tail_fn(tail, upper=True):
    """m -> P(M >= m) from an array of tails, 1 for m <= 0. Beyond the array: from above, the last
    entry, which holds the mass kept above every level; from below, 0."""
    ext = np.append(tail, tail[-1] if upper else 0.0)

    def g(m):
        m = np.asarray(m)
        return np.where(m <= 0, 1.0, ext[np.clip(m, 0, ext.size - 1)])
    return g


def q_table(h, a, d, tail, x_lo, x_hi, thresh, upper=True):
    """q[x - x_lo, k] = P(some t >= T has X(t) >= thresh | X(T) = x, phase k) (Lemma 6.6):
    1 for x >= thresh, else P(R_k + M >= thresh - x) with R_k = Bin(k - 1, a) for k >= 1 and
    R_0 = Bin(d, a) + Geo(r). `tail` is the law of M from above (upper) or below."""
    tM = tail_fn(tail, upper)
    r0, r0_tail = r0_law(h, a, d)
    laws = [(r0, r0_tail if upper else 0.0)]
    for k in range(1, d + 1):
        laws.append((binom.pmf(np.arange(k), k - 1, a), 0.0))
    xs = np.arange(x_lo, x_hi + 1)
    q = np.ones((xs.size, d + 1))
    for k, (pmf, extra) in enumerate(laws):
        rr = np.arange(pmf.size)
        for i, x in enumerate(xs):
            if x >= thresh:
                continue
            s = thresh - x
            q[i, k] = min(1.0, float(np.sum(pmf * tM(s - rr))) + extra)
    return q


def qhat_table(h, a, d, tail, x_lo, x_hi, upper=True):
    """qhat[x - x_lo, k] = P(a later count has U >= 0 | X(T) = x, phase k, flag 0) (Lemma 6.6):
    1 for x >= 1, else P(Z_k + M >= 1 - x) with Z_k = Bin(k, a) for k >= 1 and Z_0 = Y."""
    tM = tail_fn(tail, upper)
    y, y_tail = y_law(h, a, d)
    laws = [(y, y_tail if upper else 0.0)]
    for k in range(1, d + 1):
        laws.append((binom.pmf(np.arange(k + 1), k, a), 0.0))
    xs = np.arange(x_lo, x_hi + 1)
    q = np.ones((xs.size, d + 1))
    for k, (pmf, extra) in enumerate(laws):
        rr = np.arange(pmf.size)
        for i, x in enumerate(xs):
            if x >= 1:
                continue
            q[i, k] = min(1.0, float(np.sum(pmf * tM(1 - x - rr))) + extra)
    return q


def forward_all(h, a, d, T_end, q0, q1, qh, x_lo, x_hi, upper=True):
    """For T = 0..T_end: Q(T) = sum P(X'(T) = x, k) q0, Q1(T) = sum P(X'(T) = x, k) q1, and
    Qhat(T) = P(flag 1) + sum P(X'(T) = x, k, flag 0) qh (Lemma 6.5 and 6.6).

    Phase k >= 1: a count falls k slots later; phase 0: none pending. X'(0) = 1 in phase d, flag 0.
    At a count the flag becomes [X >= 0], read after the coalition's win of that slot.
    upper: mass below x_lo is kept at x_lo, mass above x_hi goes to a state counted as success in
    all three. lower: mass that leaves [x_lo, x_hi] is dropped and counted as failure."""
    nx = x_hi - x_lo + 1
    P = [np.zeros((nx, d + 1)), np.zeros((nx, d + 1))]      # flag 0, flag 1
    P[0][1 - x_lo, d] = 1.0
    nonneg = (np.arange(x_lo, x_hi + 1) >= 0)
    over = 0.0
    out = np.zeros((3, T_end + 1))

    def coal(arr):
        nxt = (1 - a) * arr
        nxt[1:] += a * arr[:-1]
        return nxt, a * float(arr[-1].sum())

    def record(t):
        tot = P[0] + P[1]
        extra = over if upper else 0.0
        out[0, t] = float(np.sum(tot * q0)) + extra
        out[1, t] = float(np.sum(tot * q1)) + extra
        out[2, t] = float(P[1].sum()) + float(np.sum(P[0] * qh)) + extra

    record(0)
    for t in range(1, T_end + 1):
        just = np.zeros(nx)
        new = []
        for f in (0, 1):
            Pf = P[f]
            nf = np.empty_like(Pf)
            if d >= 2:
                nf[:, 1:d] = Pf[:, 2:]
            nf[:, d] = h * Pf[:, 0]
            nf[:, 0] = (1 - h) * Pf[:, 0]
            c = Pf[:, 1]
            just[:-1] += c[1:]
            if upper:
                just[0] += c[0]
            new.append(nf)
        for f in (0, 1):
            new[f], o = coal(new[f])
            if upper:
                over += o
        jn = (1 - a) * just
        jn[1:] += a * just[:-1]
        if upper:
            over += a * float(just[-1])
        new[0][:, 0] += np.where(nonneg, 0.0, jn)
        new[1][:, 0] += np.where(nonneg, jn, 0.0)
        P = new
        record(t)
    return out


def forward_snapshots(h, a, d, times, x_lo, x_hi, upper=True):
    """The chain of forward_all, stepped the same way, returning at each slot of `times` the law of
    the state: (P0, P1, over), with P0 and P1 the masses with flag 0 and 1 over (x - x_lo, phase), and
    over the mass counted as success from above (0 from below). Used for the split of section 9.2."""
    nx = x_hi - x_lo + 1
    P = [np.zeros((nx, d + 1)), np.zeros((nx, d + 1))]
    P[0][1 - x_lo, d] = 1.0
    nonneg = (np.arange(x_lo, x_hi + 1) >= 0)
    over = 0.0
    want = set(times)
    snaps = {}

    def coal(arr):
        nxt = (1 - a) * arr
        nxt[1:] += a * arr[:-1]
        return nxt, a * float(arr[-1].sum())

    for t in range(1, max(times) + 1):
        just = np.zeros(nx)
        new = []
        for f in (0, 1):
            Pf = P[f]
            nf = np.empty_like(Pf)
            if d >= 2:
                nf[:, 1:d] = Pf[:, 2:]
            nf[:, d] = h * Pf[:, 0]
            nf[:, 0] = (1 - h) * Pf[:, 0]
            c = Pf[:, 1]
            just[:-1] += c[1:]
            if upper:
                just[0] += c[0]
            new.append(nf)
        for f in (0, 1):
            new[f], o = coal(new[f])
            if upper:
                over += o
        jn = (1 - a) * just
        jn[1:] += a * just[:-1]
        if upper:
            over += a * float(just[-1])
        new[0][:, 0] += np.where(nonneg, 0.0, jn)
        new[1][:, 0] += np.where(nonneg, jn, 0.0)
        P = new
        if t in want:
            snaps[t] = (P[0].copy(), P[1].copy(), over if upper else 0.0)
    return snaps


def forward(h, a, d, T_end, tables, x_lo, x_hi, upper=True):
    """sum_{x, k} P(X'(T) = x, phase k) q[x, k] for each table q, for T = 0..T_end (Lemma 6.5).

    Phase k >= 1: a count falls k slots later; phase 0: no count pending. X'(0) = 1 in phase d.
    upper: mass below x_lo is kept at x_lo, mass above x_hi goes to a state counted as success.
    lower: mass that leaves [x_lo, x_hi] is dropped and counted as failure."""
    nx = x_hi - x_lo + 1
    P = np.zeros((nx, d + 1))
    P[1 - x_lo, d] = 1.0
    over = 0.0
    out = np.zeros((len(tables), T_end + 1))
    for i, q in enumerate(tables):
        out[i, 0] = float(np.sum(P * q))
    for t in range(1, T_end + 1):
        new = np.empty_like(P)
        if d >= 2:
            new[:, 1:d] = P[:, 2:]
        new[:, d] = h * P[:, 0]
        new[:, 0] = (1 - h) * P[:, 0]
        c = P[:, 1]
        new[:-1, 0] += c[1:]
        if upper:
            new[0, 0] += c[0]
        nxt = (1 - a) * new
        nxt[1:] += a * new[:-1]
        if upper:
            over += a * float(new[-1].sum())
        P = nxt
        for i, q in enumerate(tables):
            out[i, t] = float(np.sum(P * q)) + (over if upper else 0.0)
    return out


def chernoff(h, a, d):
    """Lemma 6.7: Q(T) <= C lambda^T for T >= d. Returns theta, rho, lambda, C."""
    def rho(th):
        return brentq(lambda r: r ** d * (r - 1 + h) - h * math.exp(-th), 1 - h, 1.0,
                      xtol=1e-16, rtol=1e-15)

    def lam(th):
        return (1 - a + a * math.exp(th)) * rho(th)

    res = minimize_scalar(lam, bounds=(1e-6, 3.0), method="bounded", options={"xatol": 1e-10})
    th = float(res.x)
    rh = rho(th)
    e_min = min(1.0, math.exp(-th) / rh)
    C = rh ** (-d) / e_min
    return th, rh, lam(th), C


def ranges(h, a, d):
    """The kept range of X: from below x_lo the chance of ever reaching 0 is below about exp(-100),
    and x_hi is reached with a chance below about exp(-100) (Lemma 6.4: P(M >= m) <= exp(-theta* m))."""
    th = theta_star(h, a, d)
    return -int(math.ceil(100 / th)), int(math.ceil(100 / th)) + 1


def survival_curves(h, a, d, T_end, law=None, lower=False):
    """Q(T), Q1(T) and Qhat(T) from above (and, with lower, from below) for T = 0..T_end."""
    if law is None:
        law = max_law(h, a, d)
    low, up, _ = law
    x_lo, x_hi = ranges(h, a, d)
    tabs = [q_table(h, a, d, up, x_lo, x_hi, 0, upper=True),
            q_table(h, a, d, up, x_lo, x_hi, 1, upper=True),
            qhat_table(h, a, d, up, x_lo, x_hi, upper=True)]
    Q, Q1, Qh = forward_all(h, a, d, T_end, *tabs, x_lo, x_hi, upper=True)
    res = {"Q": Q, "Q1": Q1, "Qhat": Qh, "x_lo": x_lo, "x_hi": x_hi}
    if lower:
        tabs = [q_table(h, a, d, low, x_lo, x_hi, 0, upper=False),
                q_table(h, a, d, low, x_lo, x_hi, 1, upper=False),
                qhat_table(h, a, d, low, x_lo, x_hi, upper=False)]
        Ql, Q1l, Qhl = forward_all(h, a, d, T_end, *tabs, x_lo, x_hi, upper=False)
        res.update(Q_low=Ql, Q1_low=Q1l, Qhat_low=Qhl)
    return res


def least_w(h, Q, d, tail_C, tail_lam, eps=EPS):
    """The least w >= d with h * sum_{T >= w} Q(T) <= eps, the sum taken exactly up to the end of
    Q and bounded by Lemma 6.7 beyond it. Returns w and the function S(w) = sum_{T >= w} Q(T)."""
    T_end = Q.size - 1
    tail = tail_C * tail_lam ** (T_end + 1) / (1 - tail_lam)
    S = np.cumsum(Q[::-1])[::-1] + tail
    ok = np.nonzero((h * S <= eps) & (np.arange(Q.size) >= d))[0]
    return (int(ok[0]) if ok.size else None), S, tail
