"""What the reference window W costs, at k = 2160 and f = 1/30.

Step 8 and Fork Pruning keep forks and their ledger states up to W/f slots below the latest immutable block, which
trails the tip by about k/f slots: W/k of k. An entry can send a node down a branch that a coalition built in the window;
with four entries, up to four such branches (the coalition's wins in W/f slots, Poisson, 99.9th percentile).

A peer that marks a node with a block only that node holds learns something when the node next proposes while the mark
is usable: the chance that a node with share a of the total active stake wins at least once in the slots that follow.
"""
from math import exp

k, f_inv, alpha = 2160, 30, 0.3


def poisson_quantile(lam, q):
    p = exp(-lam); c = p; n = 0
    while c < q:
        n += 1; p *= lam / n; c += p
    return n


print("W | window | extra forks and states kept, share of k | wins of a 0.3 coalition in the window: mean, 99.9 % "
      "| blocks four entries can name: mean, 99.9 %")
for W in (12, 24, 48, 96, 144, 240):
    lam = alpha * W
    n = poisson_quantile(lam, 0.999)
    print(f"{W:4d} | {W * f_inv:5d} slots = {W * f_inv / 60:4.0f} min | {100 * W / k:5.1f} % | {lam:5.1f}, {n:4d} | {4 * lam:5.0f}, {4 * n:4d}")

f = 1 / f_inv
print("\nchance that a node with share a wins at least once within n slots")
for a in (0.01, 0.05):
    phi = 1 - (1 - f) ** a
    print(f"  a = {a}: " + ", ".join(f"n = {n}: {1 - (1 - phi) ** n:.3f}" for n in (360, 7200)))
