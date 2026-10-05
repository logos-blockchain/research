"""Differential test: the Lean model of Cryptarchia against the specification's pseudocode.

This file transliterates, independently of the Lean code, the pseudocode of
  - fork-choice.md: common_prefix_depth, density, bootstrap_fork_choice, online_fork_choice;
  - cryptarchia-v1-protocol.md: prune_forks / prune_blocks, uncle_candidates +
    select_uncles_oldest, the N_BLOCKS count of compute_epoch_state;
  - cryptarchia-total-stake-inference.md: total_stake_inference (Rust integer semantics:
    signed division truncates toward zero);
  - cryptarchia-proof-of-leadership.md: lottery_constants and the threshold v(t0 + t1 v) in F_p;
generates random block trees, and writes one `#guard` per case to
CryptarchiaTest/Diff.lean. Checking that file with Lean runs the comparison:

    python3 tools/difftest/cryptarchia_diff.py && lake env lean CryptarchiaTest/Diff.lean
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

P = 0x30644E72E131A029B85045B68181585D2833E84879B9709143E1F593F0000001
T0C = 0x1a3fb997fd5838f2a1585ee090a95c88129ab25cc4d2e2d28f1a95f81d85465
T1C = 0x71e790b4199113a9a00298d823c5716ddac764a110a45fe3b770bbb3e8a57


# ---------------------------------------------------------------- block trees
class Tree:
    def __init__(self):
        self.parent = {0: 0}
        self.slot = {0: 0}
        self.uncles = {0: []}  # list of (id, parent, slot)

    def ancestors(self, b):
        """ancestors(b), tip first, including b, down to genesis."""
        out = [b]
        while b != 0:
            b = self.parent[b]
            out.append(b)
        return out

    def height(self, b):
        return len(self.ancestors(b)) - 1


def common_ancestor(t: Tree, a, b):
    anc_b = set(t.ancestors(b))
    for x in t.ancestors(a):
        if x in anc_b:
            return x
    return 0


def common_prefix_depth(t: Tree, a, b):
    l = common_ancestor(t, a, b)
    return t.height(a) - t.height(l), t.height(b) - t.height(l)


def density(t: Tree, b, d, s_gen):
    anc = t.ancestors(b)
    base = anc[d] if d < len(anc) else 0
    s0 = t.slot[base]
    return sum(1 for x in anc if s0 < t.slot[x] <= s0 + s_gen)


def online_fork_choice(t: Tree, c_local, forks, k):
    c_max = c_local
    for c_fork in forks:
        depth_max, depth_fork = common_prefix_depth(t, c_max, c_fork)
        if depth_max <= k:
            if depth_max < depth_fork:
                c_max = c_fork
        else:
            continue
    return c_max


def bootstrap_fork_choice(t: Tree, c_local, forks, k, s_gen):
    c_max = c_local
    for c_fork in forks:
        depth_max, depth_fork = common_prefix_depth(t, c_max, c_fork)
        if depth_max <= k:
            if depth_max < depth_fork:
                c_max = c_fork
        else:
            if density(t, c_max, depth_max, s_gen) < density(t, c_fork, depth_fork, s_gen):
                c_max = c_fork
    return c_max


def tips(t: Tree, T):
    Ts = set(T)
    return [b for b in T if not any(c != b and t.parent[c] == b for c in Ts)]


def prune_forks(t: Tree, T, B):
    Tp = list(T)
    for B_tip in tips(t, T):
        B_div = common_ancestor(t, B_tip, B)
        if B_div != B:
            x = B_tip
            while x != B_div:
                if x in Tp:
                    Tp.remove(x)
                x = t.parent[x]
    return Tp


def select_uncles_oldest(t: Tree, T, cloc, sl_B, W_slots, max_uncles):
    anc = t.ancestors(cloc)  # ancestors(B) = cloc's chain, B extends cloc
    referenced = [u for A in anc for u in t.uncles[A]]
    occupied = {t.slot[A] for A in anc} | {u[2] for u in referenced}
    cands = []
    for U in T:
        pU = t.parent[U]
        if (pU in anc and U not in anc and sl_B > t.slot[U]
                and sl_B - t.slot[pU] <= W_slots and t.slot[U] not in occupied):
            cands.append(U)
    ordered = sorted(cands, key=lambda U: (t.slot[t.parent[U]], t.slot[U], U))
    selected, slots = [], set()
    for U in ordered:
        if len(selected) == max_uncles:
            break
        if t.slot[U] in slots:
            continue
        slots.add(t.slot[U])
        selected.append(U)
    return selected


def n_blocks(t: Tree, tip, e, epoch_len, period):
    lo, hi = e * epoch_len, e * epoch_len + period
    inw = lambda s: lo <= s < hi
    chain = t.ancestors(tip)
    ref = [u for A in chain if inw(t.slot[A]) for u in t.uncles[A]]
    return len({t.slot[B] for B in chain if inw(t.slot[B])} | {u[2] for u in ref if inw(u[2])})


def tdiv(a, b):
    q = abs(a) // abs(b)
    return q if (a >= 0) == (b > 0) else -q


def infer(D, N, period, f_p, beta_p=1000, prec=1000):
    tse_p = D * prec
    measured = N * prec
    expected = period * f_p
    diff = expected - measured
    err = tdiv(tse_p * diff, expected)
    corr = tdiv(beta_p * err, prec)
    new = tdiv(tse_p - corr, prec)
    return max(new, 1)


def threshold(D, v):
    t0 = T0C // D
    t1 = P - (T1C // (D * D))
    return (v * (t0 + t1 * v)) % P


# ---------------------------------------------------------------- generation
def random_tree(rng, n, max_gap=4, uncle_p=0.3):
    t = Tree()
    for i in range(1, n + 1):
        p = rng.choice(list(t.parent.keys()))
        t.parent[i] = p
        t.slot[i] = t.slot[p] + rng.randint(1, max_gap)
        t.uncles[i] = []
    for i in range(1, n + 1):
        if rng.random() < uncle_p:
            for u in rng.sample(range(1, n + 1), k=min(n, rng.randint(1, 3))):
                t.uncles[i].append((u, t.parent[u], t.slot[u]))
    return t


def lean_store(t: Tree):
    items = []
    for b in sorted(t.parent):
        us = ", ".join(f"({u}, {p}, {s})" for u, p, s in t.uncles[b])
        items.append(f"({b}, {t.parent[b]}, {t.slot[b]}, [{us}])")
    return "mkStore [" + ", ".join(items) + "]"


def main(cases=400, seed=1):
    rng = random.Random(seed)
    out = ["import CryptarchiaTest.Harness", "", "open Cryptarchia Cryptarchia.Test", "",
           "/-! Generated by `tools/difftest/cryptarchia_diff.py`: every `#guard` compares the Lean model",
           "with an independent transliteration of the specification's pseudocode. -/", ""]
    n_guard = 0
    for case in range(cases):
        n = rng.randint(3, 25)
        t = random_tree(rng, n)
        st = f"st{case}"
        out.append(f"def {st} : Store := {lean_store(t)}")
        T = sorted(t.parent)
        k = rng.randint(1, 4)
        s_gen = rng.randint(1, 8)
        fDen = rng.choice([2, 3, 5])
        cfg = f"(cfg {k} 1 {fDen})"
        sgen_lean = k * fDen // 4
        cloc = rng.choice(T)
        tp = tips(t, T)
        rng.shuffle(tp)
        tl = "[" + ", ".join(map(str, tp)) + "]"
        # fork choice, both rules, the given order
        out.append(f"#guard forkChoice {st} .online {k} {s_gen} {cloc} {tl} = "
                   f"{online_fork_choice(t, cloc, tp, k)}")
        out.append(f"#guard forkChoice {st} .bootstrap {k} {s_gen} {cloc} {tl} = "
                   f"{bootstrap_fork_choice(t, cloc, tp, k, s_gen)}")
        a, b = rng.choice(T), rng.choice(T)
        out.append(f"#guard commonPrefixDepth {st} {a} {b} = {common_prefix_depth(t, a, b)}")
        d = rng.randint(0, 4)
        out.append(f"#guard density {st} {a} {d} {s_gen} = {density(t, a, d, s_gen)}")
        # pruning at a random block on cloc's chain
        B = rng.choice(t.ancestors(cloc))
        pr = prune_forks(t, T, B)
        out.append(f"#guard (pruneForks {st} {T} {B}).toFinset = ({sorted(pr)} : List ℕ).toFinset")
        # uncle selection for a block at slot sl extending cloc, from the node's tree T
        sl = t.slot[cloc] + rng.randint(1, 6)
        W_slots = 1 * fDen  # W = 1
        mu = 4
        sel = select_uncles_oldest(t, T, cloc, sl, W_slots, mu)
        out.append(f"#guard (selectUncles {cfg} {st} {T} {cloc} {sl}).map (·.id) = {sel}")
        # the TSI count on the chain of a random tip, epoch e, small geometry
        tip = rng.choice(T)
        c_kf = k * fDen
        epoch_len, period = 10 * c_kf, 6 * c_kf
        e = rng.randint(0, max(0, t.slot[tip] // max(1, epoch_len)))
        nb = n_blocks(t, tip, e, epoch_len, period)
        out.append(f"#guard occupied {cfg} (chainUp {st} {tip}) {e} = {nb}")
        n_guard += 7
    # TSI arithmetic and the lottery threshold at the specified constants
    period, f_p = 388800, 33
    for _ in range(300):
        D = rng.choice([rng.randint(1, 10**3), rng.randint(1, 10**12), rng.randint(1, 10**17)])
        N = rng.randint(0, period)
        out.append(f"#guard infer Config.spec {D} {N} = {infer(D, N, period, f_p)}")
        v = rng.choice([rng.randint(0, D), rng.randint(0, 100 * D), rng.randint(0, 10**18)])
        out.append(f"#guard threshold Config.spec {D} {v} = {threshold(D, v)}")
        n_guard += 2
    path = Path(__file__).resolve().parent.parent.parent / "CryptarchiaTest" / "Diff.lean"
    path.write_text("\n".join(out) + "\n")
    print(f"wrote {n_guard} checks ({cases} random block trees) to {path}")


if __name__ == "__main__":
    main(*(int(a) for a in sys.argv[1:]))
