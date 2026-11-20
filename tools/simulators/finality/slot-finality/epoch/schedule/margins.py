"""Margins of the phases of 2K + 2K + 2K and 3K + K + 2K, and the wins a coalition gives up to deflate D (CONSTRUCTIONS.md 2.2, 6).

Part 1 gives G* by `least_gap` of ../common.py (REVIEW.md 5.4) and the proved w_B of ../out_08_buffer.txt, in the states of the K row
with the largest values and in two states outside the row, and each phase over what it needs.
Part 2 gives the wins a coalition of 30 % of the total active stake gives up in each window it withholds, until the mean D over the
honest stake is at most 1.01, from the mean D of out_betas.txt, part 3, under the exact rule.
Usage: python margins.py > out_margins.txt   (with the finality study's interpreter)
"""
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.dont_write_bytecode = True
from common import least_gap             # noqa: E402

K, PHI = 36000, 689
F = 1 / 30
STATES = (   # (label, building share of D, delay in slots, name of the state in ../out_08_buffer.txt)
    ("the K row's largest G*: 30 %, every honest block 15 s late", 0.7, 15, "30 %, every honest block 15 s late"),
    ("the K row's largest w_B: 30 %, a tenth of the honest stake offline, 10 s", 0.63 / 0.93, 10,
     "30 %, a tenth of the honest stake offline, 10 s"),
    ("outside the row: 30 %, 15 s and a tenth of the honest stake offline", 0.63 / 0.93, 15,
     "30 %, 15 s and a tenth of the honest stake offline"),
    ("outside the row: a coalition of a third, 15 s", 2 / 3, 15, "a third, 15 s"),
)
TEXTS = (("2K + 2K + 2K", 2 * K, 2 * K), ("3K + K + 2K", 3 * K, K))   # (text, phase 1, phase 2); phase 3 is 2K in both
DEFLATION = (("3K + 3K", 108000), ("2K + 2K + 2K", 144000))           # constructions of out_betas.txt, part 3, and their windows


def proved_w_b():
    out = {}
    for line in open(os.path.join(HERE, "..", "out_08_buffer.txt")):
        m = re.match(r"\s+(.+?): proved w_B = (\d+) slots", line)
        if m:
            out[m.group(1)] = int(m.group(2))
    return out


def margins(g, w):
    cells = [f"{name}: phase 1 {l1 / g:.2f}, phase 2 {l2 / w:.2f}" for name, l1, l2 in TEXTS]
    return " | ".join(cells) + f" | phase 3 {2 * K / g:.2f}"


def part_1():
    print("1. each phase over what it needs: phase 1 and phase 3 over G*, phase 2 over w_B")
    w_b = proved_w_b()
    rows = []
    for label, x, d, name in STATES:
        g, w = least_gap(K, PHI, x, d), w_b[name]
        rows.append((g, w))
        print(f"   {label}: share {x:.4f}, G* = {g}, w_B = {w}")
    print(f"   the K row's largest values, G* = {rows[0][0]}, w_B = {rows[1][1]}: {margins(rows[0][0], rows[1][1])}")
    for (label, _, _, _), (g, w) in zip(STATES[2:], rows[2:]):
        print(f"   {label}: {margins(g, w)}")


def wins(P, share):
    """The expected wins of a stake whose share of D is `share`, in P slots."""
    return -math.expm1(share * math.log1p(-F)) * P


def part_2():
    print()
    print("2. wins a coalition of 30 % gives up in each window it withholds, until the mean D over the honest stake is at most 1.01 (exact rule)")
    text = open(os.path.join(HERE, "out_betas.txt")).read().split("3. deflation")[1].split("4. a stake")[0]
    for label, P in DEFLATION:
        block = text.split(f"   {label}: window")[1].split("\n   ")[0:7]
        for line in block[1:]:
            m = re.match(r"\s*beta\s+(\S+) \|.*\| exact \(x\* 1\.0000\): (.*)$", line)
            if not m:
                continue
            path = [float(v) for v in m.group(2).split()]
            ratio, given = 1 / 0.7, []        # D over the honest stake: before the first window, D is the total active stake
            for nxt in path:
                given.append(wins(P, 0.3 / (0.7 * ratio)))
                ratio = nxt
                if ratio <= 1.01:
                    break
            cells = ", ".join(f"{v:.0f}" for v in given)
            print(f"   {label}, beta {m.group(1):>3s}: {len(given)} window(s): {cells}; sum {sum(given):.0f}")


if __name__ == "__main__":
    part_1()
    part_2()
