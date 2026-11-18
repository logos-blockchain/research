"""A simulation of the model of REVIEW.md, section 5, against the bounds of statements 5.4 and
5.5. Sizes are scaled down so that the chances can be measured by sampling.

Model M(p, d): every slot is won with chance p, independently. After a block of the chain in slot s,
the next block of the chain is in the first won slot after s + d. Only blocks of the chain count as
occupied slots (no uncles), so the lower bound for that case applies.

Per sample: the chain starts L0 slots before the cut-off c = 0. Y is the first block with slot >= 0,
T the last block with slot <= G - 1, Z the last block with slot < 0. The value is final when first
used if Y passes both tests of commit against the tip T, or if Z sits in slot -1 and passes both
(statement 4.4). For the first samples of each row the literal commit loop of s02_commit.py is run
and compared.
Usage: python s04_gap_sim.py > out_04_gap_sim.txt
"""
import math

import numpy as np
from scipy.stats import binom

from common import lower_chain, p_of, short, upper
from s02_commit import commit

L0 = 4_000          # the chain starts this many slots before the cut-off
BATCH = 50_000
TAIL = 1e-5         # a sampled count is rejected when its chance under a bound is below this


def sample(rng, n, G, p, d, start_at_minus_one=False):
    """Block slots, one row per sample, enough of them to pass slot G."""
    span = (1 if start_at_minus_one else L0) + G
    blocks = int(2.0 * span / (d + 1 / p) + 12 * math.sqrt(span * p) + 40)
    gaps = d + rng.geometric(p, size=(n, blocks))
    first = -1 if start_at_minus_one else -L0
    slots = first + np.concatenate((np.zeros((n, 1), dtype=np.int64), np.cumsum(gaps, axis=1)), axis=1)
    assert (slots[:, -1] > G).all(), "not enough blocks drawn"
    return slots


def verdicts(slots, G, K, phi):
    n = slots.shape[0]
    rows = np.arange(n)
    y = (slots < 0).sum(axis=1)                  # index of Y: the first block with slot >= 0
    t = (slots <= G - 1).sum(axis=1) - 1         # index of T: the last block with slot <= G - 1
    z = y - 1                                    # index of Z
    sl_y, sl_t, sl_z = slots[rows, y], slots[rows, t], slots[rows, z]
    final_a = (t >= y) & (sl_y + K <= sl_t) & (t - y >= phi)
    final_b = (sl_z == -1) & (sl_z + K <= sl_t) & (t - z >= phi)
    return final_a | final_b, y, t, z


def check_literal(slots, G, K, phi, final, y, t, z, how_many=300):
    """The literal loop of Commit, started from the first block, against the vectorised verdict."""
    for i in range(min(how_many, slots.shape[0])):
        chain = [(int(s), []) for s in slots[i, : t[i] + 1]]
        got = commit(chain, int(t[i]), 0, K, phi)
        literal = got >= y[i] or (got == z[i] and chain[z[i]][0] == -1)
        assert literal == bool(final[i])


def row(rng, name, K, phi, d, p, G, n_total):
    fails, floor_fails, checked = 0, 0, 0
    for b in range(n_total // BATCH):
        slots = sample(rng, BATCH, G, p, d)
        final, y, t, z = verdicts(slots, G, K, phi)
        if b == 0:
            check_literal(slots, G, K, phi, final, y, t, z)
            checked = 300
        fails += int((~final).sum())
        # the worst start for the count: a block of the chain in slot -1
        worst = sample(rng, BATCH, G, p, d, start_at_minus_one=True)
        in_gap = ((worst >= 0) & (worst <= G - 1)).sum(axis=1)
        floor_fails += int((in_gap < phi + 1).sum())
    freq = fails / n_total
    lo, up = lower_chain(G, K, phi, p, d), upper(G, K, phi, p, d)
    exact = short(phi + 1, G, p, d)
    ffreq = floor_fails / n_total
    # A count is rejected when its chance under the bound is below TAIL.
    ok = (binom.cdf(fails, n_total, lo) >= TAIL                       # not too few for the lower bound
          and binom.sf(fails - 1, n_total, up) >= TAIL                # not too many for the upper bound
          and binom.cdf(floor_fails, n_total, exact) >= TAIL          # the count's formula, both sides
          and binom.sf(floor_fails - 1, n_total, exact) >= TAIL)
    print(f"{name} G = K + {G - K:5d} | lower {lo:.4e} | sampled {freq:.4e} ({fails}) | upper {up:.4e} | "
          f"fewer than phi + 1 blocks after a block in slot c - 1: sampled {ffreq:.4e} ({floor_fails}), formula {exact:.4e} | "
          f"{'ok' if ok else 'OUTSIDE'} (literal commit on {checked} samples)")
    return ok


if __name__ == "__main__":
    rng = np.random.default_rng(533)
    n_total = 400_000
    all_ok = True
    print(f"{n_total} samples a row; in brackets the number of samples counted; 'ok' means that no count has a chance below {TAIL:g} "
          "under the bound it is compared with")
    for name, K, phi, d, p, extras in (
        ("K = 3000, phi = 55, d = 15, x = 1.0 |", 3000, 55, 15, p_of(1.0), (0, 30, 100, 200, 300, 450, 600, 1000)),
        ("K = 3000, phi = 55, d = 15, x = 0.7 |", 3000, 55, 15, p_of(0.7), (600, 1000, 1500, 2500)),
        ("K = 2000, phi = 30, d =  0, x = 1.0 |", 2000, 30, 0, p_of(1.0), (0, 100, 250, 400)),
        ("K = 2000, phi = 45, d = 10, x = 1.0 |", 2000, 45, 10, p_of(1.0), (200, 400, 600, 1000)),
    ):
        for extra in extras:
            all_ok &= row(rng, name, K, phi, d, p, K + extra, n_total)
    print("every row inside its bounds" if all_ok else "A ROW IS OUTSIDE ITS BOUNDS")
