"""Constants and exact distributions for GENESIS.md.

Constants are the specification's, read with git from the worktree Bedrock-RFC-Slot-Finality of
logos-lips (`git show <ref>:docs/blockchain/raw/<path>`), refs 7f3cf149 (latest #533) and ded1d4c6
(its base). Line numbers are those printed by `git show`.

The formulas are the ones GENESIS.md proves:
  - N(m): the largest set of honest slots among m consecutive slots with gaps of at least Delta + 1
    (statement 4.2). P(N >= n) = P(Bin(m - (n - 1) Delta, p_h) >= n).
  - M: the all-time maximum of the process Y of statement 5.3, started at Bin(L0, p_a).
    Its tail is bounded above by the exact solution of the hitting problem on a strip, with
    Lundberg's bound as the boundary value below the strip (statement 5.4).
  - P1(x) = P(M_pre + Z_x + M_post >= 0) (statement 5.5).
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from scipy import optimize, sparse, special, stats
from scipy.sparse.linalg import spsolve

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ.setdefault("NUMBA_CACHE_DIR", os.path.join(HERE, ".cache"))
FINALITY_SRC = os.path.normpath(os.path.join(HERE, "..", "..", "..", "..", "src"))   # tools/simulators/finality/src

# --- cryptarchia-v1-protocol.md, Constants (7f3cf149 lines 102-110; ded1d4c6 one lower) ----------
F = 1 / 30                      # f, line 102
K_SEC = 2160                    # k, line 103
U_SLOTS = 64_800                # floor(k/f), the unit of the Epoch Schedule, lines 153-159
K_CASES = {"10 h (#533, 7f3cf149)": 36_000, "18 h (base, ded1d4c6)": 64_800}   # line 104 / 103
EPOCH = 10 * U_SLOTS            # line 159
GAP = 4 * U_SLOTS               # Lottery Constants Finalization, line 155: cut-off to next epoch
W_UNCLE = 360                   # W f^-1, line 109
# --- fork-choice.md, Definitions, line 80 (identical at both refs) -----------------------------
S_GEN = K_SEC * 30 // 4         # floor(k/(4f)) = 16,200
# --- cryptarchia-v1-bootstr-sync.md, Constants, line 110 (identical at both refs) -------------
T_OFFLINE = 20 * 60             # 1,200 slots
# --- targets of the K row (protocol line 104) and T_M (blend-protocol.md line 481) ------------
DELTAS = (10, 15)
ALPHAS = (0.30, 1 / 3)
EPS = 1e-9
H = 3600                        # slots in an hour (slot = 1 s, protocol line 106)
YEAR = 365 * 24 * H             # slots in a year


def p_of(share: float, f: float = F) -> float:
    """Chance per slot that stake of the given share of D wins it: 1 - (1 - f)^share."""
    return -math.expm1(share * math.log1p(-f))


def shortfall(share: float, f: float = F) -> float:
    """delta = 1 - q / (1 - e^-y), y = -ln(1 - f) share: the relative shortfall of the circuit's
    second-order threshold q = y - y^2/2 (statement 4.4) for one note that holds the given share of D,
    against 1 - (1 - f)^share. It grows with the note's value, so it bounds every note of that stake."""
    y = -math.log1p(-f) * share
    return 1.0 - (y - y * y / 2) / -math.expm1(-y)


def pct(a: float) -> str:
    return "a third" if abs(a - 1 / 3) < 1e-12 else f"{100 * a:g} %"


# ------------------------------------------------------------------------------------------------
# N(m): the greedy count of honest slots with gaps of at least Delta + 1 (statement 4.2)
# ------------------------------------------------------------------------------------------------
def binom_logcdf(k, n, p: float) -> np.ndarray:
    """log P(Bin(n, p) <= k), elementwise. Where scipy underflows it returns -inf: such a term is
    below exp(-745) and does not change any sum below."""
    with np.errstate(divide="ignore"):
        out = np.asarray(stats.binom.logcdf(k, n, p), dtype=float)
    return np.where(np.isnan(out), -np.inf, out)


def binom_logsf(k, n, p: float) -> np.ndarray:
    """log P(Bin(n, p) > k), elementwise; -inf where scipy underflows, as for binom_logcdf."""
    with np.errstate(divide="ignore"):
        out = np.asarray(stats.binom.logsf(k, n, p), dtype=float)
    return np.where(np.isnan(out), -np.inf, out)


def log_pmf_greedy(m: int, p: float, delta: int) -> np.ndarray:
    """log P(N(m) = n) for n = 0..m. N(m) >= n iff Bin(m - (n - 1) delta, p) >= n.

    The mass is taken as a difference of lower tails where P(N <= n) < 1/2 and of upper tails
    elsewhere, so that no difference cancels. Far tails are summed in log space."""
    if m <= 0:
        out = np.full(1, 0.0)
        return out
    # beyond n_top the chance is below exp(-700) relative to the mode; P(N >= n) needs
    # m - (n - 1) delta >= n, so n <= (m + delta) / (delta + 1)
    n_feas = (m + delta) // (delta + 1)
    n = np.arange(n_feas + 2)
    trials_ge = m - (n - 1) * delta            # P(N >= n) = P(Bin(trials_ge, p) >= n), n >= 1
    log_ge = np.full(n.size, -np.inf)
    log_ge[0] = 0.0
    ok = (n >= 1) & (trials_ge >= n)
    log_ge[ok] = binom_logsf(n[ok] - 1, trials_ge[ok], p)
    # P(N <= n) = 1 - P(N >= n + 1) = P(Bin(m - n delta, p) <= n)
    trials_le = m - n * delta
    log_le = np.zeros(n.size)                  # where Bin trials < n + 1, N <= n surely
    ok = trials_le >= n + 1
    log_le[ok] = binom_logcdf(n[ok], trials_le[ok], p)
    log_le_prev = np.concatenate(([-np.inf], log_le[:-1]))
    with np.errstate(divide="ignore", invalid="ignore"):
        upper = log_ge[:-1] + np.log1p(-np.exp(log_ge[1:] - log_ge[:-1]))
        diff = np.where(np.isneginf(log_le_prev[:-1]), -np.inf, log_le_prev[:-1] - log_le[:-1])
        lower = log_le[:-1] + np.log1p(-np.exp(diff))
    lower = np.where(np.isneginf(log_le[:-1]), -np.inf, lower)
    upper = np.where(np.isneginf(log_ge[:-1]), -np.inf, upper)
    use_lower = log_le[:-1] < math.log(0.5)
    out = np.where(use_lower, lower, upper)
    full = np.full(m + 1, -np.inf)
    k = min(m + 1, out.size)
    full[:k] = out[:k]
    return full


def pmf_greedy_dp(m: int, p: float, delta: int) -> np.ndarray:
    """The same pmf by a slot-by-slot dynamic programme, for checks at small m."""
    # state: (count, dead) ; dead = slots left in which an honest win does not count
    nmax = m + 1
    cur = np.zeros((nmax + 1, delta + 1))
    cur[0, 0] = 1.0
    for _ in range(m):
        nxt = np.zeros_like(cur)
        # dead > 0: decrement, nothing counts
        nxt[:, : delta] += cur[:, 1:]
        # dead == 0: win w.p. p -> count + 1, dead = delta; else stay
        nxt[1:, delta] += cur[:-1, 0] * p
        nxt[:, 0] += cur[:, 0] * (1 - p)
        cur = nxt
    return cur.sum(axis=1)[: m + 1]


# ------------------------------------------------------------------------------------------------
# M: the all-time maximum of Y (statements 5.3 and 5.4)
# ------------------------------------------------------------------------------------------------
def theta_star(pa: float, ph: float, delta: int) -> float:
    """The positive root of E[exp(theta xi)] = 1 for a cycle increment xi = Bin(G + delta, pa) - 1,
    G ~ Geometric(ph) on {1, 2, ...} (statement 5.4)."""
    def log_mgf(th: float) -> float:
        q = 1 - pa + pa * math.exp(th)
        if (1 - ph) * q >= 1:
            return math.inf
        return -th + (delta + 1) * math.log(q) + math.log(ph) - math.log(1 - (1 - ph) * q)
    drift = pa * (1 / ph + delta) - 1
    if drift >= 0:
        raise ValueError("no negative drift")
    hi = 1e-6
    while log_mgf(hi) < 0:
        hi *= 2
        if hi > 50:
            raise ValueError("no root")
    return optimize.brentq(log_mgf, hi / 2 if log_mgf(hi / 2) < 0 else 1e-9, hi, xtol=1e-14)


def hit_zero_upper(pa: float, ph: float, delta: int, depth: int = 400) -> tuple[np.ndarray, float]:
    """phi[d, c] >= P(Y ever reaches 0 | Y = -d, dead = c) for d = 1..depth, c = 0..delta.

    Y moves each step by +a - eta: a ~ Bernoulli(pa); eta = 1 iff dead = 0 and an independent
    Bernoulli(ph) is 1, after which dead = delta; otherwise dead decreases to 0. Exact solution of the
    hitting problem on the strip -depth <= Y <= -1, with the boundary value
    exp(-theta*(d - 1)) q*^c for d > depth, which bounds the true value (statement 5.4). Returns
    phi (index d - 1) and theta*."""
    th = theta_star(pa, ph, delta)
    qs = 1 - pa + pa * math.exp(th)
    nd, nc = depth, delta + 1
    idx = lambda d, c: (d - 1) * nc + c          # noqa: E731
    rows, cols, vals = [], [], []
    rhs = np.zeros(nd * nc)

    def bound(d: int, c: int) -> float:
        return min(1.0, math.exp(-th * (d - 1)) * qs ** c)

    for d in range(1, nd + 1):
        for c in range(nc):
            i = idx(d, c)
            rows.append(i); cols.append(i); vals.append(1.0)
            if c == 0:
                moves = [(+1, 0, pa * (1 - ph)), (0, delta, pa * ph), (0, 0, (1 - pa) * (1 - ph)),
                         (-1, delta, (1 - pa) * ph)]
            else:
                moves = [(+1, c - 1, pa), (0, c - 1, 1 - pa)]
            for dy, c2, pr in moves:
                d2 = d - dy                      # Y = -d moves to -d + dy
                if d2 <= 0:
                    rhs[i] += pr
                elif d2 > nd:
                    rhs[i] += pr * bound(d2, c2)
                else:
                    rows.append(i); cols.append(idx(d2, c2)); vals.append(-pr)
    A = sparse.csr_matrix((vals, (rows, cols)), shape=(nd * nc, nd * nc))
    sol = spsolve(A.tocsc(), rhs)
    phi = np.maximum(sol.reshape(nd, nc), 0.0)
    # the solution must not exceed the Lundberg bound of the same states (a check of the solve)
    return phi, th


def max_tail(pa: float, ph: float, delta: int, l0: int, m_max: int = 120,
             depth: int = 400) -> np.ndarray:
    """T[m] >= P(M >= m), m = 0..m_max, for M = sup_v Y_v with Y_0 ~ Bin(l0, pa) and dead = 0.
    T is made non-increasing; T[0] = 1."""
    phi, _ = hit_zero_upper(pa, ph, delta, depth)
    y0 = np.arange(l0 + 1)
    w0 = stats.binom.pmf(y0, l0, pa)
    T = np.ones(m_max + 1)
    for m in range(1, m_max + 1):
        tot = 0.0
        for y, w in zip(y0, w0):
            d = m - y                            # need to climb from y to m: start at -d
            tot += w * (1.0 if d <= 0 else (phi[d - 1, 0] if d <= depth else 0.0))
        T[m] = min(1.0, tot)
    return np.minimum.accumulate(T)


def tail_to_pmf(T: np.ndarray) -> np.ndarray:
    """A pmf on 0..len(T)-1 plus an atom at infinity (last entry) that dominates the tail T."""
    pmf = np.empty(len(T) + 1)
    pmf[:-2] = T[:-1] - T[1:]
    pmf[-2] = 0.0
    pmf[-1] = T[-1]                              # mass at +infinity
    return pmf


# ------------------------------------------------------------------------------------------------
# P1(x) = P(M_pre + Z_x + M_post >= 0)  (statement 5.5)
# ------------------------------------------------------------------------------------------------
def log_z_ge(x: int, pa: float, ph: float, delta: int, kmax: int) -> np.ndarray:
    """log P(Z_x >= -k), k = 0..kmax, Z_x = Bin(x, pa) - N(x - delta), independent."""
    lpn = log_pmf_greedy(x - delta, ph, delta)
    n = np.arange(len(lpn))
    out = np.empty(kmax + 1)
    keep = np.isfinite(lpn)
    n, lpn = n[keep], lpn[keep]
    for k in range(kmax + 1):
        thr = n - k                              # need A >= n - k
        la = np.where(thr <= 0, 0.0, binom_logsf(np.maximum(thr, 1) - 1, x, pa))
        out[k] = special.logsumexp(lpn + la)
    return np.minimum(out, 0.0)


def log_joint_greedy_tau(m: int, p: float, delta: int) -> np.ndarray:
    """L[n, t] = log P(N(m) = n, tau = t) for the greedy choice of statement 5.2 (1) on m slots, where
    tau is the number of slots from its last slot to the end of the interval, and t = delta + 1 stands
    for tau >= delta + 1 or no slot at all (statement 6.2). With T_n the slot of the n-th pick:
      t <= delta, n >= 1:  P(T_n = m - t)                   = p P(Bin(m - t - (n - 1) delta - 1, p) = n - 1);
      t = delta + 1:       P(T_n <= m - delta - 1 < m < T_(n+1)) = (1 - p) P(Bin(m - n delta - 1, p) = n).
    For t <= delta no later pick fits, since T_(n+1) >= T_n + delta + 1."""
    n_feas = max(0, (m + delta) // (delta + 1))
    n = np.arange(n_feas + 2)
    out = np.full((n.size, delta + 2), -np.inf)
    lp, lq = math.log(p), math.log1p(-p)
    with np.errstate(divide="ignore"):
        for t in range(delta + 1):
            trials = m - t - (n - 1) * delta - 1
            ok = (n >= 1) & (trials >= n - 1)
            if ok.any():
                out[ok, t] = lp + stats.binom.logpmf(n[ok] - 1, trials[ok], p)
        trials = m - n * delta - 1
        ok = trials >= n
        if ok.any():
            out[ok, delta + 1] = lq + stats.binom.logpmf(n[ok], trials[ok], p)
    return out


def joint_step(pa: float, ph: float) -> tuple[float, float, float, float]:
    """(P(fork wins, honest wins), P(fork, not honest), P(not fork, honest), P(neither)) for one slot when
    the coalition's and the honest stake's wins are independent (A1)."""
    return pa * ph, pa * (1 - ph), (1 - pa) * ph, (1 - pa) * (1 - ph)


def keys_step(alpha: float, b: float, f: float = F) -> tuple[float, float, float, float]:
    """The same for statement 9.2: the coalition's own win a ~ p(alpha), the acquired stake's win
    b ~ p(b) and the win r ~ p(1 - alpha - b) of the stake that stays honest are independent; the fork
    counts a or b, the honest chain b or r (identical tickets, 4.2 and leadership 180)."""
    pa, pb, pr = p_of(alpha, f), p_of(b, f), p_of(1 - alpha - b, f)
    q11 = pb + (1 - pb) * pa * pr
    q10 = (1 - pb) * pa * (1 - pr)
    q01 = (1 - pb) * (1 - pa) * pr
    q00 = (1 - pb) * (1 - pa) * (1 - pr)
    return q11, q10, q01, q00


class Window:
    """The pieces of statement 6.2 for one parameter set (pa, ph, delta).

    S_t = M_pre + M+_post given tau_x = t (statement 6.2 (b)): for t = delta + 1, M+_post = M_post,
    whose start Bin(2 delta + 1, pa) counts the first 2 delta + 1 slots after the window; for t <= delta,
    M+_post = A_m + max(J + W, 1) with m = delta - t, A_m ~ Bin(m, pa) the coalition's wins in the first
    m slots after the window, and J + W the maximum of the same chain started at Bin(2 delta + 1 - m, pa).
    Each law is a finite pmf plus an atom at +infinity that dominates the tail beyond m_max."""

    def __init__(self, pa: float, ph: float, delta: int, m_max: int = 120):
        self.pa, self.ph, self.delta = pa, ph, delta
        self.t_pre = max_tail(pa, ph, delta, delta, m_max)
        self.t_post = max_tail(pa, ph, delta, 2 * delta + 1, m_max)
        pre, post = tail_to_pmf(self.t_pre), tail_to_pmf(self.t_post)
        fin = np.convolve(pre[:-1], post[:-1])
        self.inf_mass = pre[-1] + post[-1] - pre[-1] * post[-1]   # either part at infinity
        self.s_pmf = fin                                    # pmf of M_pre + M_post (finite part)
        self.theta = theta_star(pa, ph, delta)
        self.s_tau = []                                     # (finite pmf, mass at infinity) of S_t
        for t in range(delta + 2):
            if t == delta + 1:
                self.s_tau.append((fin, self.inf_mass))
                continue
            m = delta - t
            mx = max_tail(pa, ph, delta, 2 * delta + 1 - m, m_max).copy()
            mx[:2] = 1.0                                     # max(J + W, 1) >= 1
            pm = tail_to_pmf(mx)
            post_t = np.convolve(stats.binom.pmf(np.arange(m + 1), m, pa), pm[:-1])
            self.s_tau.append((np.convolve(pre[:-1], post_t), pre[-1] + pm[-1] - pre[-1] * pm[-1]))
        self.kmax = max(len(s) for s, _ in self.s_tau) - 1
        # G[t, z - Z_LO] = P(S_t >= -z), for the forward pass of p1_curve
        self._g_cache = {}

    def g_table(self, z_lo: int, z_hi: int) -> np.ndarray:
        key = (z_lo, z_hi)
        if key not in self._g_cache:
            zs = np.arange(z_lo, z_hi + 1)
            G = np.ones((self.delta + 2, zs.size))
            for t, (spmf, inf_t) in enumerate(self.s_tau):
                sf = np.append(np.cumsum(spmf[::-1])[::-1], 0.0)        # P(S_t finite and >= k)
                need = -zs                                              # S_t >= -z
                inside = need > 0
                k = np.minimum(need[inside], sf.size - 1)
                G[t, inside] = np.minimum(1.0, sf[k] + inf_t)
            self._g_cache[key] = G
        return self._g_cache[key]

    def p1(self, x: int, with_max: bool = True, corrected: bool = True) -> float:
        """P1(x) of statement 6.2, P(M_pre + Z_x + M+_post >= 0), from the joint law of (N, tau_x) in
        closed form. corrected=False gives the bound before the correction, P(M_pre + Z_x + M_post >= 0);
        with_max=False gives P(Z_x >= 0), the single-window figure without the maxima."""
        if not with_max:
            return float(math.exp(log_z_ge(x, self.pa, self.ph, self.delta, 0)[0]))
        if not corrected:
            kmax = len(self.s_pmf) - 1
            lz = log_z_ge(x, self.pa, self.ph, self.delta, kmax)
            with np.errstate(divide="ignore"):
                tot = special.logsumexp(np.log(self.s_pmf) + lz)
            return float(min(1.0, math.exp(tot) + self.inf_mass))
        lj = log_joint_greedy_tau(x - self.delta, self.ph, self.delta)
        n = np.arange(lj.shape[0])
        kmax = self.kmax
        js = np.arange(-kmax, n[-1] + 1)                  # log P(Bin(x, pa) >= j)
        lsf = np.where(js <= 0, 0.0, binom_logsf(np.maximum(js, 1) - 1, x, self.pa))
        terms = []
        for t, (spmf, inf_t) in enumerate(self.s_tau):
            col = lj[:, t]
            keep = np.isfinite(col)
            if not keep.any():
                continue
            keep &= col > col[keep].max() - 800.0
            nn, cc = n[keep], col[keep]
            ks = np.arange(spmf.size)
            L = special.logsumexp(cc[None, :] + lsf[nn[None, :] - ks[:, None] + kmax], axis=1)
            with np.errstate(divide="ignore"):
                terms.append(special.logsumexp(np.log(spmf) + L))
            if inf_t > 0:
                terms.append(math.log(inf_t) + special.logsumexp(cc))
        return float(min(1.0, math.exp(special.logsumexp(terms))))

    def p1_curve(self, x_max: int, step: tuple[float, float, float, float] | None = None,
                 z_lo: int = -1500, z_hi: int = 400) -> np.ndarray:
        """P1(x) for x = 0..x_max (entries below delta + 1 are 1) by a forward pass over the window's
        slots, with the state (z, tau): z = the fork's count minus N, tau as in log_joint_greedy_tau.
        `step` gives the joint law of (fork wins, honest wins) in one slot (default: independent, A1).
        The first delta slots count for the fork only. Mass below z_lo is held at z_lo, which only
        raises z; mass above z_hi counts as the event. Both keep the result an upper bound."""
        d = self.delta
        q11, q10, q01, q00 = joint_step(self.pa, self.ph) if step is None else step
        pf = q11 + q10                                    # the fork's chance in one slot
        G = self.g_table(z_lo, z_hi)
        nz = z_hi - z_lo + 1
        P = np.zeros((d + 2, nz))
        P[d + 1, -z_lo] = 1.0
        over = 0.0
        out = np.ones(x_max + 1)

        def up(a):                                        # z -> z + 1; the top row leaves the range
            r = np.empty_like(a)
            r[..., 1:] = a[..., :-1]
            r[..., 0] = 0.0
            return r, float(a[..., -1].sum())

        def down(a):                                      # z -> z - 1; the bottom is held at z_lo
            r = np.empty_like(a)
            r[..., :-1] = a[..., 1:]
            r[..., -1] = 0.0
            r[..., 0] += a[..., 0]
            return r

        for x in range(1, x_max + 1):
            new = np.zeros_like(P)
            if x <= d:                                    # fork only, no pick yet
                u, o = up(P[d + 1])
                new[d + 1] = pf * u + (1 - pf) * P[d + 1]
                over += pf * o
            else:
                u, o = up(P[:d])                          # not eligible: tau < delta
                new[1:d + 1] += pf * u + (1 - pf) * P[:d]
                over += pf * o
                E = P[d] + P[d + 1]                       # eligible: tau >= delta
                uE, oE = up(E)
                new[0] += q11 * E + q01 * down(E)
                new[d + 1] += q10 * uE + q00 * E
                over += q10 * oE
            P = new
            if x > d:
                out[x] = min(1.0, float(np.sum(P * G)) + over)
        return out


def strict_single(x: int, pa: float, ph: float, delta: int) -> float:
    """P(Bin(x, pa) > N_study(x)) with the study's honest count, P(N >= n) = P(Bin(x - n delta) >= n):
    the figure of finality_sim.recovery (fork strictly denser, no maxima)."""
    lpn = log_pmf_greedy(x - delta, ph, delta)  # same law as the study's N over x slots
    n = np.arange(len(lpn))
    la = binom_logsf(n, x, pa)                   # A > n
    return float(math.exp(special.logsumexp(lpn + la)))


# ------------------------------------------------------------------------------------------------
# U(w): the study's settlement bound (GRR 2022/1571, Lemma 10 and Theorem 2), finality_sim.waitbound
# ------------------------------------------------------------------------------------------------
def settle_curve(alpha: float, delta: int, t_max: int, scale: float = 1.0) -> np.ndarray:
    """U[w - 1] = the study's bound on P(mu_l >= 0 at some time >= l + w), w = 1..t_max."""
    if FINALITY_SRC not in sys.path:
        sys.path.insert(0, FINALITY_SRC)
    from finality_sim import waitbound as wb  # noqa: E402
    return wb.wait_curve(t_max, alpha, delta, f=F, floor=0.0, scale=scale)


def settle_cached(alpha: float, delta: int, t_max: int = 80_000, scale: float = 1.0) -> np.ndarray:
    os.makedirs(os.path.join(HERE, ".cache"), exist_ok=True)
    name = os.path.join(HERE, ".cache", f"U_a{alpha:.6f}_d{delta}_t{t_max}_s{scale:.6f}.npy")
    if os.path.exists(name):
        return np.load(name)
    c = settle_curve(alpha, delta, t_max, scale)
    np.save(name, c)
    return c


def U_at(curve: np.ndarray, w: int) -> float:
    if w <= 0:
        return 1.0
    if w > len(curve):
        raise ValueError("curve too short")
    return float(curve[w - 1])
