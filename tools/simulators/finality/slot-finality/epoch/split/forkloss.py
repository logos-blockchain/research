"""Share of occupied slots that the stake inference does not count, under the specification's uncle rules.

Model. Every slot has Poisson(-ln(1-f) * r) winners, r = S/D, each a separate leader with no block of its own in flight.
A block of slot t is visible to every leader from slot t + 1 + delay on. A leader extends the longest visible chain; a tie keeps the
chain seen first ("common"), or is broken at random for each leader ("split"). Uncles: protocol, Uncle References and Uncle
Selection (parent on the chain, at most 360 slots from the parent to the referencing block, at most 4, oldest parent first, only
new slots). The count of a window: canonical blocks of the window and the uncles they carry whose slots lie in the window.
Usage: python forkloss.py
"""
import math
import sys
import time

import numpy as np
from numba import njit

F = 1 / 30
LAM = -math.log(1 - F)
WIN, MAXU = 360, 4


@njit(cache=False)
def simulate(T, rate, mode, d_fixed, dmax, hops, gossip, split, seed, P):
    """mode 0: fixed delay d_fixed. mode 1: sum of `hops` uniforms on (0, dmax) plus `gossip`."""
    np.random.seed(seed)
    cap = int(T * rate * 1.06) + 1000
    slot = np.zeros(cap, np.int64)
    par = np.full(cap, -1, np.int64)
    hgt = np.zeros(cap, np.int64)
    vis = np.zeros(cap, np.int64)
    unc = np.full((cap, MAXU), -1, np.int64)
    n = 1                                  # block 0: genesis at slot -1
    slot[0] = -1
    tip = 0
    order = np.zeros(cap, np.int64)        # blocks in the order they became visible
    m = 1
    pend = np.zeros(4096, np.int64)
    np_ = 0
    tips = np.zeros(64, np.int64)          # visible blocks of the greatest height
    ntips = 1
    anc = np.zeros(1024, np.int64)
    occ = np.zeros(8192, np.int64)
    cand = np.zeros(1024, np.int64)
    occupied = 0
    occ_win = np.zeros(T // P, np.int64)
    for t in range(T):
        # make blocks visible
        if np_ > 0:
            k = 0
            while k < np_:
                b = pend[k]
                if vis[b] <= t:
                    order[m] = b
                    m += 1
                    if hgt[b] > hgt[tip]:
                        tip = b
                        tips[0] = b
                        ntips = 1
                    elif hgt[b] == hgt[tip] and ntips < 64:
                        tips[ntips] = b
                        ntips += 1
                    for j in range(k, np_ - 1):
                        pend[j] = pend[j + 1]
                    np_ -= 1
                else:
                    k += 1
        w = np.random.poisson(rate)
        if w == 0:
            continue
        occupied += 1
        occ_win[t // P] += 1
        for _ in range(w):
            p = tip
            if split and ntips > 1:
                p = tips[np.random.randint(ntips)]
            # ancestors with slot >= t - WIN, and the slots they occupy
            na = 0
            no = 0
            a = p
            while a >= 0 and slot[a] >= t - WIN:
                anc[na] = a
                na += 1
                occ[no] = slot[a]
                no += 1
                for u in range(MAXU):
                    if unc[a, u] >= 0:
                        occ[no] = slot[unc[a, u]]
                        no += 1
                a = par[a]
            # candidates: visible blocks whose parent is one of the ancestors, not ancestors themselves
            nc = 0
            k = m - 1
            seen_old = 0
            while k >= 0 and seen_old < 40:
                u = order[k]
                k -= 1
                if slot[u] <= t - WIN:
                    seen_old += 1
                    continue
                pu = par[u]
                if pu < 0 or slot[pu] < t - WIN:
                    continue
                is_anc = False
                par_in = False
                for j in range(na):
                    if anc[j] == u:
                        is_anc = True
                    if anc[j] == pu:
                        par_in = True
                if is_anc or not par_in:
                    continue
                taken = False
                for j in range(no):
                    if occ[j] == slot[u]:
                        taken = True
                        break
                if taken:
                    continue
                cand[nc] = u
                nc += 1
            b = n
            n += 1
            slot[b] = t
            par[b] = p
            hgt[b] = hgt[p] + 1
            # select: oldest parent first, then slot, then index; distinct slots
            chosen = 0
            used = np.zeros(nc, np.int64)
            for _s in range(nc):
                best = -1
                for j in range(nc):
                    if used[j]:
                        continue
                    if best < 0:
                        best = j
                        continue
                    x, y = cand[j], cand[best]
                    kx = (slot[par[x]], slot[x], x)
                    ky = (slot[par[y]], slot[y], y)
                    if kx < ky:
                        best = j
                if best < 0 or chosen == MAXU:
                    break
                used[best] = 1
                u = cand[best]
                dup = False
                for j in range(chosen):
                    if slot[unc[b, j]] == slot[u]:
                        dup = True
                if not dup:
                    unc[b, chosen] = u
                    chosen += 1
            if mode == 0:
                vis[b] = t + 1 + d_fixed
            else:
                dl = gossip
                for _h in range(hops):
                    dl += np.random.random() * dmax
                vis[b] = t + 1 + int(dl)
            pend[np_] = b
            np_ += 1
    # final chain
    canon = np.zeros(n, np.uint8)
    a = tip
    while a >= 0:
        canon[a] = 1
        a = par[a]
    cnt = np.zeros(T // P, np.int64)
    mark = np.zeros(T + 1, np.uint8)
    # window by window count, distinct slots
    for b in range(1, n):
        if not canon[b]:
            continue
        wi = slot[b] // P
        if wi < cnt.size and mark[slot[b]] == 0:
            mark[slot[b]] = 1
            cnt[wi] += 1
    for b in range(1, n):
        if not canon[b]:
            continue
        wi = slot[b] // P
        if wi >= cnt.size:
            continue
        for u in range(MAXU):
            x = unc[b, u]
            if x >= 0 and slot[x] // P == wi and mark[slot[x]] == 0:
                mark[slot[x]] = 1
                cnt[wi] += 1
    # lost slots by the depth of the block below the final chain (1: parent canonical)
    lost = np.zeros(8, np.int64)
    last = -1
    for b in range(1, n):
        if canon[b] or mark[slot[b]] or slot[b] // P >= cnt.size:
            continue
        if slot[b] == last:
            continue
        last = slot[b]
        dep = 1
        a = par[b]
        while a >= 0 and not canon[a]:
            dep += 1
            a = par[a]
        lost[min(dep, 7)] += 1
    ncanon = 0
    for b in range(1, n):
        ncanon += canon[b]
    return occupied, occ_win, cnt, lost, n - 1, ncanon


def fixed_ratio(c):
    """D/S at which c * q(S/D) = f."""
    return math.log(1 - F) / math.log(1 - F / c)


def run(label, T, r, mode, d, dmax=0.0, hops=3, gossip=0.0, split=False, seeds=(1, 2, 3), P=144000):
    occ_tot = cnt_tot = 0
    allc, allo, lost = [], [], np.zeros(8, np.int64)
    blocks = canon = 0
    for s in seeds:
        o, ow, c, l, nb, nc = simulate(T, LAM * r, mode, d, dmax, hops, gossip, split, s, P)
        allc.append(c)
        allo.append(ow)
        lost += l
        blocks += nb
        canon += nc
    c = np.concatenate(allc)
    o = np.concatenate(allo)
    cov = c.sum() / o.sum()
    per = 1 - c / o
    sem = per.std(ddof=1) / math.sqrt(len(per))
    q = -math.expm1(math.log1p(-F) * r)
    var_ratio = c.var(ddof=1) / (P * cov * q * (1 - cov * q))
    print(f"{label}: loss {100 * (1 - cov):.4f} % (sem {100 * sem:.4f} %) -> D/S {fixed_ratio(cov):.5f} | var of the count over binomial "
          f"{var_ratio:.3f} ({len(c)} windows) | off-chain blocks {100 * (1 - canon / blocks):.2f} % | lost slots by depth 1..4: "
          f"{[int(x) for x in lost[1:5]]}", flush=True)
    return cov


if __name__ == "__main__":
    T = 144000 * 100
    simulate(20000, LAM, 0, 15, 0.0, 3, 0.0, False, 1, 10000)
    t0 = time.time()
    for split in (False, True):
        print("ties:", "each leader picks at random" if split else "first seen, the same for all")
        for d in (5, 10, 12, 15, 17, 20):
            run(f"  fixed delay {d} s", T, 1.0, 0, d, split=split)
        for dmax in (3.0, 4.0, 8.0):
            run(f"  Blend: 3 hops, uniform to {dmax:g} s, gossip 4.84 s, mean {1.5 * dmax + 4.84:.1f} s", T, 1.0, 1, 0, dmax=dmax, gossip=4.84,
                split=split)
    print("at S/D = 1.094, fixed 15 s:")
    run("  first seen", T, 1.094, 0, 15)
    run("  split", T, 1.094, 0, 15, split=True)
    print(f"({time.time() - t0:.0f} s)")
