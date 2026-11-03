"""Phase L.2 and L.3: Casper FFG run by Blend's declared nodes on the engine's block trees
(PLAN.md Phase L).

A checkpoint is a pair ``(round, block)``. Round 0's checkpoint is the genesis block, justified and
final at every node from the start. Rounds start every ``R`` slots. In round ``r``, at ``t``:

- each voting node ``i`` takes as its source the latest checkpoint it holds justified: the
  justified checkpoint of the latest round whose justification reached it by ``t``;
- it takes as its target its checkpoint of round ``r``: the latest block at least ``L`` slots old
  on its best received chain among the chains that contain the source's block (Casper FFG's fork
  choice, "follow the chain containing the justified checkpoint of the greatest height"), or the
  source's block itself while no block above it is that old;
- its vote, the link (source, target), reaches node ``j`` at ``t + delay[i, j]``.

A checkpoint of round ``r`` is justified once the votes for one link to it carry ``q`` of the
declared weight. Node ``j`` holds it justified once those votes have reached it and it holds the
link's source justified. A justified checkpoint of round ``r`` is finalized once round ``r + 1``
justifies a link from it, and node ``j`` holds it final once it holds the second justified. A block
is final at node ``j`` once ``j`` holds final a checkpoint whose block is the block or descends
from it.

Weights: one per declaration, ``n_declared`` in all. ``voters`` marks the honest declarations that
vote. With ``coalition > 0`` the coalition's declarations sign every link an honest node casts, at
once and at every node, as a coalition that signs on every side does; it adds ``coalition`` to each
link's weight. Withheld, it adds nothing, and its declarations still count in the total.

The engine builds its trees with the plain longest-chain rule. Where a justified checkpoint falls
off the engine's final chain, the gadget's fork choice would have kept nodes on it: such
checkpoints are counted (``off_chain``), and a run is read only where there are none.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from finality_sim.votes import local_tips


def descends(tree, b: int, a: int) -> bool:
    """``b`` is ``a`` or one of its descendants."""
    sa = tree.slot[a]
    while b > 0 and tree.slot[b] > sa:
        b = int(tree.parent[b])
    return b == a


def target_of(tree, tip: int, t: float, lag: int) -> int:
    """The latest ancestor of ``tip``, itself included, whose slot is at most ``t − lag``."""
    b = tip
    while b > 0 and tree.slot[b] > t - lag:
        b = int(tree.parent[b])
    return b


def descendant_mask(tree, root: int) -> np.ndarray:
    """``root`` and its descendants. A block's parent has a lower id, as the engine builds them."""
    mask = np.zeros(tree.n_blocks, dtype=bool)
    mask[root] = True
    parent = tree.parent
    for b in range(root + 1, tree.n_blocks):
        if mask[parent[b]]:
            mask[b] = True
    return mask


def vote_target(tree, tip: int, root: int, t: float, lag: int) -> int:
    """The target a node votes from source block ``root``: the latest block at least ``lag`` slots
    old on the chain to ``tip``, or ``root`` itself while no block above it is that old."""
    b = target_of(tree, tip, t, lag)
    return b if descends(tree, b, root) else root


def best_descendant(tree, row: np.ndarray, t: float, root: int,
                    mask: np.ndarray | None = None) -> int:
    """The best block a node holds by ``t`` among ``root`` and its descendants: height, then
    earlier slot, then lower id, as the engine's fork choice; ``root`` if it holds none of them.
    ``row`` is the node's arrivals; ``mask``, if given, is ``descendant_mask(tree, root)``."""
    if mask is None:
        mask = descendant_mask(tree, root)
    held = (row <= t) & mask
    held[root] = True
    c2 = float(tree.n_blocks + 1)
    c1 = (float(tree.slot.max()) + 2.0) * c2
    key = tree.height * c1 - tree.slot * c2 - np.arange(tree.n_blocks)
    return int(np.where(held, key, -np.inf).argmax())


@dataclass
class Checkpoint:
    round: int
    block: int
    source: int                       # index of the source checkpoint in ``Run.checkpoints``
    held: np.ndarray                  # per node, when it holds this checkpoint justified
    final: np.ndarray | None = None   # per node, when it holds it final


@dataclass
class Run:
    rounds: np.ndarray
    checkpoints: list[Checkpoint]
    justified_rounds: int = 0
    finalized_rounds: int = 0
    restricted: int = 0               # votes whose best chain had to be restricted to the source
    off_chain: int = 0                # justified checkpoints off the engine's final chain
    first_off: int = -1               # the round of the first, or -1; later rounds follow it
    conflicts: int = 0                # rounds with two conflicting justified checkpoints
    finalized_conflicts: int = 0      # conflicting pairs of finalized checkpoints
    per_round: list[int] = field(default_factory=list)   # justified checkpoints per round


def link_times(delay: np.ndarray, voters: np.ndarray, t: float, need: int,
               cross: np.ndarray | None = None) -> np.ndarray:
    """When each node holds ``need`` of the votes cast at ``t`` by ``voters``: the ``need``-th
    smallest arrival. Where ``cross[i, j]`` is finite it replaces ``t + delay[i, j]``, for a vote
    that crosses a partition's cut."""
    n = delay.shape[1]
    if need <= 0:
        return np.full(n, t)
    if need > voters.size:
        return np.full(n, np.inf)
    arr = t + delay[voters]
    if cross is not None:
        c = cross[voters]
        arr = np.where(np.isfinite(c), c, arr)
    return np.partition(arr, need - 1, axis=0)[need - 1]


def run_gadget(tree, arrival: np.ndarray, delay: np.ndarray, voters: np.ndarray, rounds,
               lag: int, n_declared: int, q: float = 2 / 3, coalition: int = 0,
               cut=None, tips_cache: dict | None = None) -> Run:
    """Play the gadget over ``rounds``, the round starts in slots, ascending; round 0 at genesis is
    implicit. ``voters`` are node ids. ``cut(t)``, when given, returns for votes cast at ``t`` a
    matrix of arrival times where a vote crosses a partition's cut, ``inf`` elsewhere, or
    ``None`` outside the partition. ``tips_cache`` keeps each round start's best received
    blocks across runs on one tree."""
    offsets: dict[tuple, np.ndarray] = {}     # quorum delays of a voter set, without a cut
    masks: dict[int, np.ndarray] = {}         # descendants of a justified checkpoint's block
    n_nodes = arrival.shape[0]
    need_total = math.ceil(q * n_declared - 1e-9)
    canonical = np.zeros(tree.n_blocks, dtype=bool)
    canonical[np.asarray(tree.canonical_chain(), dtype=np.int64)] = True
    canonical[0] = True
    genesis = Checkpoint(round=0, block=0, source=-1, held=np.full(n_nodes, -np.inf),
                         final=np.full(n_nodes, -np.inf))
    run = Run(rounds=np.asarray(rounds, dtype=float), checkpoints=[genesis])
    finals: list[int] = [0]
    voters = np.asarray(voters, dtype=np.int64)
    source = np.zeros(n_nodes, dtype=np.int64)     # each node's latest checkpoint held justified
    pending: list[int] = []                         # checkpoints some node does not hold yet
    for r, t in enumerate(run.rounds.tolist(), start=1):
        if tips_cache is not None and t in tips_cache:
            tips = tips_cache[t]
        else:
            tips = local_tips(tree, arrival, t)
            if tips_cache is not None:
                tips_cache[t] = tips
        still = []
        for c_id in pending:
            held = run.checkpoints[c_id].held <= t
            source = np.where(held & (c_id > source), c_id, source)
            if not held.all():
                still.append(c_id)
        pending = still
        src = source[voters]
        pairs, inv = np.unique(np.stack([src, tips[voters]]), axis=1, return_inverse=True)
        inv = inv.reshape(-1)
        tgt = np.empty(pairs.shape[1], dtype=np.int64)
        for k in range(pairs.shape[1]):
            root, tip = run.checkpoints[int(pairs[0, k])].block, int(pairs[1, k])
            tgt[k] = vote_target(tree, tip, root, t, lag) if descends(tree, tip, root) else -1
        tgt = tgt[inv]
        for k in np.nonzero(tgt < 0)[0].tolist():  # a node whose best chain left its source
            i = int(voters[k])
            root = run.checkpoints[int(src[k])].block
            if root not in masks:
                masks[root] = descendant_mask(tree, root)
            tip = best_descendant(tree, arrival[i], t, root, masks[root])
            tgt[k] = vote_target(tree, tip, root, t, lag)
            run.restricted += 1
        links: dict[tuple[int, int], np.ndarray] = {}
        keys, which = np.unique(np.stack([src, tgt]), axis=1, return_inverse=True)
        which = which.reshape(-1)
        for k in range(keys.shape[1]):
            links[(int(keys[0, k]), int(keys[1, k]))] = voters[which == k]
        cross = cut(t) if cut is not None else None
        made = []
        for (s_id, b_id), ids in links.items():
            if ids.size + coalition < need_total:
                continue
            need = need_total - coalition
            if cross is None:
                o_key = (need, ids.size, hash(ids.tobytes()))
                if o_key not in offsets:
                    offsets[o_key] = link_times(delay, ids, 0.0, need)
                held = t + offsets[o_key]
            else:
                held = link_times(delay, ids, t, need, cross)
            held = np.maximum(held, run.checkpoints[s_id].held)
            run.checkpoints.append(Checkpoint(round=r, block=b_id, source=s_id, held=held))
            made.append(len(run.checkpoints) - 1)
            if not canonical[b_id]:
                run.off_chain += 1
                if run.first_off < 0:
                    run.first_off = r
            prev = run.checkpoints[s_id]
            if prev.round == r - 1 and prev.final is not None:    # a second finalizing link
                prev.final = np.minimum(prev.final, np.maximum(prev.held, held))
            elif prev.round == r - 1:
                prev.final = np.maximum(prev.held, held)
                run.finalized_rounds += 1
                # the finalized blocks form one branch per conflict: extend the branch the new one
                # descends from, or open a new branch that conflicts with every other
                x = prev.block
                ext = [k for k, b in enumerate(finals) if descends(tree, x, b)]
                if ext:
                    finals[ext[0]] = x
                elif not any(descends(tree, b, x) for b in finals):
                    run.finalized_conflicts += len(finals)
                    finals.append(x)
        pending.extend(made)
        blocks = [run.checkpoints[c].block for c in made]
        if any(not (descends(tree, x, y) or descends(tree, y, x)) for x in blocks for y in blocks):
            run.conflicts += 1
        run.per_round.append(len(made))
        run.justified_rounds += bool(made)
    return run


def block_final_times(tree, run: Run, blocks: np.ndarray) -> np.ndarray:
    """Per block (rows) and node (columns), the time the node holds final a checkpoint whose block
    is the block or descends from it; ``inf`` if none. Checkpoints are read in round order, and a
    later round never finalizes sooner at a node, so the first that holds a block decides."""
    chain = np.asarray(tree.canonical_chain(), dtype=np.int64)[::-1]     # genesis side first
    index = np.full(tree.n_blocks, -1, dtype=np.int64)
    index[chain] = np.arange(chain.size)
    order = np.argsort(np.where(index[blocks] >= 0, index[blocks], np.iinfo(np.int64).max),
                       kind="stable")
    out = np.full((blocks.size, run.checkpoints[0].held.size), np.inf)
    pending = [int(k) for k in order]          # canonical blocks by height, the rest after
    for c in run.checkpoints[1:]:
        if c.final is None or not pending:
            continue
        top = index[c.block]
        if top >= 0:                            # a canonical checkpoint holds a prefix of them
            j = 0
            while j < len(pending) and 0 <= index[blocks[pending[j]]] <= top:
                out[pending[j]] = c.final
                j += 1
            pending = pending[j:]
            continue
        still = []
        for k in pending:
            if descends(tree, c.block, int(blocks[k])):
                out[k] = c.final
            else:
                still.append(k)
        pending = still
    return out
