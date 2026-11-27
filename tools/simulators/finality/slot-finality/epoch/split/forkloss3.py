"""Fork loss when an adversary schedules deliveries within the bound d to keep honest leaders split.

Two classes of honest leaders, half of the stake each. Every block reaches class 0 exactly d slots late. Class 1 gets the competitors of the
first block A of a height (blocks of the same height made by slot a + d) just before A, at a + d, and prefers the last of them; every delivery
is within d of its block. Class 0 extends the first block of the greatest height it holds. Uncles as in forkloss.py.
"""
import math

import numpy as np
from numba import njit

F = 1 / 30
LAM = -math.log(1 - F)
WIN, MAXU = 360, 4


@njit(cache=False)
def simulate(T, rate, d, seed, P, share1):
    np.random.seed(seed)
    cap = int(T * rate * 1.06) + 1000
    slot = np.zeros(cap, np.int64)
    par = np.full(cap, -1, np.int64)
    hgt = np.zeros(cap, np.int64)
    unc = np.full((cap, MAXU), -1, np.int64)
    first = np.full(cap + 2, -1, np.int64)      # first block of a height
    n = 1
    slot[0] = -10 ** 6
    first[0] = 0
    H = 0                                       # greatest height whose first block is at least d + 1 slots old
    maxh = 0
    occ_win = np.zeros(T // P, np.int64)
    anc = np.zeros(1024, np.int64)
    occ = np.zeros(8192, np.int64)
    cand = np.zeros(1024, np.int64)
    for t in range(T):
        while H < maxh and slot[first[H + 1]] <= t - d - 1:
            H += 1
        w = np.random.poisson(rate)
        if w == 0:
            continue
        occ_win[t // P] += 1
        nf = n
        for _ in range(w):
            z = np.random.random() < share1
            A = first[H]
            p = A
            if z:
                b = nf - 1
                while b > A:
                    if hgt[b] == H and slot[b] <= slot[A] + d:
                        p = b
                        break
                    b -= 1
            na = no = 0
            a2 = p
            while a2 >= 0 and slot[a2] >= t - WIN:
                anc[na] = a2
                na += 1
                occ[no] = slot[a2]
                no += 1
                for u in range(MAXU):
                    if unc[a2, u] >= 0:
                        occ[no] = slot[unc[a2, u]]
                        no += 1
                a2 = par[a2]
            nc = 0
            u = nf - 1
            while u > 0 and slot[u] > t - WIN:
                hold = slot[u] <= t - d - 1
                if not hold and z:
                    hu = hgt[u]
                    if hu <= H and slot[u] <= slot[first[hu]] + d:
                        hold = True
                pu = par[u]
                if hold and pu >= 0 and slot[pu] >= t - WIN:
                    is_anc = par_in = False
                    for q in range(na):
                        if anc[q] == u:
                            is_anc = True
                        if anc[q] == pu:
                            par_in = True
                    if par_in and not is_anc:
                        taken = False
                        for q in range(no):
                            if occ[q] == slot[u]:
                                taken = True
                                break
                        if not taken:
                            cand[nc] = u
                            nc += 1
                u -= 1
            b = n
            n += 1
            slot[b] = t
            par[b] = p
            hgt[b] = hgt[p] + 1
            if hgt[b] > maxh:
                maxh = hgt[b]
                first[maxh] = b
            chosen = 0
            used = np.zeros(nc, np.int64)
            for _s in range(nc):
                bi = -1
                for q in range(nc):
                    if used[q]:
                        continue
                    if bi < 0:
                        bi = q
                        continue
                    x, y = cand[q], cand[bi]
                    if (slot[par[x]], slot[x], x) < (slot[par[y]], slot[y], y):
                        bi = q
                if bi < 0 or chosen == MAXU:
                    break
                used[bi] = 1
                dup = False
                for q in range(chosen):
                    if slot[unc[b, q]] == slot[cand[bi]]:
                        dup = True
                if not dup:
                    unc[b, chosen] = cand[bi]
                    chosen += 1
    tip = first[maxh]
    canon = np.zeros(n, np.uint8)
    a3 = tip
    while a3 >= 0:
        canon[a3] = 1
        a3 = par[a3]
    cnt = np.zeros(T // P, np.int64)
    mark = np.zeros(T + 1, np.uint8)
    for b in range(1, n):
        if canon[b] and slot[b] // P < cnt.size and mark[slot[b]] == 0:
            mark[slot[b]] = 1
            cnt[slot[b] // P] += 1
    for b in range(1, n):
        if not canon[b]:
            continue
        wi = slot[b] // P
        if wi >= cnt.size:
            continue
        for u in range(MAXU):
            x2 = unc[b, u]
            if x2 >= 0 and slot[x2] // P == wi and mark[slot[x2]] == 0:
                mark[slot[x2]] = 1
                cnt[wi] += 1
    nc2 = 0
    for b in range(1, n):
        nc2 += canon[b]
    return occ_win, cnt, n - 1, nc2


if __name__ == "__main__":
    T, P = 144000 * 60, 144000
    simulate(20000, LAM, 15, 1, 10000, 0.5)
    for d in (5, 10, 12, 15):
        for share1 in (0.0, 0.5):
            oc, cc, bl, ca = [], [], 0, 0
            for s in (1, 2, 3):
                o, c, nb, nc = simulate(T, LAM, d, s, P, share1)
                oc.append(o)
                cc.append(c)
                bl += nb
                ca += nc
            o, c = np.concatenate(oc), np.concatenate(cc)
            cov = c.sum() / o.sum()
            per = 1 - c / o
            print(f"delay bound {d} s, class 1 holds {share1:.1f}: loss {100 * (1 - cov):.3f} % (sem {100 * per.std(ddof=1) / math.sqrt(len(per)):.3f} %)"
                  f" -> D/S {math.log(1 - F) / math.log(1 - F / cov):.4f} | off-chain {100 * (1 - ca / bl):.2f} %", flush=True)
