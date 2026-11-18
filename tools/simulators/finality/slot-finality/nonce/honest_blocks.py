"""The honest blocks that a fork published at a cut-off replaces, at mean rates.

The fork replaces the honest chain's blocks in a window of W slots before the cut-off. At mean
rates the honest chain makes one block every Delta + 1/p_h slots: Delta slots of worst-case delay
after each of its blocks, then the wait for the next honest win. p_h = 1 - (1 - f)^(1 - alpha) is
the chance that the honest stake wins a slot, alpha is the coalition's share and f = 1/30. So the
window holds W / (Delta + 1/p_h) honest blocks. W is 600 and 3,600 slots, 10 minutes and one hour.
`clock` in model.py gives Delta + 1/p_h.

Usage: python honest_blocks.py > honest_blocks.out
"""
from model import F, clock

WINDOWS = (600, 3600)

print("share | delay | slots a block | blocks in 600 slots | blocks in 3,600 slots")
for alpha, who in ((0.30, "30 %"), (1 / 3, "a third")):
    for delta in (10, 15):
        gap = clock(alpha, delta, F)
        print(f"{who:7s} | {delta} s | {gap:.2f} | " + " | ".join(f"{w / gap:.2f}" for w in WINDOWS))
