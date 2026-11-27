"""The stop rule of Downloading Uncles as Cryptarchia Bootstrapping & Synchronization drafts it, on random block trees.

For an entry u of a block A, the node skips u if its slot is not before the slot of A or lies W/f or more
slots before it. During the download it stops, before adding a block Y that is not in its tree, if the
common ancestor of Y and A lies more than W/f slots before A, or if Y's slot is u.slot or later and Y is
not the block u names.

The provider streams the path from the highest common ancestor of the target and the known blocks to the
target. Two cases: it holds A's parent (known = A.parent, best tip, B_imm), or it lacks A's chain and
starts from B_imm (where a stop at the first block outside the window would cut off valid uncles).

Checks:
  (a) a valid entry is never cut off: the uncle reaches the tree;
  (b) every block the download adds lies inside the window: its common ancestor with A is at most W/f
      slots before A, and its slot is before u.slot unless it is the named block itself;
  (c) an entry whose fork point lies outside the window adds no block of the uncle's branch.
Usage: stop_rule.py
"""
import random

WF = 40                                    # W/f in slots, small so that both sides of the window occur


class B:
    __slots__ = ("id", "parent", "slot", "h")

    def __init__(s, i, parent, slot):
        s.id, s.parent, s.slot = i, parent, slot
        s.h = 0 if parent is None else parent.h + 1


def ancestors(b):                          # b and all its ancestors
    out = []
    while b is not None:
        out.append(b); b = b.parent
    return out


def lca(a, b):
    sa = {x.id for x in ancestors(a)}
    while b.id not in sa:
        b = b.parent
    return b


def tree(rng, n):
    g = B(0, None, 0); bs = [g]
    for i in range(1, n):
        p = bs[-1 - min(int(rng.expovariate(0.15)), len(bs) - 1)]      # mostly recent parents: many short forks
        bs.append(B(i, p, p.slot + rng.randint(1, 12)))
    return bs


def run(seed):
    rng = random.Random(seed)
    bs = tree(rng, 400)
    # The node's tree: closed under ancestry, missing many fork blocks.
    T = set()
    for b in rng.sample(bs, 120):
        T |= {x.id for x in ancestors(b)}
    inT = [b for b in bs if b.id in T]
    A = rng.choice([b for b in inT if b.h > 5])
    imm = ancestors(A)[min(len(ancestors(A)) - 1, rng.randint(1, 30))]
    best = max(inT, key=lambda b: (b.h, -b.id))
    stats = dict(valid=0, cut=0, outside=0, added_outside=0, added=0, bad_added=0, skipped=0)
    on_chain = {x.id for x in ancestors(A)}
    for X in rng.sample(bs, 60):
        if X.id in on_chain or X.id in T:
            continue
        for slot in (X.slot, X.slot + rng.choice((-3, -1, 1, 3))):
            G = lca(X, A)
            valid = slot == X.slot < A.slot and A.slot - G.slot <= WF
            if not (A.slot - WF < slot < A.slot):          # limit 1: the entry cannot be valid
                stats["skipped"] += 1
                assert not valid
                continue
            for case in ("holds A's parent", "starts from B_imm"):
                known = [A.parent, best, imm] if case == "holds A's parent" else [imm]
                start = max((lca(X, k) for k in known if k is not None), key=lambda b: b.h)
                path = [x for x in ancestors(X) if x.h > start.h][::-1]      # parent first, ends at X
                local = set(T)
                stopped = False
                for Y in path:
                    if Y.id in local:
                        continue
                    assert Y.parent.id in local                              # the stream is parent first
                    ca = lca(Y, A)
                    if A.slot - ca.slot > WF or (Y.slot >= slot and Y.id != X.id):
                        stopped = True
                        break
                    local.add(Y.id)
                    stats["added"] += 1
                    if not (A.slot - lca(Y, A).slot <= WF and (Y.slot < slot or Y.id == X.id)):
                        stats["bad_added"] += 1                              # (b)
                    if Y.id == X.id and Y.slot != slot:
                        stats["uncle_wrong_slot"] = stats.get("uncle_wrong_slot", 0) + 1
                    if A.slot - G.slot > WF:
                        stats["added_outside"] += 1                          # (c)
                if valid:
                    stats["valid"] += 1
                    if X.id not in local:
                        stats["cut"] += 1                                    # (a)
                if A.slot - G.slot > WF:
                    stats["outside"] += 1
    return stats


if __name__ == "__main__":
    tot = {}
    for sd in range(400):
        for key, v in run(sd).items():
            tot[key] = tot.get(key, 0) + v
    print(f"valid entries downloaded: {tot['valid']}, cut off: {tot['cut']} (a)")
    print(f"blocks added: {tot['added']}, outside the window or past the entry's slot: {tot['bad_added']} (b);"
          f" of them the named block of an entry with a wrong slot: {tot.get('uncle_wrong_slot', 0)} (one block, inside the window)")
    print(f"downloads whose fork point lies outside the window: {tot['outside']}, blocks they added: {tot['added_outside']} (c)")
    print(f"entries skipped by the slot limit: {tot['skipped']}")
