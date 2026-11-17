# The rows marked "simulated" in RFC 532, "Counting from the tip's slot", at K = 64,800 and
# phi = 1,291 (the floor of 2026-11-17: all of the stake builds, every block T_M = 15 slots late). One block per occupied slot (no forks, no uncles), a slot occupied with chance p.
# B_imm passes the child C while sl(C) + K <= ref and at least phi occupied slots lie in
# (sl(C), sl(tip)]. ref is the clock (clock rule) or the tip's slot (tip rule).
import bisect
import random
import statistics as st

K, PHI = 64800, 1291
F = 1 / 30
P_THIRD = 1 - (1 - F) ** (2 / 3)


def chain(p, horizon, rng):
    return [s for s in range(1, horizon + 1) if rng.random() < p]


def b_imm(slots, n_tip, ref):
    """Index of B_imm among slots[:n_tip] (the chain up to its tip), -1 = genesis.
    The test is monotone along the chain, so it is the last block that passes."""
    tip = n_tip - 1
    by_age = bisect.bisect_right(slots, ref - K, 0, n_tip) - 1      # last block with slot <= ref - K
    by_floor = tip - PHI                                            # phi blocks follow it, the tip included
    return min(by_age, by_floor)


def lag(p, seed):
    rng = random.Random(seed)
    slots = chain(p, 6 * K, rng)
    lags_time, lags_slot = [], []
    # per block C: the slot at which each rule first passes it
    for i in range(len(slots) - PHI - 2):
        if slots[i] < K or slots[i] + K > 5 * K:
            continue
        t_clock = max(slots[i] + K, slots[i + PHI])                 # K old and phi blocks after it
        j = bisect.bisect_left(slots, slots[i] + K)                 # the first block at or past sl(C) + K
        t_tip = max(slots[j], slots[i + PHI])
        lags_time.append(t_tip - t_clock)
    # sampled at every slot: how far B_imm of the tip rule trails that of the clock rule, in slots
    for now in range(2 * K, 5 * K, 7):
        n_tip = bisect.bisect_right(slots, now)
        a, b = b_imm(slots, n_tip, now), b_imm(slots, n_tip, slots[n_tip - 1])
        lags_slot.append(slots[a] - slots[b])
    return st.mean(lags_time), st.mean(lags_slot)


def shift(seed):
    rng = random.Random(seed)
    now = 3 * K
    slots = chain(F, now, rng)
    n = len(slots)
    before = b_imm(slots, n, now)
    tip_before = b_imm(slots, n, slots[-1])
    clock_after = b_imm(slots, n, now + K)                          # the clock steps forward by K
    out = dict(age_before_h=(now - slots[before]) / 3600, depth_before=n - 1 - before,
               tip_age_h=(now - slots[tip_before]) / 3600, tip_depth=n - 1 - tip_before,
               clock_age_after_h=(now - slots[clock_after]) / 3600, clock_depth_after=n - 1 - clock_after)
    # the tip rule: one block at a slot of the shifted range (now, now + K]
    res = []
    for back in (38700, 38000, 30000, 20000, 10000, 1, 39500, 45000, 64000):
        s = now + K - back + 1
        ext = slots + [s]
        b = b_imm(ext, n + 1, s)
        res.append((back, (now - slots[b]) / 3600, n - b, n - 1 - b))   # age, depth below the new tip, below the old tip
    out["tip_after_block"] = res
    return out


def silence(seed):
    rng = random.Random(seed)
    stop = 3 * K
    slots = chain(F, stop, rng)
    n = len(slots)
    clock_rule = b_imm(slots, n, stop + K)                          # K slots pass with no block
    tip_rule = b_imm(slots, n, slots[-1])
    nxt = slots + [stop + K + 30]
    after = b_imm(nxt, n + 1, nxt[-1])
    return n - 1 - clock_rule, n - 1 - tip_rule, n - after


if __name__ == "__main__":
    for name, p in (("f = 1/30", F), ("a third withholds, p_h", P_THIRD)):
        r = [lag(p, s) for s in range(6)]
        print(f"lag, {name}: per block, slots from the clock rule's move to the tip rule's: {st.mean(x[0] for x in r):.1f}; "
              f"sampled, slot(B_imm clock) - slot(B_imm tip): {st.mean(x[1] for x in r):.1f}   [RFC before: about 29, about 44]")
    rs = [shift(s) for s in range(20)]
    for key in ("age_before_h", "depth_before", "tip_age_h", "tip_depth", "clock_age_after_h", "clock_depth_after"):
        print(f"clock step of +K: {key}: mean {st.mean(r[key] for r in rs):.2f}")
    for i, back in enumerate(x[0] for x in rs[0]["tip_after_block"]):
        ages = [r["tip_after_block"][i][1] for r in rs]
        d_new = [r["tip_after_block"][i][2] for r in rs]
        d_old = [r["tip_after_block"][i][3] for r in rs]
        print(f"  tip rule, one block {back} slots before the end of the shifted range: B_imm {st.mean(ages):.2f} h old, "
              f"{st.mean(d_new):.0f} occupied slots below the new tip ({st.mean(d_old):.0f} below the old tip)")
    ss = [silence(s) for s in range(20)]
    print(f"no block for K slots: clock rule {st.mean(x[0] for x in ss):.0f} below the stale tip, tip rule {st.mean(x[1] for x in ss):.0f}; "
          f"after the next block the tip rule stands {st.mean(x[2] for x in ss):.0f} occupied slots below the new tip")
