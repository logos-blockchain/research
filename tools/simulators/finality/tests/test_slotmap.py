"""Gates for the epoch nonces a race of at most K slots meets (src/finality_sim/slotmap.py)."""

import pytest

from finality_sim.slotmap import nonce_coverage


def test_the_shares_count_every_target_by_its_race():
    """Against an enumeration of every target slot of an epoch: a race that stays in the epoch
    meets one nonce; one that reaches the next epoch meets two from past the cut-off, and a nonce
    its own private chain set from before it."""
    epoch, cutoff = 600, 360
    for window in (0, 1, 60, 239, 240, 241, 300, 360, 599, 600):
        one = two = private = 0
        for x in range(epoch):
            if x + window < epoch:
                one += 1
            elif x >= cutoff:
                two += 1
            else:
                private += 1
        got = nonce_coverage(window, epoch, cutoff)
        assert got == pytest.approx((one / epoch, two / epoch, private / epoch), abs=1e-12), window


def test_a_window_past_the_epoch_is_refused():
    with pytest.raises(ValueError):
        nonce_coverage(601, 600, 360)
