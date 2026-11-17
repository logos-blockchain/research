"""Model of the Slot-Finality rules.

The two fork choice rules and `commit` are NOT re-implemented: they are the printed python
fences of fork-choice.md and of the RFC (`commit`), exec'd verbatim. Everything else
(`on_block`, `prune_forks`, step 5/7/8, density helpers) follows the LaTeX in
cryptarchia-v1-protocol.md line by line.

The checkout of the specification is read from SPEC_ROOT. The RFC document is found by its
title. `block_id` is supplied to the printed code. `Rules(..., unordered=True)` gives the
Bootstrap rule without its fixed order of visits.
"""
import glob
import hashlib
import os
import re
import subprocess

WT = os.environ.get("SPEC_ROOT")
if not WT:
    raise SystemExit("Set SPEC_ROOT to a checkout of the logos-lips repository. The model runs the rules it prints.")
RAW = WT + "/docs/blockchain/raw/"


def fences(text):
    return re.findall(r"^```python\n(.*?)^```", text, re.S | re.M)


class MissingHistory(Exception):
    pass


class NotOnChain(Exception):
    pass


class _Missing:
    def __getattr__(self, name):
        raise MissingHistory(name)


MISSING = _Missing()  # the parent of a checkpoint block: reading it means reading below the checkpoint


class Block:
    __slots__ = ("id", "parent", "slot", "height", "uncles", "tag")
    counter = 0

    def __init__(self, parent, slot, uncles=(), tag="", height=None):
        Block.counter += 1
        self.id = Block.counter
        self.parent = parent
        self.slot = slot
        self.uncles = list(uncles)
        self.tag = tag
        self.height = height if height is not None else (parent.height + 1 if parent is not None else 0)

    def __repr__(self):
        return f"<{self.tag or self.id} sl={self.slot} h={self.height}>"


def chain_up(parent, slots, tag=""):
    """Blocks at `slots` on top of `parent`. Returns the list."""
    out = []
    for i, s in enumerate(slots):
        parent = Block(parent, s, tag=f"{tag}{i}" if tag else "")
        out.append(parent)
    return out


# helpers the printed fences read -------------------------------------------------------------


def common_prefix_depth(a, b):
    x, y, da, db = a, b, 0, 0
    while x is not y:
        if x.height > y.height:
            x, da = x.parent, da + 1
        elif y.height > x.height:
            y, db = y.parent, db + 1
        else:
            x, y, da, db = x.parent, y.parent, da + 1, db + 1
    return da, db


def grandparent(b, d):
    for _ in range(d):
        b = b.parent
    return b


def density(b, d, s_gen):
    D = grandparent(b, d)
    n, x = 0, b
    while x is not D:
        if D.slot < x.slot <= D.slot + s_gen:
            n += 1
        x = x.parent
    return n


def is_ancestor(a, b):
    """Reflexive: a is on the chain ending in b."""
    while b.height > a.height:
        b = b.parent
    return b is a


def common_ancestor(a, b):
    da, _ = common_prefix_depth(a, b)
    return grandparent(a, da)


def child_on_chain(b, c):
    x = c
    while x.height > b.height + 1:
        x = x.parent
    if x.height != b.height + 1 or x.parent is not b:
        raise NotOnChain(f"{b} is not on the chain of {c}")
    return x


def sl(b):
    return b.slot


def block_id(b):
    """Stands in for the hash of a header: an order unrelated to the order of creation."""
    return hashlib.blake2b(str(b.id).encode(), digest_size=32).digest()


def density_over_slots(c, s, p):
    """[s, s+p): chain blocks in range and uncles they carry that are in range, each slot once.
    The walk reads no block below the range, so it can never read below a checkpoint."""
    occ, x = set(), c
    while x is not None and x.slot >= s:
        if x.slot < s + p:
            occ.add(x.slot)
            for u in x.uncles:
                if s <= u.slot < s + p:
                    occ.add(u.slot)
        x = x.parent
    return len(occ)


def tips(T):
    has_child = {b.parent for b in T if b.parent is not None and b.parent is not MISSING}
    return [b for b in T if b not in has_child]


def prune_blocks(new, old, T):
    x, Tp = new, set(T)
    while x is not old:
        Tp.discard(x)
        x = x.parent
    return Tp


def prune_forks(T, B):
    Tp = set(T)
    for t in tips(T):
        div = common_ancestor(t, B)
        if div is not B:
            Tp = prune_blocks(t, div, Tp)
    return Tp


# load the printed fences ----------------------------------------------------------------------

fc_text = open(RAW + "fork-choice.md", encoding="utf-8").read()
(rfc_path,) = glob.glob(RAW + "rfc/RFC-*-cryptarchia-count-finality-in-slots.md")
rfc_text = open(rfc_path, encoding="utf-8").read()
ORDERED = "sorted(forks, key=block_id)"
assert fc_text.count(ORDERED) == 2, "both printed rules are expected to visit the forks by block ID"


class Rules:
    """One parameter set. K, phi, s_gen live in the namespace of the printed code."""

    BOOTSTRAP, ONLINE = "BOOTSTRAP", "ONLINE"

    def __init__(self, K, phi, s_gen, W_slots=None, unordered=False):
        self.K, self.phi, self.s_gen = K, phi, s_gen
        self.W_slots = W_slots if W_slots is not None else max(1, K // 4)
        self.ns = dict(
            common_prefix_depth=common_prefix_depth,
            grandparent=grandparent,
            density=density,
            is_ancestor=is_ancestor,
            child_on_chain=child_on_chain,
            sl=sl,
            block_id=block_id,
            density_over_slots=density_over_slots,
            prune_forks=prune_forks,
            K=K,
            phi=phi,
            ONLINE=self.ONLINE,
            fork_choice_rule=self.ONLINE,
        )
        for body in fences(fc_text):
            if unordered:
                # The rules as printed, visiting the forks in the order the caller lists them.
                body = body.replace(ORDERED, "forks")
            exec(body, self.ns)
        for body in fences(rfc_text):
            if "def commit" in body:
                exec(body, self.ns)
        self.bootstrap_fork_choice = self.ns["bootstrap_fork_choice"]
        self.online_fork_choice = self.ns["online_fork_choice"]
        self.commit = self.ns["commit"]


class Node:
    def __init__(self, rules, root, rule="BOOTSTRAP", step8="height", clock=None, prune="complete"):
        self.r = rules
        self.T = {root}
        self.B_imm = root
        self.c_loc = root
        self.rule = rule
        self.step8 = step8
        self.prune = prune
        self.clock = clock  # None: no step 6 check
        self.rejected = []
        self.trace = []

    # ---- Block Header Validation, the steps the rules touch
    def valid_header(self, b):
        p = b.parent
        if p not in self.T:  # step 7
            return "step7"
        if not b.slot > p.slot:  # step 5
            return "step5"
        if self.clock is not None and b.slot > self.clock:  # step 6
            return "step6"
        if self.step8 == "height":
            if not b.height > self.B_imm.height:
                return "step8"
        else:
            if not is_ancestor(self.B_imm, b):
                return "step8"
        for u in b.uncles:  # step 10, the rules that read slots and the chain
            if not (u.parent.height < b.height and is_ancestor(u.parent, b)):
                return "uncle-parent"
            if is_ancestor(u, b):
                return "uncle-on-chain"
            if not (u.parent.slot < u.slot < b.slot):
                return "uncle-order"
            if b.slot - u.parent.slot > self.r.W_slots:
                return "uncle-window"
        return None

    # ---- on_block
    def on_block(self, b):
        if b in self.T:
            return "known"
        err = self.valid_header(b)
        if err:
            self.rejected.append((b, err))
            return err
        Tp = self.T | {b}
        # on_block as written at 45a40aea: the `c` split, then the three-case `c_loc'` split
        c = b if b.parent is self.c_loc else self.c_loc
        if self.rule == "BOOTSTRAP":
            c2 = self.r.bootstrap_fork_choice(c, tips(Tp), self.r.K, self.r.s_gen, self.B_imm)
        elif b.parent is self.c_loc:
            c2 = c
        else:
            c2 = self.r.online_fork_choice(self.c_loc, tips(Tp), self.B_imm)
        if self.rule == "ONLINE":
            self.r.ns["fork_choice_rule"] = "ONLINE"
            Tp, self.B_imm = self._commit(Tp, c2)
        self.T, self.c_loc = Tp, c2
        return "ok"

    def _commit(self, T, c):
        if self.prune == "complete":
            return self.r.commit(T, c, self.B_imm)
        # an implementation allowed by step 8's second sentence: B_imm moves, forks stay
        _, B = self.r.commit(T, c, self.B_imm)
        return T, B

    def switch_to_online(self, run_commit=True):
        self.rule = "ONLINE"
        if run_commit:
            self.T, self.B_imm = self._commit(self.T, self.c_loc)


def master_rules(k, s_gen):
    """The rules of the base commit, with only their syntax errors repaired, for comparison."""
    txt = subprocess.run(
        ["git", "-C", WT, "show", "f28cf3e5:docs/blockchain/raw/fork-choice.md"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    ns = dict(common_prefix_depth=common_prefix_depth, density=density)
    for body in fences(txt):
        body = body.replace("common_prefix_depth(c_max, c_fork):", "common_prefix_depth(c_max, c_fork)")
        body = body.replace("if depth_max < depth_fork\n", "if depth_max < depth_fork:\n")
        body = body.rstrip() + "\n    return c_max\n"
        exec(body, ns)
    return ns
