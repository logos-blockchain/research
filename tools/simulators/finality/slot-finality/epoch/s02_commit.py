"""A check of statements 3.4 to 3.6 of REVIEW.md by enumeration. It supports the proofs and does not
replace them.

`commit` and `density_over_slots` are written from the specification:
  cryptarchia-v1-protocol.md, Commit (lines 496-522 on the 10-hour branch);
  cryptarchia-total-stake-inference.md, Functions (line 62).
A chain is a list of blocks with strictly increasing slots (Block Header Validation, step 5). A block
carries uncles; an uncle has a slot after its parent's and before its referencing block's (Uncle
References). The checks, on random chains with random K, phi and starting B_imm:
  1. the age test and the floor test are monotone along the chain (3.4);
  2. the loop returns the later of B_imm and the latest block that meets both tests (3.5);
  3. a block after the starting B_imm is immutable after the call exactly when it meets both tests (3.6).
Usage: python s02_commit.py > out_02_commit.txt
"""
import random


def density_over_slots(chain, tip, s, p):
    """Distinct occupied slots of the chain ending in block index `tip`, among the p slots from s:
    a slot counts if it holds a block of the chain, or an uncle referenced by a block of the chain
    that lies in [s, s + p) itself."""
    occupied = set()
    for j in range(tip + 1):
        sl, uncles = chain[j]
        if s <= sl < s + p:
            occupied.add(sl)
            for u in uncles:
                if s <= u < s + p:
                    occupied.add(u)
    return len(occupied)


def commit(chain, tip, b_imm, K, phi):
    """The loop of Commit. Returns the index of the new B_imm."""
    b = b_imm
    while b != tip:
        c = b + 1                                     # child_on_chain(B, c_loc)
        sl_c, sl_tip = chain[c][0], chain[tip][0]
        if sl_c + K > sl_tip or density_over_slots(chain, tip, sl_c + 1, sl_tip - sl_c) < phi:
            break
        b = c
    return b


def random_chain(rng, n):
    chain, sl = [], rng.randrange(0, 5)
    for j in range(n):
        uncles = []
        if j > 0:
            for _ in range(rng.choice((0, 0, 0, 1, 2, 4))):
                parent = rng.randrange(max(0, j - 4), j)          # the uncle's parent, on the chain
                lo, hi = chain[parent][0] + 1, sl - 1            # sl_parent < sl_U < sl_A
                if lo <= hi:
                    uncles.append(rng.randrange(lo, hi + 1))
        chain.append((sl, uncles))
        sl += rng.choice((1, 1, 2, 3, 5, 8, 13, 30))
    return chain


if __name__ == "__main__":
    rng = random.Random(20261117)
    runs, moved, with_uncle_count = 300_000, 0, 0
    for _ in range(runs):
        n = rng.randrange(2, 28)
        chain = random_chain(rng, n)
        tip = n - 1
        K = rng.randrange(0, 60)
        phi = rng.randrange(0, 8)
        b_imm = rng.randrange(0, n)
        sl_tip = chain[tip][0]
        age = [chain[j][0] + K <= sl_tip for j in range(n)]
        count = [density_over_slots(chain, tip, chain[j][0] + 1, sl_tip - chain[j][0]) for j in range(n)]
        blocks_after = [n - 1 - j for j in range(n)]
        floor = [c >= phi for c in count]
        # 1. monotone: a test met at a later block is met at every earlier one; counts do not grow
        for j in range(1, n):
            assert count[j] <= count[j - 1]
            assert count[j] >= blocks_after[j]                    # occupied slots >= blocks
            if age[j]:
                assert age[j - 1]
            if floor[j]:
                assert floor[j - 1]
        if any(c > b for c, b in zip(count, blocks_after)):
            with_uncle_count += 1
        # 2. the loop's result
        got = commit(chain, tip, b_imm, K, phi)
        both = [m for m in range(b_imm + 1, n) if age[m] and floor[m]]
        assert got == max([b_imm] + both)
        # 3. immutable after the call <=> both tests, for every block after the starting B_imm
        for x in range(b_imm + 1, n):
            assert (x <= got) == (age[x] and floor[x])
        moved += got != b_imm
    print(f"{runs} random chains: every assertion held")
    print(f"  B_imm moved in {moved} of them; an uncle raised a count above the blocks in {with_uncle_count}")

    # A starting B_imm need not meet the tests against a new tip: the Online rule can move c_loc to
    # a longer fork whose tip has an earlier slot.
    K, phi = 10, 1
    old = [(0, []), (5, []), (16, [])]            # B_imm moved to slot 5 when the tip was at slot 16
    assert commit(old, 2, 0, K, phi) == 1
    new = [(0, []), (5, []), (9, []), (12, [])]   # a longer fork through that B_imm, tip at slot 12
    print("example: B_imm at slot 5 was fixed by a tip at slot 16; a longer fork through it ends at slot 12;")
    print(f"  age test of B_imm against the new tip: {new[1][0] + K <= new[3][0]}; commit keeps B_imm at index {commit(new, 3, 1, K, phi)}")
