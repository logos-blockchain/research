"""The survival law of Theorem 6.1 against the study's `branch_survival` (SURVIVAL.md, sections 7 and 9).

For each state and T = 1..10 hours:
  Qhat(T)  the proved bound (Theorem 6.1), from above and from below (Lemmas 6.4 to 6.6);
  Q1(T)    P(some t >= T has X(t) >= 1), the strict lead (section 9.3);
  Q(T)     P(some t >= T has X(t) >= 0), the bound without the tie argument (Corollary 6.2);
  study    the finality study's branch_survival(f', alpha, T, delta = d), read only;
  Lemma 6.7, the closed-form bound C lambda^T.
Part 2 recomputes the study's law from its formula as section 9.1 reads it,
P(Bin(T, a) + Y + M >= N_T + 1), with this folder's laws of Y and M and the negative binomial law of
N_T, to confirm that reading. Part 3 forms the law of N_T from survival functions in place of
differences of distribution functions near 1, and shows where branch_survival loses digits.
Part 4 splits the difference of section 9.2 into its two departures, each taken alone, from the law
of the state (X(T), k_T, F_T) of Lemma 6.5:
  pending block counted at its count, alone:  E[qhat(X(T), k_T)]  (no credit for a tie);
  tie credit alone:                           E[F_T + (1 - F_T) q_s(X(T), k_T)],
with q_s(x, k) = P(x - [k >= 1] + Y + M >= 1), the study's chance from the state (section 9.2).
E[q_s(X(T), k_T)] recomputes the study's law from the same state, as a check.
Usage: python s2_survival.py > out_2_survival.txt
"""
import sys

import numpy as np
from scipy.stats import binom, nbinom

from sv_common import (H, STATE, STATES, STUDY_SRC, chernoff, forward_snapshots, max_law, qhat_table, rates, ranges,
                       study_params, survival_curves, tail_fn, y_law)

sys.path.insert(0, STUDY_SRC)
from finality_sim.formation import branch_survival   # noqa: E402

T_END = 20 * H
HOURS = (1, 2, 3, 4, 5, 6, 8, 10)


def study_formula(h, a, d, T, tail_up):
    """P(Bin(T, a) + Y + M >= N_T + 1), all independent; N_T the greedy d-isolated honest wins in
    1..T after a block at slot 0: P(N_T >= n) = P(NB(n, h) <= T - n (d + 1))."""
    y, _ = y_law(h, a, d)
    pm = -np.diff(np.append(tail_up, 0.0))                   # P(M = m)
    up = np.convolve(np.convolve(binom.pmf(np.arange(T + 1), T, a), y), pm)
    sf = np.cumsum(up[::-1])[::-1]                           # P(sum >= j)
    n = np.arange(T // (d + 1) + 2)
    at_least = np.ones(n.size)
    at_least[1:] = nbinom.cdf(T - n[1:] * (d + 1), n[1:], h)
    pn = at_least - np.append(at_least[1:], 0.0)
    need = n + 1
    ok = need < sf.size
    return float(np.sum(pn[ok] * sf[need[ok]]))


def qs_table(h, a, d, tail, x_lo, x_hi, upper=True):
    """q_s[x - x_lo, k] = P(x - [k >= 1] + Y + M >= 1): the study's chance from the state (section 9.2).
    From above the mass of Y beyond its support counts as success; from below it is dropped."""
    tM = tail_fn(tail, upper)
    y, y_tail = y_law(h, a, d)
    extra = y_tail if upper else 0.0
    rr = np.arange(y.size)
    xs = np.arange(x_lo, x_hi + 1)
    q = np.ones((xs.size, d + 1))
    for i, x in enumerate(xs):
        for k in range(d + 1):
            need = 1 - x + (1 if k >= 1 else 0)          # Y + M >= need
            if need <= 0:
                continue
            q[i, k] = min(1.0, float(np.sum(y * tM(need - rr))) + extra)
    return q


def split(h, a, d, hours):
    """For T at the given hours: (Qhat, the pending block alone, the tie credit alone, the study's law
    from the state), from below and from above (Lemma 6.5 and section 9.2)."""
    low, up, _ = max_law(h, a, d)
    x_lo, x_hi = ranges(h, a, d)
    times = [hr * H for hr in hours]
    out = {}
    for side, tail, upper in (("low", low, False), ("up", up, True)):
        qh = qhat_table(h, a, d, tail, x_lo, x_hi, upper=upper)
        qs = qs_table(h, a, d, tail, x_lo, x_hi, upper=upper)
        snaps = forward_snapshots(h, a, d, times, x_lo, x_hi, upper=upper)
        for T in times:
            P0, P1, over = snaps[T]
            tot = P0 + P1
            out[(side, T)] = (float(P1.sum() + np.sum(P0 * qh)) + over,      # Qhat (Lemma 6.6)
                              float(np.sum(tot * qh)) + over,                 # pending block at its count, alone
                              float(P1.sum() + np.sum(P0 * qs)) + over,       # tie credit alone
                              float(np.sum(tot * qs)) + over)                 # the study's law from the state
    return out


if __name__ == "__main__":
    print("1. survival by T: Qhat from above (from below) | Q1 | Q | the study's law | Qhat / study, Q1 / study, Q / study | Lemma 6.7")
    ratios = {"Qhat": [], "Q1": [], "Q": []}
    for key, label, xh, xa, d, _, _ in STATES:
        h, a = rates(xh, xa)
        fp, al = study_params(xh, xa)
        res = survival_curves(h, a, d, T_END, lower=True)
        th, rho, lam, C = chernoff(h, a, d)
        print(f"   {label} (x_h = {xh:.4f}, x_a = {xa:.4f}, d = {d}; kept range of X: {res['x_lo']}..{res['x_hi']})")
        for hr in HOURS:
            T = hr * H
            st = branch_survival(fp, al, T, delta=d)
            qh, ql, q1, q = res["Qhat"][T], res["Qhat_low"][T], res["Q1"][T], res["Q"][T]
            print(f"     T = {hr:2d} h: Qhat {qh:.4e} ({ql:.4e}) | Q1 {q1:.4e} | Q {q:.4e} | study {st:.4e} | "
                  f"{qh / st:.4f}, {q1 / st:.4f}, {q / st:.4f} | {C * lam ** T:.3e}")
            if hr <= 6:                               # part 3: below about 1e-20 the study's code loses digits
                assert abs(qh - ql) <= 1e-3 * qh
                ratios["Qhat"].append(ql / st)
                ratios["Q1"].append(q1 / st)
                ratios["Q"].append(q / st)
    print(f"   over T = 1..6 h in every state ({len(ratios['Qhat'])} rows; from above and below agree to 0.1 % in each): "
          f"Qhat (from below) / study from {min(ratios['Qhat']):.4f} to {max(ratios['Qhat']):.4f}; "
          f"Q1 / study from {min(ratios['Q1']):.4f} to {max(ratios['Q1']):.4f}; Q / study from {min(ratios['Q']):.4f} to {max(ratios['Q']):.4f}")

    print("\n2. the study's law recomputed from the formula of section 9.1, against branch_survival")
    worst = 0.0
    for key, label, xh, xa, d, _, _ in STATES:
        h, a = rates(xh, xa)
        fp, al = study_params(xh, xa)
        _, tail_up, _ = max_law(h, a, d)
        cells = []
        for hr in (1, 3, 5):
            T = hr * H
            mine, theirs = study_formula(h, a, d, T, tail_up), branch_survival(fp, al, T, delta=d)
            worst = max(worst, abs(mine - theirs) / theirs)
            cells.append(f"T = {hr} h: {mine:.6e} against {theirs:.6e}")
        print(f"   {label}: " + " | ".join(cells))
    print(f"   largest relative difference: {worst:.1e}")

    print("\n3. the study's formula with P(N_T = n) = P(tau_(n+1) > T) - P(tau_n > T) from survival functions, against "
          "branch_survival, whose blocks_pmf takes differences of distribution functions near 1")
    for key in ("none", "defl"):
        _, label, xh, xa, d, _, _ = STATE[key]
        h, a = rates(xh, xa)
        fp, al = study_params(xh, xa)
        _, tail_up, _ = max_law(h, a, d)
        y, _ = y_law(h, a, d)
        pm = -np.diff(np.append(tail_up, 0.0))
        cells = []
        for hr in (6, 8, 10):
            T = hr * H
            up = np.convolve(np.convolve(binom.pmf(np.arange(T + 1), T, a), y), pm)
            sf = np.cumsum(up[::-1])[::-1]
            n = np.arange(T // (d + 1) + 2)
            later = np.zeros(n.size)
            later[1:] = nbinom.sf(T - n[1:] * (d + 1), n[1:], h)
            pn = np.append(later[1:], 1.0) - later
            need = n + 1
            ok = need < sf.size
            acc = float(np.sum(pn[ok] * sf[need[ok]]))
            cells.append(f"T = {hr} h: {acc:.4e} against {branch_survival(fp, al, T, delta=d):.4e}")
        print(f"   {label}: " + " | ".join(cells))

    print("\n4. each departure of section 9.2 alone, from the law of the state at T, against branch_survival: "
          "pending block counted at its count (no tie credit) | tie credit alone | Qhat | the study's law from the state; "
          "values from below, T = 1..6 h")
    SPLIT_HOURS = (1, 2, 3, 4, 5, 6)
    r_pend, r_tie, r_chk, r_chk4, gap = [], [], [], [], 0.0
    for key, label, xh, xa, d, _, _ in STATES:
        h, a = rates(xh, xa)
        fp, al = study_params(xh, xa)
        sp = split(h, a, d, SPLIT_HOURS)
        cells = []
        for hr in SPLIT_HOURS:
            T = hr * H
            st = branch_survival(fp, al, T, delta=d)
            qh, pend, tie, chk = sp[("low", T)]
            for lo, hi in zip(sp[("low", T)], sp[("up", T)]):
                gap = max(gap, (hi - lo) / hi)
            r_pend.append(pend / st)
            r_tie.append(tie / st)
            r_chk.append(abs(chk / st - 1))
            if hr <= 4:
                r_chk4.append(abs(chk / st - 1))
            cells.append(f"T = {hr} h: {pend / st:.4f}, {tie / st:.4f}, {qh / st:.4f}, {chk / st:.7f}")
        print(f"   {label}: " + " | ".join(cells))
    print(f"   over T = 1..6 h in every state ({len(r_pend)} rows; from above and below agree to {gap:.1e} relative): "
          f"pending block alone / study from {min(r_pend):.4f} to {max(r_pend):.4f}; tie credit alone / study from "
          f"{min(r_tie):.4f} to {max(r_tie):.4f}; the study's law from the state differs from branch_survival by at most "
          f"{max(r_chk4):.1e} at 1 to 4 h and {max(r_chk):.1e} at 1 to 6 h")
