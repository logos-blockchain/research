"""First look for the fast-finalization plan.

Prints every number PLAN.md §1 quotes. The models are deliberately crude: they size the
problem, they do not settle it. PLAN.md §1.8 names the phase that replaces each one.

    python3 firstlook.py           # gates, then the tables
    python3 firstlook.py --gates   # gates only

Pinned sources (logos-lips 47a73cdc, docs/blockchain/raw/; research 272fd9a; logos-blockchain):
- cryptarchia-v1-protocol.md, Constants and Notation: f = 1/30, k = 2160 blocks, slot = 1 s,
  s = 3*floor(k/f), epoch = 10*floor(k/f) slots; Block Header: ProofOfLeadership 224 bytes.
- analysis-total-stake-inference.md, "Connecting Simulation to Logos Blockchain": q = 0.85 at
  the specification's Blend parameters (3 hops, 2 s per hop, 6 s mean end-to-end delay),
  measured before uncle references, so the orphan share o = 0.15.
- reports/tsi/README.md §3.3 and §6.10 (research 272fd9a): o = 0.20, 0.35 and 0.60 at per-hop
  delays of 2, 8 and 32 s, with D_vis = 3 * delay / 2 + 5 s.
- analysis-block-times-blend-network.md, Annex: the Praos condition and its 70/75/83 % readings.
- David, Gazi, Kiayias, Russell, "Ouroboros Praos", ePrint 2017/573 rev. 2023-04-27: Theorem 7
  (the condition) and Theorem 11 (epoch R = 24k/f, liveness u = 8k/f).
- logos-blockchain 865df42ba (testnet 0.3.0), deployment settings.yaml: k = 120, f = 1/30.
- reports/blend/README.md §3.10 (research 272fd9a): the emission-quota ceiling
  s_max = ln(1 - q) / ln(1 - f) and its table at N = 20 000.
- Nakamoto, "Bitcoin: A Peer-to-Peer Electronic Cash System", §11: the attacker tables.
- Grunspan, Perez-Marco, "Double spend races", arXiv 1702.02867v3: Tables 2-4 and
  P(z) = I_{4pq}(z, 1/2).
- Dembo et al., "Everything is a Race and Nakamoto Always Wins", arXiv 2005.10484v4, eq. (2):
  beta < (1 - beta) / (1 + (1 - beta) lambda Delta), for PoW and Ouroboros/Snow White PoS.
- CIP-0140 (Ouroboros Peras), status Proposed: committee n = 900, round U = 90 slots.
- Castro-Castilla, Pawlowski, Zhou, "Areon: Latency-Friendly and Resilient Multi-Proposer
  Consensus", arXiv 2511.23025v1, §6: evaluated block rates of 0.05-0.5 per slot, default 0.25.
"""

from __future__ import annotations

import argparse
import math
import sys

import numpy as np
from scipy import special, stats

# --- Constants (pinned above) --------------------------------------------------------------
F = 1 / 30          # slot activation coefficient: occupied slots per slot
K = 2160            # security parameter, blocks
K_TESTNET = 120     # security parameter of testnet 0.3.0
SLOT_S = 1.0        # slot length, seconds
POL_BYTES = 224     # ProofOfLeadership, Block Header
O_SPEC = 0.15       # orphan share at the specification's Blend parameters
O_TSI = 0.35        # orphan share at the TSI report's operating point (8 s per hop)
ORPHANS = (0.0, O_SPEC, O_TSI)
BLEND_N = 20_000    # reports/blend §3.10: network size behind its quota table
PERAS_N, PERAS_U = 900, 90


# --- Settlement models ---------------------------------------------------------------------

def satoshi(q: float, z: int) -> float:
    """Nakamoto §11 AttackerSuccessProbability, ported line for line."""
    p = 1.0 - q
    lam = z * (q / p)
    total = 1.0
    for k in range(z + 1):
        poisson = math.exp(-lam)
        for i in range(1, k + 1):
            poisson *= lam / i
        total -= poisson * (1 - (q / p) ** (z - k))
    return total


def rosenfeld_closed(q: float, n: int) -> float:
    """Rosenfeld's closed form, 1 - sum_{m=0}^{n} C(m+n-1, m)(p^n q^m - p^m q^n).

    Cancels catastrophically below ~1e-12; used only as an independent check of
    :func:`rosenfeld` at small n.
    """
    if n == 0:
        return 1.0
    p = 1.0 - q
    s = 0.0
    for m in range(n + 1):
        s += math.comb(m + n - 1, m) * (p ** n * q ** m - p ** m * q ** n)
    return 1.0 - s


def rosenfeld(q: float, n: int, _shift: int = 0) -> float:
    """Double-spend success after n confirmations, attacker block share q (Rosenfeld 2014).

    The attacker's blocks M while the honest chain finds n are negative binomial; from a
    deficit n - M it catches up with probability (q/p)^(n-M). Summed in log space, so it
    stays accurate at n = 2160 and far below 1e-12. ``_shift`` exists only for the mutation
    gate.
    """
    if q >= 0.5:
        return 1.0
    if n == 0:
        return 1.0
    p = 1.0 - q
    m = np.arange(n)
    log_nb = stats.nbinom.logpmf(m, n, p)
    log_catch = (n - m + _shift) * math.log(q / p)
    behind = float(np.exp(special.logsumexp(log_nb + log_catch)))
    ahead = float(stats.nbinom.sf(n - 1, n, p))     # P(M >= n)
    return ahead + behind


def catchup(q: float, d: int) -> float:
    """The reports/tsi §6.10 tail: an attacker d blocks behind ever draws level."""
    if q >= 0.5:
        return 1.0
    return (q / (1.0 - q)) ** d


def alpha_eff(alpha: float, o: float) -> float:
    """Attacker share of chain-extending blocks when honest blocks are orphaned at rate o."""
    return alpha / (alpha + (1.0 - alpha) * (1.0 - o))


def alpha_from_eff(q: float, o: float) -> float:
    """Inverse of :func:`alpha_eff`."""
    return q * (1.0 - o) / (1.0 - q * o)


def min_depth(fn, q: float, eps: float) -> int | None:
    """Smallest n with fn(q, n) <= eps, or None when no depth suffices."""
    if q >= 0.5:
        return None
    hi = 1
    while fn(q, hi) > eps:
        hi *= 2
        if hi > 10 ** 7:
            return None
    lo = hi // 2
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if fn(q, mid) <= eps:
            hi = mid
        else:
            lo = mid
    return hi


def max_share(fn, n: int, eps: float) -> float:
    """Largest attacker share q with fn(q, n) <= eps."""
    lo, hi = 0.0, 0.5
    for _ in range(60):
        mid = (lo + hi) / 2
        if fn(mid, n) <= eps:
            lo = mid
        else:
            hi = mid
    return lo


def minutes(depth: int, o: float, f: float = F) -> float:
    """Expected minutes for the canonical chain to grow by depth blocks."""
    return depth / (f * (1.0 - o)) * SLOT_S / 60


def praos_honest(f: float, delta: int, eps: float = 1e-6, _exp_shift: int = 1) -> float:
    """Honest share the Praos condition alpha (1-f)^(Delta+1) >= (1+eps)/2 requires.

    ``_exp_shift`` exists only for the mutation gate.
    """
    return (1.0 + eps) / (2.0 * (1.0 - f) ** (delta + _exp_shift))


def private_attack_threshold(x: float) -> float:
    """Dembo et al. eq. (2) at equality, beta = (1 - beta) / (1 + (1 - beta) x), x = f Delta.

    Closed-form root of x beta^2 - (2 + x) beta + 1 = 0.
    """
    if x == 0:
        return 0.5
    return ((2 + x) - math.sqrt(4 + x * x)) / (2 * x)


def private_attack_threshold_bisect(x: float) -> float:
    """Independent check of :func:`private_attack_threshold`: bisect eq. (2)."""
    lo, hi = 0.0, 0.5
    for _ in range(80):
        mid = (lo + hi) / 2
        if mid < (1 - mid) / (1 + (1 - mid) * x):
            lo = mid
        else:
            hi = mid
    return lo


def quota_ceiling(rate: float, n_nodes: int = BLEND_N, f: float = F) -> float:
    """reports/blend §3.10: the largest stake share, of inferred stake, whose lottery wins fit
    a node's cover quota q = rate / N per slot, alpha_max = ln(1 - q) / ln(1 - f)."""
    q = rate / n_nodes
    return math.log(1 - q) / math.log(1 - f)


def emission_multiplier(n_seats: float, round_slots: float, f: float = F) -> float:
    """Lottery emissions per unit stake with votes, over blocks alone: (f + n/R) / f."""
    return 1.0 + n_seats / (round_slots * f)


def orphan_share(f: float, d_vis: float) -> float:
    """Collision model: a block loses a tie with probability 1/2 to any block made within
    +-D_vis of it. Crude; checked against the TSI engine in :func:`table_rate`."""
    return (1.0 - math.exp(-2.0 * f * d_vis)) / 2.0


# reports/tsi §3.3 and §6.10: 3 hops and a gossip term of about 5 s give D_vis = 3 delay/2 + 5.
TSI_MEASURED = ((2, 0.20), (8, 0.35), (32, 0.60))


# --- Anonymous-seat committee --------------------------------------------------------------

def safety_tail(n: float, alpha: float, q2: int, adv_weight: int = 2,
                awake: float = 1.0) -> float:
    """P(H + 2A >= q2): two conflicting quorums of Q = q2/2 votes can both form.

    H ~ Poisson(awake (1-alpha) n) honest seats vote once; offline honest seats cast nothing.
    A ~ Poisson(alpha n) adversarial seats vote for both sides. ``adv_weight`` exists only for
    the mutation gate.
    """
    mu_h, mu_a = awake * (1 - alpha) * n, alpha * n
    a_max = int(mu_a + 60 * math.sqrt(mu_a + 1) + 60)
    a = np.arange(a_max + 1)
    log_pa = stats.poisson.logpmf(a, mu_a)
    need = q2 - adv_weight * a                      # honest seats still needed
    log_sf = np.where(need <= 0, 0.0, stats.poisson.logsf(need - 1, mu_h))
    return float(np.exp(special.logsumexp(log_pa + log_sf)))


def safety_tail_brute(n: float, alpha: float, q2: int) -> float:
    """Independent check of :func:`safety_tail`: convolve the two pmfs directly."""
    mu_h, mu_a = (1 - alpha) * n, alpha * n
    top = int(3 * n + 200)
    ph = stats.poisson.pmf(np.arange(top), mu_h)
    pa = stats.poisson.pmf(np.arange(top), mu_a)
    p2a = np.zeros(2 * top)
    p2a[::2] = pa
    conv = np.convolve(ph, p2a)
    return float(conv[q2:].sum())


def liveness_tail(n: float, alpha: float, quorum: int, awake: float = 1.0) -> float:
    """P(H < Q): the adversary abstains and the awake honest seats miss the quorum."""
    return float(stats.poisson.cdf(quorum - 1, awake * (1 - alpha) * n))


def committee(alpha: float, eps: float, awake: float = 1.0) -> tuple[int, int] | None:
    """Smallest expected committee n, with its quorum Q, holding both tails <= eps.

    ``awake`` is the share of honest stake that votes; seats are drawn against all stake, as
    they are until the stake inference adapts.
    """
    if alpha >= awake / (2 + awake):                # 2Q > (1+alpha) n and Q < awake (1-alpha) n
        return None

    def quorum_for(n: int) -> int:
        lo, hi = 0, 2 * n + 10                       # bisection on Q: safety falls with Q
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if safety_tail(n, alpha, 2 * mid, awake=awake) <= eps:
                hi = mid
            else:
                lo = mid
        return hi

    def ok(n: int) -> bool:
        return liveness_tail(n, alpha, quorum_for(n), awake) <= eps

    hi = 16
    while not ok(hi):
        hi *= 2
        if hi > 2 ** 22:
            return None
    lo = hi // 2
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid
        else:
            lo = mid
    return hi, quorum_for(hi)


# --- Gates ---------------------------------------------------------------------------------

SATOSHI_Q01 = [1.0000000, 0.2045873, 0.0509779, 0.0131722, 0.0034552, 0.0009137,
               0.0002428, 0.0000647, 0.0000173, 0.0000046, 0.0000012]
SATOSHI_Q03 = {0: 1.0000000, 5: 0.1773523, 10: 0.0416605, 15: 0.0101008, 20: 0.0024804,
               25: 0.0006132, 30: 0.0001522, 35: 0.0000379, 40: 0.0000095,
               45: 0.0000024, 50: 0.0000006}
SATOSHI_Z = {0.10: 5, 0.15: 8, 0.20: 11, 0.25: 15, 0.30: 24, 0.35: 41, 0.40: 89, 0.45: 340}
# analysis-block-times-blend-network.md, Annex: (f, Delta, stated honest share, tolerance).
PRAOS_ANNEX = ((1 / 20, 5, 0.70, 0.025), (1 / 30, 14, 0.83, 0.005), (1 / 30, 11, 0.75, 0.005))


def gate_satoshi(fn) -> bool:
    """fn reproduces Nakamoto §11 to the printed 7 decimals, and its P < 0.1% depths."""
    for z, want in enumerate(SATOSHI_Q01):
        if abs(fn(0.1, z) - want) > 5e-8:
            return False
    for z, want in SATOSHI_Q03.items():
        if abs(fn(0.3, z) - want) > 5e-8:
            return False
    return all(min_depth(fn, q, 1e-3) == z for q, z in SATOSHI_Z.items())


# Grunspan, Perez-Marco, arXiv 1702.02867v3: Table 2 (q = 0.1), Table 3 (q = 0.3), Table 4.
GPM_Q01 = [1.0000000, 0.2000000, 0.0560000, 0.0171200, 0.0054560, 0.0017818, 0.0005914,
           0.0001986, 0.0000673, 0.0000229, 0.0000079]
GPM_Q03 = {0: 1.0000000, 5: 0.1976173, 10: 0.0651067, 15: 0.0233077, 20: 0.0086739,
           25: 0.0033027, 30: 0.0012769, 35: 0.0004991, 40: 0.0001967, 45: 0.0000780,
           50: 0.0000311}
GPM_Z = {0.10: 6, 0.15: 9, 0.20: 13, 0.25: 20, 0.30: 32, 0.35: 58, 0.40: 133, 0.45: 539}
# reports/blend/README.md §3.10: cover rate (msg/s, whole network) -> s_max, % of inferred stake.
BLEND_QUOTA = {1: 0.147, 16: 2.36, 64: 9.45, 256: 38.0}


def gate_rosenfeld(fn) -> bool:
    """fn reproduces Grunspan and Perez-Marco's Tables 2-4, their closed form
    I_{4pq}(z, 1/2) to 1e-12, and Rosenfeld's closed form to 1e-12 at small z.

    The printed tables are matched to one unit in their last digit: their q = 0.1, z = 8
    entry reads 0.0000673 where the closed form gives 0.00006725.
    """
    for z, want in enumerate(GPM_Q01):
        if abs(fn(0.1, z) - want) > 1e-7:
            return False
    for z, want in GPM_Q03.items():
        if abs(fn(0.3, z) - want) > 1e-7:
            return False
    if any(min_depth(fn, q, 1e-3) != z for q, z in GPM_Z.items()):
        return False
    for q in (0.05, 0.1, 0.2, 0.3, 0.4, 0.45):
        for n in range(1, 41):
            if abs(fn(q, n) - special.betainc(n, 0.5, 4 * q * (1 - q))) > 1e-12:
                return False
            if abs(fn(q, n) - rosenfeld_closed(q, n)) > 1e-12:
                return False
    return True


def gate_threshold(fn) -> bool:
    """fn agrees with a bisection of Dembo et al. eq. (2) to 1e-9, and is 1/2 at x = 0."""
    if abs(fn(0.0) - 0.5) > 1e-12:
        return False
    return all(abs(fn(x) - private_attack_threshold_bisect(x)) <= 1e-9
               for x in (0.01, 0.1, 0.2, 0.37, 0.5, 1.0, 2.0))


def gate_quota(fn) -> bool:
    """fn reproduces the Blend report's s_max column to 0.5 % relative."""
    return all(abs(100 * fn(rate) - want) <= 0.005 * want for rate, want in BLEND_QUOTA.items())


def gate_committee(fn) -> bool:
    """fn agrees with a direct convolution to 1e-3 relative, over a grid of quorums."""
    for alpha in (0.1, 0.25):
        for n in (200, 800):
            for frac in (0.55, 0.65, 0.75):
                q2 = 2 * int(frac * n)
                want = safety_tail_brute(n, alpha, q2)
                got = fn(n, alpha, q2)
                if want < 1e-280:
                    continue
                if abs(got - want) > 1e-3 * want:
                    return False
    return True


def gate_praos(fn) -> bool:
    """fn reproduces the honest shares the specification's annex reads off its plots."""
    return all(abs(fn(f, delta) - want) <= tol for f, delta, want, tol in PRAOS_ANNEX)


def run_gates() -> None:
    checks = [
        ("satoshi reproduces Nakamoto §11", gate_satoshi(satoshi), True),
        ("mutant satoshi (z-1) fails it", gate_satoshi(lambda q, z: satoshi(q, max(z - 1, 0))), False),
        ("rosenfeld (log space) = closed form", gate_rosenfeld(rosenfeld), True),
        ("mutant rosenfeld (exponent +1) fails it",
         gate_rosenfeld(lambda q, n: rosenfeld(q, n, _shift=1)), False),
        ("committee tail = direct convolution", gate_committee(safety_tail), True),
        ("mutant committee tail (H + A) fails it",
         gate_committee(lambda n, a, q2: safety_tail(n, a, q2, adv_weight=1)), False),
        ("praos condition reproduces the annex", gate_praos(praos_honest), True),
        ("mutant praos condition ((1-f)^Delta) fails it",
         gate_praos(lambda f, d: praos_honest(f, d, _exp_shift=0)), False),
        ("private-attack threshold = bisection of eq. (2)", gate_threshold(private_attack_threshold), True),
        ("mutant threshold (beta x for (1-beta) x) fails it",
         gate_threshold(lambda x: (math.sqrt(1 + x) - 1) / x if x else 0.5), False),
        ("quota ceiling reproduces the Blend report", gate_quota(quota_ceiling), True),
        ("mutant quota ceiling (q/f) fails it",
         gate_quota(lambda r: (r / BLEND_N) / F), False),
    ]
    bad = [name for name, got, want in checks if got != want]
    for name, got, want in checks:
        print(f"  [{'ok' if got == want else 'FAIL'}] {name}")
    if bad:
        sys.exit(f"gates failed: {bad}")


# --- Tables --------------------------------------------------------------------------------

def hours(slots: float) -> float:
    return slots * SLOT_S / 3600


def table_timeline() -> None:
    kf = math.floor(K / F)
    print("\n1. Where the time goes")
    print(f"  k/f = {kf} slots = {hours(kf):.1f} h (time to k-deep, no forks)")
    print(f"  s = 3*floor(k/f) = {3 * kf} slots = {hours(3 * kf):.1f} h")
    print(f"  epoch = 10*floor(k/f) = {10 * kf} slots = {hours(10 * kf) / 24:.2f} days")
    for o in ORPHANS:
        t = K / (F * (1 - o))
        print(f"  k-deep at orphan share o = {o:.2f}: {t:.0f} slots = {hours(t):.1f} h")
    kt = math.floor(K_TESTNET / F)
    print(f"  testnet 0.3.0, k = {K_TESTNET}: k/f = {kt} slots = {hours(kt):.1f} h, "
          f"epoch = {hours(10 * kt):.1f} h")
    print("  partition: the losing side rolls back what it made since the split; a side holding")
    print("  stake share sigma occupies a slot with probability 1 - (1 - f)^sigma (same epoch,")
    print("  no forks), so it makes `depth` blocks in depth / (1 - (1 - f)^sigma) slots")
    for depth, label in ((K, "k"), (K // 10, "k/10"), (K_TESTNET, "k_test")):
        cells = ", ".join(f"sigma={sg:.1f}: {hours(depth / (1 - (1 - F) ** sg)):.1f} h"
                          for sg in (0.5, 0.2))
        print(f"    {label:6s} = {depth:4d} blocks: {cells}")
    t_offline = 20 * 60                          # cryptarchia-v1-bootstr-sync.md, T_offline
    print("  offline grace margin (k/f) / T_offline, T_offline = 20 min: " + ", ".join(
        f"{label} {math.floor(depth / F) * SLOT_S / t_offline:.1f}"
        for depth, label in ((K, "k"), (K // 10, "k/10"), (K_TESTNET, "k_test"))))


def table_depths() -> None:
    print("\n2. Confirmation depth d (blocks) and minutes, Rosenfeld model, attacker share alpha_eff")
    print("   minutes = d / (f (1 - o)) / 60; 'none' = alpha_eff >= 1/2, no depth suffices")
    for o in ORPHANS:
        print(f"  o = {o:.2f}")
        print("    alpha  a_eff  | eps=1e-3        | eps=1e-6        | eps=1e-9")
        for a in (0.10, 0.20, 0.25, 0.30, 1 / 3, 0.40):
            q = alpha_eff(a, o)
            cells = []
            for eps in (1e-3, 1e-6, 1e-9):
                d = min_depth(rosenfeld, q, eps)
                cells.append("none".ljust(15) if d is None
                             else f"{d:5d} {minutes(d, o):6.0f} min")
            print(f"    {a:.3f}  {q:.3f}  | " + " | ".join(cells))
    print("  for comparison, the reports/tsi §6.10 catch-up tail at o = 0.35, eps = 1e-3:")
    print("    " + ", ".join(
        f"alpha={a:.2f}: d={min_depth(catchup, alpha_eff(a, O_TSI), 1e-3)}"
        for a in (0.10, 0.20, 0.30)))


def table_orphans() -> None:
    print("\n2b. The orphan share moves both factors: depth (via alpha_eff) and time per block")
    print("    eps = 1e-9, Rosenfeld model; cells: depth, minutes")
    print("    o     | alpha=0.20       | alpha=0.25       | alpha=0.30")
    for o in (0.0, 0.1, O_SPEC, 0.2, O_TSI, 0.5):
        cells = []
        for a in (0.20, 0.25, 0.30):
            d = min_depth(rosenfeld, alpha_eff(a, o), 1e-9)
            cells.append("none".ljust(16) if d is None else f"{d:5d} {minutes(d, o):6.0f} min")
        print(f"    {o:.2f}  | " + " | ".join(cells))


def table_rate() -> None:
    print("\n2c. Block rate and visibility delay, collision model o = (1 - exp(-2 f D_vis)) / 2")
    print("    model against the TSI engine at f = 1/30:")
    for delta, measured in TSI_MEASURED:
        d_vis = 3 * delta / 2 + 5
        print(f"      per-hop delay {delta:2d} s, D_vis {d_vis:4.1f} s: model o = "
              f"{orphan_share(F, d_vis):.2f}, engine o = {measured:.2f}")
    print("    minutes to settle, alpha = 0.25, eps = 1e-9, Rosenfeld model;"
          " '-' = rho = f D_vis > 1, outside the model")
    rates = (60, 45, 30, 20, 15, 10)
    print("      D_vis \\ 1/f | " + " | ".join(f"{r:5d}" for r in rates))
    for d_vis in (3.0, 6.0, 8.0, 17.0, 30.0):
        cells = []
        for r in rates:
            f = 1 / r
            if f * d_vis > 1.0:                  # the model under-predicts o past rho = 1
                cells.append("    -")
                continue
            o = orphan_share(f, d_vis)
            d = min_depth(rosenfeld, alpha_eff(0.25, o), 1e-9)
            cells.append(f"{minutes(d, o, f):5.0f}" if d else " none")
        print(f"      {d_vis:4.0f} s      | " + " | ".join(cells))
    for d_vis in (3.0, 6.0):
        print(f"    collision-model o at f = 1/30, D_vis = {d_vis:.0f} s: "
              f"{orphan_share(F, d_vis):.2f}")


def table_what_k_buys() -> None:
    print("\n3. What k = 2160 buys: largest attacker share it holds, Rosenfeld model")
    print("    eps     max alpha_eff | alpha at o=0 | alpha at o=0.15 | alpha at o=0.35")
    for eps in (1e-3, 1e-6, 1e-9, 1e-12):
        q = max_share(rosenfeld, K, eps)
        print(f"    {eps:.0e}  {q:.4f}        | " + " | ".join(
            f"{alpha_from_eff(q, o):.4f}".ljust(14) for o in ORPHANS))
    for o in ORPHANS:
        print(f"  alpha_eff reaches 1/2 at o = {o:.2f} when alpha = {alpha_from_eff(0.5, o):.4f}")
    q = max_share(rosenfeld, K_TESTNET, 1e-9)
    print(f"  testnet k = {K_TESTNET}, eps = 1e-9: max alpha_eff {q:.4f}; alpha at o=0.15 "
          f"{alpha_from_eff(q, O_SPEC):.4f}")


def table_praos() -> None:
    print("\n3b. The specification's Praos condition: honest share needed, f = 1/30, eps = 1e-6")
    for delta in (3, 6, 11, 14, 15, 17, 19, 20):
        h = praos_honest(F, delta)
        tail = f"adversary <= {1 - h:.3f}" if h <= 1 else "no stake split satisfies it"
        print(f"    Delta = {delta:2d} s: honest >= {h:.3f}, {tail}")
    d_max = math.floor(math.log(2 / (1 + 1e-6)) / -math.log(1 - F)) - 1
    print(f"    the condition can hold only while Delta <= {d_max} s")
    u = math.floor(8 * K / F)
    print(f"    Praos Theorem 11 liveness bound u = 8k/f = {u} slots = {hours(u) / 24:.1f} days at k = {K}")


def table_threshold() -> None:
    print("\n3c. Worst-case delay: the private-attack threshold of Dembo et al. eq. (2), f = 1/30")
    print("    against the random-delay threshold alpha_eff = 1/2, alpha = (1-o)/(2-o)")
    # 3 s: testnet's Blend deadline T_M = 1 (1 + 2); 6 s: the specification's mean 3-hop delay;
    # 11 s: the annex's maximum delay; 15 s: the specification's deadline T_M = 3 (3 + 2).
    for delta in (3, 6, 11, 15):
        x = F * delta
        b = private_attack_threshold(x)
        o_equiv = 1 - 1 / (1 + (1 - b) * x)
        print(f"    Delta = {delta:2d} s (f Delta = {x:.3f}): beta* = {b:.4f}; honest growth "
              f"factor 1/(1+(1-beta*) f Delta) = {1 - o_equiv:.3f}, i.e. o = {o_equiv:.3f}")
    for o in (O_SPEC, O_TSI):
        print(f"    random delays, o = {o:.2f}: alpha < {alpha_from_eff(0.5, o):.4f}")


def table_spread() -> None:
    print("\n4. Spread of the wait: time to d chain blocks is Gamma(d, f(1-o)); p95 / mean")
    for d in (10, 30, 100, K):
        ratio = stats.gamma.ppf(0.95, d) / d
        print(f"    d = {d:5d}: p95/mean = {ratio:.2f}")


def table_committee() -> None:
    print("\n5. Anonymous-seat committee: smallest expected size n (and quorum Q) per round")
    print("   seats Poisson, adversary votes both sides; safety P(H+2A >= 2Q), liveness P(H < Q)")
    print("    alpha | eps=1e-6         | eps=1e-9")
    for a in (0.10, 0.20, 0.25, 0.30):
        cells = []
        for eps in (1e-6, 1e-9):
            res = committee(a, eps)
            cells.append(f"n={res[0]:6d} Q={res[1]:6d}" if res else "none")
        print(f"    {a:.2f}  | " + " | ".join(cells))
    print("   alpha >= 1/3: no quorum exists (2Q > (1+alpha)n and Q < (1-alpha)n conflict)")
    print("   a fifth of honest stake offline (awake = 0.8), seats still drawn against all stake:")
    for a in (0.10, 0.20, 0.25, 0.30):
        res = committee(a, 1e-6, awake=0.8)
        print(f"    alpha {a:.2f}, eps 1e-6: " + (f"n={res[0]:6d} Q={res[1]:6d}" if res
                                                 else "none (alpha >= awake/(2+awake))"))
    seats = committee(0.25, 1e-9)[0]
    print(f"   at alpha = 0.25, eps = 1e-9: {seats} seats x {POL_BYTES} B = "
          f"{seats * POL_BYTES / 1e6:.1f} MB a round, before nullifiers, targets and Blend overhead")
    print("   Blend emission budget (reports/blend §3.10): every lottery win is an emission")
    print(f"    quota ceiling at the baseline cover rate (1 msg/s, N = {BLEND_N}): "
          f"{100 * quota_ceiling(1):.3f} % of inferred stake")
    for n_seats, r_slots, label in ((PERAS_N, PERAS_U, "Peras n, U"), (seats, PERAS_U, "n(0.25,1e-9), U"),
                                    (PERAS_N, 600, "Peras n, 10 min"), (seats, 600, "n(0.25,1e-9), 10 min")):
        m = emission_multiplier(n_seats, r_slots)
        print(f"    {label:22s} n = {n_seats:5d}, R = {r_slots:3d} s: votes {n_seats / r_slots:6.1f} msg/s; "
              f"emissions per unit stake x{m:7.1f}; ceiling {100 * quota_ceiling(1) / m:.5f} % "
              f"unless the cover rate rises x{m:.0f}")
    print("   multi-proposer DAG (Areon): every block is a lottery win, so lam blocks per slot")
    print("   multiply emissions per unit stake by lam / f")
    for lam in (0.05, 0.10, 0.25):
        m = lam / F
        print(f"    lam = {lam:.2f} per slot: x{m:4.1f}; ceiling {100 * quota_ceiling(1) / m:.4f} % "
              f"unless the cover rate rises x{m:.1f}")
    year = 365 * 24 * 3600
    for label, seconds in (("one round per 30 s block", 30), ("one round per 10 min", 600)):
        print(f"   {label}: {year / seconds:,.0f} rounds a year, so eps = 1e-9 per round "
              f"is {year / seconds * 1e-9:.1e} expected failures a year")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gates", action="store_true", help="run the gates only")
    args = ap.parse_args()
    print("Gates")
    run_gates()
    if args.gates:
        return
    table_timeline()
    table_depths()
    table_orphans()
    table_rate()
    table_what_k_buys()
    table_praos()
    table_threshold()
    table_spread()
    table_committee()


if __name__ == "__main__":
    main()
