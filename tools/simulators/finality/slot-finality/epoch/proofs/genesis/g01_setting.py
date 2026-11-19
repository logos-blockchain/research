"""GENESIS.md, section 1: the constants, checked against the specification's text, and the values
derived from them.

Reads the specification with `git show <ref>:<path>` (read-only) from a clone of logos-co/logos-lips
that holds commits 7f3cf149 and ded1d4c6, named by the environment variable LIPS_REPO.
Usage: LIPS_REPO=<clone> python g01_setting.py > out_01_setting.txt
"""
import math
import os
import subprocess

from common_g import (ALPHAS, DELTAS, EPOCH, F, GAP, H, K_CASES, K_SEC, S_GEN, T_OFFLINE, U_SLOTS,
                      W_UNCLE, p_of, pct, theta_star)

REPO = os.environ.get("LIPS_REPO") or exit("set LIPS_REPO to a clone of logos-co/logos-lips that holds 7f3cf149 and ded1d4c6")
RAW = "docs/blockchain/raw/"


def line(ref: str, path: str, n: int) -> str:
    out = subprocess.run(["git", "-C", REPO, "show", f"{ref}:{RAW}{path}"], capture_output=True,
                         text=True, check=True).stdout.splitlines()
    return out[n - 1]


def check(ref, path, n, needle):
    ok = needle in line(ref, path, n)
    print(f"  {ref} {path}:{n} contains {needle!r}: {ok}")
    assert ok


if __name__ == "__main__":
    print("the text (git show, read-only)")
    check("7f3cf149", "cryptarchia-v1-protocol.md", 102, "1/30")
    check("7f3cf149", "cryptarchia-v1-protocol.md", 103, "2160 blocks")
    check("7f3cf149", "cryptarchia-v1-protocol.md", 104, "36,000 slots (10 hours)")
    check("7f3cf149", "cryptarchia-v1-protocol.md", 104, "at most one of three disturbances")
    check("ded1d4c6", "cryptarchia-v1-protocol.md", 103, "64,800 slots (18 hours)")
    check("ded1d4c6", "cryptarchia-v1-protocol.md", 103, "at most two of three disturbances")
    check("7f3cf149", "cryptarchia-v1-protocol.md", 109, "360 at")
    check("7f3cf149", "cryptarchia-v1-protocol.md", 155, "4\\lfloor \\frac{k}{f}\\rfloor")
    check("7f3cf149", "fork-choice.md", 80, "s_{gen} = \\lfloor\\frac{k}{4f}\\rfloor")
    check("7f3cf149", "fork-choice.md", 100, "uncle references")
    check("7f3cf149", "fork-choice.md", 137, "density(c_max, depth_max, s_gen) < density(c_fork")
    check("7f3cf149", "cryptarchia-v1-bootstr-sync.md", 110, "20 minutes")
    check("7f3cf149", "cryptarchia-proof-of-leadership.md", 68, "no leader note evolution")
    check("7f3cf149", "cryptarchia-proof-of-leadership.md", 180, "ticket := \\text{hash}")
    diff = subprocess.run(["git", "-C", REPO, "diff", "--stat", "ded1d4c6", "7f3cf149", "--",
                           RAW + "fork-choice.md", RAW + "cryptarchia-v1-bootstr-sync.md",
                           RAW + "cryptarchia-proof-of-leadership.md"],
                          capture_output=True, text=True, check=True).stdout.strip()
    print(f"  fork-choice, bootstrap and leadership identical at both refs: {diff == ''}")

    print("\nconstants (slots of 1 second)")
    print(f"  f = 1/30, k = {K_SEC}, floor(k/f) = {U_SLOTS}, epoch E = {EPOCH} slots = {EPOCH / H:g} h")
    print(f"  gap G from the cut-off to the next epoch = {GAP} slots = {GAP / H:g} h; G + 1 = {GAP + 1}")
    print(f"  s = s_gen = floor(k/(4f)) = {S_GEN} slots = {S_GEN / H:g} h")
    print(f"  T_offline = {T_OFFLINE} slots, W f^-1 = {W_UNCLE} slots")
    for name, K in K_CASES.items():
        print(f"  {name}: K = {K}; K - s = {K - S_GEN}; K >= s + 1: {K >= S_GEN + 1}; "
              f"2K = {2 * K} <= G + 1: {2 * K <= GAP + 1}; 2 s <= K: {2 * S_GEN <= K}")

    print("\nper-slot chances and rates (section 3, statement 5.2)")
    print(" share | Delta | p_h = 1-(1-f)^(1-a) | p_a = 1-(1-f)^a | honest Delta-separated rate 1/(Delta+1/p_h) | p_a / rate | theta* | e^-theta*")
    for a in ALPHAS:
        for d in DELTAS:
            ph, pa = p_of(1 - a), p_of(a)
            rate = 1 / (d + 1 / ph)
            th = theta_star(pa, ph, d)
            print(f" {pct(a):>7} | {d:5d} | {ph:.6f} | {pa:.6f} | {rate:.6f} | {pa / rate:.4f} | "
                  f"{th:.4f} | {math.exp(-th):.4f}")
    print("\nthe floor at the coalition's mean rate (remark 7.4): slots for phi wins at p_a(30 %)")
    for name, phi in (("10 h (#533), phi = 689", 689), ("18 h (base), phi = 1291", 1291)):
        print(f"  {name}: phi / p_a = {phi / p_of(0.3):.0f} slots = {phi / p_of(0.3) / H:.1f} h")
    print("\nan honest chain with no honest win in K - 2 Delta - 1 slots (statements 7.1 and 7.2): log10 of (1 - p_h)^(K - 2 Delta - 1)")
    for name, K in K_CASES.items():
        worst = min(p_of(1 - a) for a in ALPHAS)
        print(f"  {name}: at most 10^{(K - 2 * max(DELTAS) - 1) * math.log10(1 - worst):.0f}")
    print("\nthe drift condition p_a (1/p_h + Delta) < 1 of statement 6.2 (c) holds up to")
    for a in ALPHAS:
        ph, pa = p_of(1 - a), p_of(a)
        print(f"  {pct(a)}: Delta < 1/p_a - 1/p_h = {1 / pa - 1 / ph:.1f} slots")
