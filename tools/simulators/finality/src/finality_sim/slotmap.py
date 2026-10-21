"""Finality counted in slots: which epoch nonces a race meets (SLOTS.md, K.4).

An epoch of ``E`` slots fixes the next epoch's nonce at its cut-off, ``c`` slots in, and the next
epoch starts ``E − c`` slots later (the specification: ``E = 10⌊k/f⌋``, ``c = 6⌊k/f⌋``). With
``B_imm`` at most ``K`` slots back, a race against a target lasts at most ``K`` slots past the
target's slot, so its schedule is that of the epochs the slots ``(x, x + K]`` reach, for a target
``x`` slots into its epoch. B6 sorts the targets by the nonces the race meets:

- **one ground nonce**: the race stays within the target's epoch;
- **two ground nonces**: the target lies past the cut-off and its race reaches the next epoch,
  whose nonce was fixed before the target;
- **a nonce the private chain sets**: the target lies before the cut-off and its race reaches the
  next epoch, so the private chain, forked before the target, holds the cut-off and carries a
  nonce the coalition picks itself, and no bound covers it.
"""

from __future__ import annotations


def nonce_coverage(window: int, epoch: int, cutoff: int) -> tuple[float, float, float]:
    """The shares of targets, uniform over an epoch, whose race of at most ``window`` slots meets
    one ground nonce, two, or a nonce a private chain sets. ``window`` may not exceed the epoch."""
    if not 0 <= window <= epoch or not 0 < cutoff < epoch:
        raise ValueError("need 0 <= window <= epoch and 0 < cutoff < epoch")
    lead = epoch - cutoff                       # from the cut-off to the next epoch's first slot
    two = min(window, lead) / epoch             # past the cut-off, within the window of the end
    private = max(window - lead, 0) / epoch     # before the cut-off, within the window of the end
    return 1.0 - two - private, two, private
