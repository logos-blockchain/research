"""Fork loss with a separate arrival time of every block at every leader (a second model, beside forkloss.py).

A leader of slot t holds a block if it arrived by t. Arrival = broadcast time + a private final leg.
 mode "blend": broadcast time = slot + 3 transport legs + 3 uniforms on (0, dmax); final leg ~ Normal(1.21, 0.26) cut at 0.1 (the gossip
   distances of the uncle study's 1,000-node graph: mean 1.21, sd 0.28; two relays differ at a node by sd 0.36 = 0.26 * sqrt 2).
 mode "fixed": arrival = slot + d + a private leg uniform on (-j, 0): every block up to d late, the last j seconds private.
 mode "uniform": arrival = slot + uniform(0, d), private to each leader: an adversary that delays each delivery at random within the bound.
The leader extends the longest chain it holds, the one that arrived first among equals. Each leader is a new node (no own block in flight).
Uncles as in forkloss.py. Usage: python forkloss2.py
"""
import math
import time

import numpy as np
from numba import njit

F = 1 / 30
LAM = -math.log(1 - F)
WIN, MAXU = 360, 4


@njit(cache=False)
def simulate(T, rate, mode, d, dmax, j, seed, P, look):
    np.random.seed(seed)
    cap = int(T * rate * 1.06) + 1000
    slot = np.zeros(cap, np.int64)
    par = np.full(cap, -1, np.int64)
    hgt = np.zeros(cap, np.int64)
    bt = np.zeros(cap)
    unc = np.full((cap, MAXU), -1, np.int64)
    n = 1
    slot[0] = -1
    bt[0] = -1e9
    base = 0                                # every block before this index is held by everyone
    occ_win = np.zeros(T // P, np.int64)
    arr = np.zeros(4096)
    held = np.zeros(4096, np.uint8)
    anc = np.zeros(1024, np.int64)
    occ = np.zeros(8192, np.int64)
    cand = np.zeros(1024, np.int64)
    sure_tip = 0                            # highest block held by everyone, first by broadcast time
    for t in range(T):
        w = np.random.poisson(rate)
        if w == 0:
            continue
        occ_win[t // P] += 1
        new_first = n
        for _ in range(w):
            # recent blocks: those with slot >= t - look
            lo = new_first
            while lo > 1 and slot[lo - 1] >= t - look:
                lo -= 1
            best = -1
            besth = -1
            besta = 0.0
            for b in range(lo, new_first):
                if mode == 0:
                    a = bt[b] + max(0.1, 1.21 + 0.26 * np.random.randn())
                elif mode == 1:
                    a = slot[b] + d - j * np.random.random()
                else:
                    a = slot[b] + d * np.random.random()
                k = b - lo
                arr[k] = a
                pb = par[b]
                okp = pb < lo or held[pb - lo] == 1
                held[k] = 1 if (a <= t and okp) else 0
                if pb >= lo and arr[pb - lo] > a:
                    arr[k] = arr[pb - lo]
                    if arr[k] > t:
                        held[k] = 0
                if held[k] and (hgt[b] > besth or (hgt[b] == besth and arr[k] < besta)):
                    best, besth, besta = b, hgt[b], arr[k]
            # older blocks: everyone holds them; the best of them
            k = lo - 1
            stop = max(0, lo - 60)
            while k >= stop:
                if hgt[k] > besth or (hgt[k] == besth and best >= lo):
                    if hgt[k] > besth:
                        best, besth = k, hgt[k]
                        besta = bt[k]
                    else:
                        best = k
                        besta = bt[k]
                elif hgt[k] == besth and best < lo and bt[k] < besta:
                    best, besta = k, bt[k]
                k -= 1
            p = best if best >= 0 else 0
            na = 0
            no = 0
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
            u = new_first - 1
            while u > 0 and slot[u] > t - WIN:
                hold = True
                if u >= lo:
                    hold = held[u - lo] == 1
                pu = par[u]
                if hold and pu >= 0 and slot[pu] >= t - WIN:
                    is_anc = False
                    par_in = False
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
            if mode == 0:
                x = float(t)
                for _h in range(3):
                    x += max(0.1, 1.21 + 0.28 * np.random.randn()) + np.random.random() * dmax
                bt[b] = x
            else:
                bt[b] = t + d
    tip = 0
    for b in range(1, n):
        if hgt[b] > hgt[tip]:
            tip = b
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


def fixed_ratio(c):
    return math.log(1 - F) / math.log(1 - F / c)


def run(label, T, mode, d=0.0, dmax=0.0, j=0.0, look=60, seeds=(1, 2, 3), P=144000, r=1.0):
    oc, cc = [], []
    blocks = canon = 0
    for s in seeds:
        o, c, nb, nc = simulate(T, LAM * r, mode, d, dmax, j, s, P, look)
        oc.append(o)
        cc.append(c)
        blocks += nb
        canon += nc
    o, c = np.concatenate(oc), np.concatenate(cc)
    cov = c.sum() / o.sum()
    per = 1 - c / o
    print(f"{label}: loss {100 * (1 - cov):.4f} % (sem {100 * per.std(ddof=1) / math.sqrt(len(per)):.4f} %) -> D/S {fixed_ratio(cov):.5f} | "
          f"off-chain {100 * (1 - canon / blocks):.2f} %", flush=True)


if __name__ == "__main__":
    T = 144000 * 60
    simulate(20000, LAM, 0, 15.0, 3.0, 0.0, 1, 10000, 60)
    t0 = time.time()
    for dmax in (2.0, 3.0, 4.0, 6.0, 6.8, 8.0, 16.0, 32.0):
        run(f"blend, uniform to {dmax:g} s a hop, mean {1.5 * dmax + 4.84:.1f} s", T, 0, dmax=dmax, look=int(3 * dmax) + 40)
    for d in (10.0, 12.0, 15.0):
        for j in (0.0, 1.0, 2.0, 5.0):
            run(f"fixed {d:g} s, the last {j:g} s private", T, 1, d=d, j=j, look=int(d) + 40)
        run(f"uniform on (0, {d:g} s), private", T, 2, d=d, look=int(d) + 40)
    print(f"({time.time() - t0:.0f} s)")
