"""PROOF.md, sections 1-3: the constants, the two-phase schedule, statement 2.2 (one epoch state for
G + 1 slots after a divergence, for any two-phase schedule) and statement 5.1 (which parts of the state
a fork can derive differently, and where).

(a) the constants, read with git from the specification at 83596b6e, with their lines, and the lines of
    each text that differ from GENESIS's commit 7f3cf149;
(b) the schedules: the conditions s <= K - 1, s + K <= G + 1, K <= G + 1, 2K <= G + 1, E >= 2K - 2;
(c) the span of shared state after a divergence slot sigma_0, computed exactly for every sigma_0 of an
    epoch from the schedule (the state of slot t reads only blocks with slots below the cut-off of the
    epoch before t's epoch): its least value and where it is attained;
(d) a literal implementation of compute_epoch_state (snapshot, nonce hash chain, occupied-slot count, D
    by the integer inference) on random pairs of chains that share exactly the blocks up to sigma_0,
    for small schedules: the state of every slot up to sigma_0 + G + 1 agrees, and in the first epoch
    that can differ only the nonce and D differ, never the snapshot;
(e) for Step 2 of 7.1: the divergence slots sigma_0 from which a fork whose tip lies at most
    sigma_0 + 2K - 2 can reach a slot whose state it derives from its own blocks, and the length of
    that stretch.
Usage: python t1_schedule.py > out_1_schedule.txt
"""
import hashlib
import random

from common_s import (F_HAT, K, K_SEC, S, SCHEDULES, SPEC_REF, SPEC_SCHEDULE, GENESIS_G, git_show)


def show_constants():
    proto = git_show("cryptarchia-v1-protocol.md")
    fc = git_show("fork-choice.md")
    inf = git_show("cryptarchia-total-stake-inference.md")
    print(f"(a) the specification at {SPEC_REF} (git show {SPEC_REF}:docs/blockchain/raw/<path>)")
    for path, lines, nums in (("protocol", proto, (103, 104, 105, 154, 155, 157, 159, 197, 225, 229, 237, 245)),
                              ("fork choice", fc, (80, 127, 137)),
                              ("inference", inf, (55, 56, 77, 80, 81, 83, 84, 85, 87))):
        for n in nums:
            txt = lines[n - 1].strip()
            print(f"  {path} {n}: {txt[:170]}{' ...' if len(txt) > 170 else ''}")
    print(f"  so f = 1/30, k = {K_SEC}, K = {K}, s = floor(k/(4f)) = {S}, f_hat = truncate(1000 f)/1000 = {F_HAT}, "
          f"snapshot phase = LCF phase = PERIOD = 2K = {2 * K}, beta = 2/3")
    # against GENESIS's commit 7f3cf149: which lines differ
    import difflib
    for path in ("fork-choice.md", "cryptarchia-v1-bootstr-sync.md", "cryptarchia-proof-of-leadership.md",
                 "cryptarchia-v1-protocol.md", "cryptarchia-total-stake-inference.md"):
        old, new = git_show(path, "7f3cf149"), git_show(path)
        changed = []
        for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_opcodes():
            if tag != "equal":
                changed.append(f"{i1 + 1}-{i2} -> {j1 + 1}-{j2}" if (i2 - i1 != 1 or j2 - j1 != 1) else f"{j1 + 1}")
        print(f"  {path}: 7f3cf149 -> {SPEC_REF}: " + ("identical" if not changed else
              f"{len(old)} -> {len(new)} lines, changed (old -> new line ranges): " + ", ".join(changed)))


def span_table(P, G):
    """For every divergence slot sigma0 of epoch 1 (epochs 0..3), the number of slots after sigma0 whose
    state reads only blocks with slots <= sigma0. Returns (least span, the sigma0 offsets attaining it)."""
    E = P + G
    best, arg = None, []
    for sigma0 in range(E, 2 * E):
        e = sigma0 // E
        c_e = e * E + P
        t_star = (e + 2) * E if sigma0 >= c_e - 1 else (e + 1) * E     # first slot of an epoch that reads beyond
        # brute confirmation on the epoch boundaries: the state of slot t reads slots < c_{ep(t)-1}
        span = t_star - sigma0 - 1
        if best is None or span < best:
            best, arg = span, [sigma0 - e * E]
        elif span == best:
            arg.append(sigma0 - e * E)
    return best, arg


def show_schedules():
    print("\n(b) the schedules (P = snapshot phase = PERIOD, G = gap from the cut-off to the next epoch, E = P + G)")
    rows = [("(i) G = s + K - 1, P = 54,000", 54_000, SCHEDULES["(i) G = s + K - 1"][1]),
            ("(i) G = s + K - 1, P = 72,000", 72_000, SCHEDULES["(i) G = s + K - 1"][1]),
            ("(ii) 1.5K + 1.5K", *SCHEDULES["(ii) 1.5K + 1.5K"]),
            ("the specification at 83596b6e, 2K + 2K", *SPEC_SCHEDULE),
            ("GENESIS's schedule (3, 3, 4 floor(k/f); cut-off at 6 floor(k/f))", 388_800, GENESIS_G)]
    for name, P, G in rows:
        E = P + G
        print(f"  {name}: P = {P}, G = {G}, E = {E}; s <= K - 1: {S <= K - 1}; s + K <= G + 1: {S + K <= G + 1} "
              f"(s + K = {S + K}, G + 1 = {G + 1}); K <= G + 1: {K <= G + 1}; 2K <= G + 1: {2 * K <= G + 1}; "
              f"E >= 2K - 2: {E >= 2 * K - 2}")
    print(f"  the least G with s + K <= G + 1 is s + K - 1 = {S + K - 1}; the least with 2K <= G + 1 is 2K - 1 = {2 * K - 1}")


def show_spans():
    print("\n(c) the least span of shared state after a divergence slot, over every divergence slot of an epoch")
    for name, P, G in (("(i), P = 54,000", 54_000, S + K - 1), ("(i), P = 72,000", 72_000, S + K - 1),
                       ("(ii)", 54_000, 54_000), ("specification", 2 * K, 2 * K)):
        best, arg = span_table(P, G)
        print(f"  {name}: least span {best} = G + 1 = {G + 1}: {best == G + 1}; attained at the divergence slot(s) "
              f"{arg} of the epoch, the cut-off minus 2 = {P - 2}")


# ---------------------------------------------------------------------------------------------------
# (d) literal compute_epoch_state on small schedules
# ---------------------------------------------------------------------------------------------------
def infer(D, N, P, num=2, den=3):
    """inference 77-87 with f_p = 33, PRECISION = 1000, beta = num/den, integer division toward zero."""
    def tdiv(a, b):
        q = abs(a) // abs(b)
        return q if (a >= 0) == (b > 0) else -q
    tse_p = D * 1000
    measured = N * 1000
    expected = P * 33
    diff = expected - measured
    err = tdiv(tse_p * diff, expected)
    corr = tdiv(num * err, den)
    return max(tdiv(tse_p - corr, 1000), 1)


def make_state_fn(P, G, D0=10 ** 6):
    E = P + G

    def nonce(chain_slots, upto):
        h = b"genesis"
        for sl, bid in chain_slots:
            if sl < upto:
                h = hashlib.sha256(h + bid + sl.to_bytes(8, "little")).digest()
        return h

    def state(chain_slots, ep):
        """chain_slots: sorted list of (slot, block id) of the chain (genesis excluded)."""
        if ep == 0:
            return ("genesis", b"genesis", D0)
        s0 = (ep - 1) * E
        snap = frozenset(b for sl, b in chain_slots if sl < s0)            # root at s0 (REVIEW A4)
        eta = nonce(chain_slots, s0 + P)
        n = len({sl for sl, _ in chain_slots if s0 <= sl < s0 + P})        # occupied slots in the window
        _, _, d_prev = state(chain_slots, ep - 1)
        return (snap, eta, infer(d_prev, n, P))
    return state, E


def check_states(rng, P, G, n_pairs=4000, horizon_epochs=4, density=0.3):
    """Returns (slot states equal in (sigma0, sigma0 + G + 1], different there, counts at the epoch after
    sigma0's when it is the first that differs {snapshot, nonce, D}, violations of: the first differing
    epoch is e + 1 only if sigma0 <= c_e - 2 and is never e or earlier, least shared span observed)."""
    state, E = make_state_fn(P, G)
    n_ok = n_bad = 0
    diff_parts = {"snapshot": 0, "nonce": 0, "D": 0, "pairs": 0}
    violations = 0
    least_reach = None
    for _ in range(n_pairs):
        sigma0 = rng.randrange(0, (horizon_epochs - 2) * E)
        # the shared chain ends in the divergence block, at slot sigma0 (genesis if sigma0 = 0)
        shared = [(sl, b"s%d" % sl) for sl in range(1, sigma0) if rng.random() < density]
        if sigma0 > 0:
            shared.append((sigma0, b"s%d" % sigma0))
        a = shared + [(sl, b"a%d" % sl) for sl in range(sigma0 + 1, horizon_epochs * E) if rng.random() < density]
        b = shared + [(sl, b"b%d" % sl) for sl in range(sigma0 + 1, horizon_epochs * E) if rng.random() < density]
        e = sigma0 // E
        for t in range(sigma0 + 1, min(sigma0 + G + 2, horizon_epochs * E)):
            if state(a, t // E) == state(b, t // E):
                n_ok += 1
            else:
                n_bad += 1
        # the first slot whose state differs, and what differs there
        t = sigma0 + 1
        while t < horizon_epochs * E and state(a, t // E) == state(b, t // E):
            t = (t // E + 1) * E
        if t < horizon_epochs * E:
            reach = t - sigma0 - 1
            least_reach = reach if least_reach is None else min(least_reach, reach)
            ep1 = t // E
            if ep1 <= e or (ep1 == e + 1 and sigma0 > e * E + P - 2):
                violations += 1
            if ep1 == e + 1:
                sa, sb = state(a, ep1), state(b, ep1)
                diff_parts["pairs"] += 1
                diff_parts["snapshot"] += sa[0] != sb[0]
                diff_parts["nonce"] += sa[1] != sb[1]
                diff_parts["D"] += sa[2] != sb[2]
    return n_ok, n_bad, diff_parts, violations, least_reach


def show_brute():
    print("\n(d) compute_epoch_state written out (protocol 205-249; inference 77-87 with beta = 2/3) on random pairs of chains "
          "that share exactly the blocks up to sigma_0")
    rng = random.Random(20261119)
    for P, G in ((7, 5), (9, 9), (6, 11), (12, 7)):
        n_ok, n_bad, parts, viol, reach = check_states(rng, P, G)
        print(f"  P = {P}, G = {G}: slot states compared in (sigma_0, sigma_0 + G + 1]: {n_ok} equal, {n_bad} different; "
              f"pairs whose first differing epoch is the one after sigma_0's: {parts['pairs']}, in which the snapshot differs "
              f"{parts['snapshot']} times, the nonce {parts['nonce']}, D {parts['D']}; pairs whose first differing epoch is "
              f"sigma_0's own or earlier, or the next one with sigma_0 >= cut-off - 1: {viol}; "
              f"least shared span observed {reach} (G + 1 = {G + 1})")


def show_reach():
    print("\n(e) Step 2 of 7.1: a fork X with D_X = D_Y at sigma_0 and tip at most sigma_0 + 2K - 2 derives a state of its own "
          "only at slots from the next epoch's first slot c_e + G on, so only if u = c_e - sigma_0 lies in [2, 2K - 2 - G]")
    for name, G in (("(i)", S + K - 1), ("(ii)", 54_000), ("specification", 2 * K)):
        umax = 2 * K - 2 - G
        if umax >= 2:
            print(f"  {name}, G = {G}: u in [2, {umax}]: sigma_0 in [c_e - {umax}, c_e - 2], {umax - 1} slots of the snapshot phase; "
                  f"X's own-state stretch [c_e + G, sigma_0 + 2K - 2] has 2K - 1 - G - u slots, at most {2 * K - 3 - G} "
                  f"({(2 * K - 3 - G) / 3600:.2f} h)")
        else:
            print(f"  {name}, G = {G}: no such sigma_0 (2K - 2 - G = {umax} < 2): every block of X is under H's states")


if __name__ == "__main__":
    show_constants()
    show_schedules()
    show_spans()
    show_brute()
    show_reach()
