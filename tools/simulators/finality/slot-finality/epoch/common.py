"""Constants and formulas shared by the scripts of the epoch-length review.

Every constant is the specification's, read from git:
  10-hour branch  Bedrock-RFC-Slot-Finality-10h  (commit 7f3cf149)
  base branch     Bedrock-RFC-Slot-Finality      (commit ded1d4c6)
Line numbers are those of the file as `git show <branch>:<path>` prints it.

Formulas are the ones REVIEW.md proves (statements 5.3 to 5.5). Slots are 1 second long.
"""
import math

from scipy.stats import binom

# --- cryptarchia-v1-protocol.md, Constants (lines 100-110) -------------------------------------
F_NUM, F_DEN = 1, 30            # f = 1/30, slot activation coefficient
F = F_NUM / F_DEN
K_SEC = 2160                    # k, security parameter, blocks
U = K_SEC * F_DEN // F_NUM      # floor(k/f) = 64,800 slots: the unit of the Epoch Schedule
EPS = 1e-9                      # epsilon of Finality Floor (EPSILON = 1e-9, line 531)
T_M = 15                        # message traversal time of Blend, rounds of one slot (blend-protocol.md 481)
DELTA = 10                      # Delta of the K row, slots
ALPHA_MAX = 0.3                 # alpha_max of the K row

CASES = {                       # name: (K, phi)
    "10 h (#533)": (36_000, 689),    # 10-hour branch, Constants lines 104-105
    "18 h (base)": (64_800, 1_291),  # base branch, the same rows
}

# --- Epoch Schedule (lines 149-159) ------------------------------------------------------------
PHASE_1 = 3 * U                 # Stake Distribution Snapshot
PHASE_2 = 3 * U                 # Buffer
PHASE_3 = 4 * U                 # Lottery Constants Finalization
EPOCH = PHASE_1 + PHASE_2 + PHASE_3
CUT_OFF = PHASE_1 + PHASE_2     # slot into the epoch at which eta and D are read (line 229, 237)
GAP = PHASE_3                   # from the cut-off to the first slot of the next epoch
PERIOD = 6 * U                  # cryptarchia-total-stake-inference.md line 55
S_GEN = K_SEC * F_DEN // (4 * F_NUM)   # floor(k/(4f)), fork-choice.md line 80

H = 3600                        # slots in an hour


def p_of(x: float, f: float = F) -> float:
    """Chance per slot that a share x of the inferred stake wins it: 1 - (1 - f)^x."""
    return -math.expm1(x * math.log1p(-f))


def short(n: int, slots: int, p: float, d: int) -> float:
    """S(n; L, p, d) = P(Binomial(L - n d, p) <= n - 1): the specification's blocks_short(n) with
    K -> slots, f -> p, T_M -> d (REVIEW.md, 5.3)."""
    m = slots - n * d
    if m < n:
        return 1.0
    return float(binom.cdf(n - 1, m, p))


def log_short(n: int, slots: int, p: float, d: int) -> float:
    m = slots - n * d
    if m < n:
        return 0.0
    return float(binom.logcdf(n - 1, m, p))


def at_most_one(m: int, p: float) -> float:
    """R(m; p) = P(Binomial(m, p) <= 1) for m >= 1, and 1 for m <= 0."""
    if m <= 0:
        return 1.0
    return math.exp(m * math.log1p(-p)) + m * p * math.exp((m - 1) * math.log1p(-p))


def upper(G: int, K: int, phi: int, p: float, d: int) -> float:
    """REVIEW.md, 5.4: upper bound on P(the value is not final when first used)."""
    return min(1.0, short(phi + 1, G, p, d) + at_most_one(G - K - 2 * d + 1, p))


def lower_chain(G: int, K: int, phi: int, p: float, d: int) -> float:
    """REVIEW.md, 5.5 (b): lower bound when only blocks of the chain count as occupied slots."""
    m = G + 1 - phi * d
    floor_part = 1.0 if m < phi + 1 else float(binom.cdf(phi, m, p))
    age_part = math.exp((G - K + 1) * math.log1p(-p)) if G - K + 1 > 0 else 1.0
    return max(floor_part, age_part)


def lower_wins(G: int, K: int, phi: int, p: float) -> float:
    """REVIEW.md, 5.5 (a): lower bound in every case: every win of the gap counted, no delay."""
    floor_part = float(binom.cdf(phi - 1, G, p)) if G >= phi else 1.0
    age_part = math.exp((G - K + 1) * math.log1p(-p)) if G - K + 1 > 0 else 1.0
    return max(floor_part, age_part)


def least_share(fn, eps: float = EPS, x_max: float = 1.0):
    """The least x in (0, x_max] with fn(p_of(x)) <= eps, fn decreasing in p. None if fn(p_of(x_max)) > eps."""
    if fn(p_of(x_max)) > eps:
        return None
    lo, hi = 0.0, x_max
    for _ in range(80):
        mid = (lo + hi) / 2
        if fn(p_of(mid)) <= eps:
            hi = mid
        else:
            lo = mid
    return hi


def least_gap(K: int, phi: int, x: float, d: int, eps: float = EPS, g_max: int = 40_000_000) -> int:
    """The least gap G (slots) with upper(G) <= eps, at a building share x."""
    p = p_of(x)
    lo, hi = K, g_max
    if upper(hi, K, phi, p, d) > eps:
        raise ValueError("g_max too small")
    while lo < hi:
        mid = (lo + hi) // 2
        if upper(mid, K, phi, p, d) <= eps:
            hi = mid
        else:
            lo = mid + 1
    return lo


def least_int(fn, lo: int, hi: int, eps: float = EPS) -> int:
    """The least integer G in [lo, hi] with fn(G) <= eps, fn non-increasing in G."""
    if fn(hi) > eps:
        raise ValueError("hi too small")
    while lo < hi:
        mid = (lo + hi) // 2
        if fn(mid) <= eps:
            hi = mid
        else:
            lo = mid + 1
    return lo


def mean_rate_share(G: int, phi: int) -> float:
    """The RFCs' mean-rate figure: the share x at which G slots hold phi occupied slots on average,
    p_x G = phi (RFC-533 line 183, RFC-532 line 308)."""
    q = phi / G
    return math.log1p(-q) / math.log1p(-F)


def pct(x) -> str:
    return "  none" if x is None else f"{100 * x:6.2f}"
