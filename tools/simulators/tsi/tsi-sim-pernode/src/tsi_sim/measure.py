"""Optimised per-node measurement pass.

The naive loop recomputes each node's canonical chain, density, and agreement fingerprint
independently — O(N x chain) Python and ~95% of an epoch. Two exact optimisations:

The counted density ``m`` is SLOT-based (canonical slots + recovered uncle slots — the
"one count per slot" invariant; ``legacy_block_count`` reproduces the old per-block count).

Counting models (``countable`` flag; CLI ``--old`` clears it):

* **countable** (default) — the spec's counting rules are re-checked per reference
  (cryptarchia-v1-protocol.md): the reference must be within the window
  (``0 < slot_B - slot_U <= w``), the uncle must not lie on the counting chain, and its
  **parent must lie on the counting chain** (only the first block of a fork counts).
  References failing the parent rule are tallied as ``deep`` diagnostics.
* **old** — every baked reference in the measurement window counts (fork depth ignored),
  reproducing the pre-redesign behaviour.

1. **Dedup by tip.** Nodes sharing a current tip share their whole canonical chain and every
   derived quantity, so we compute once per *distinct* tip and broadcast. High node agreement
   (the common case) collapses N to a handful of computations.
2. **numba kernel.** Each distinct tip's chain walk (honest count, deduped referenced uncles,
   recovered orphan slots, window-prefix fingerprint) runs as one cached, C-speed routine over
   flat arrays. A pure-Python fallback keeps the package importable without numba.

Results are identical to the naive per-node loop (``_reference`` in tests/test_measure.py;
see ``test_measure_matches_reference``).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import numpy as np

from .blocktree import BlockTree, tips_for_all_nodes

try:
    from numba import njit, uint64

    _HAVE_NUMBA = True
except ImportError:  # pragma: no cover - numba is an optional accelerator
    _HAVE_NUMBA = False


@dataclass
class Measurement:
    m: np.ndarray          # (N,) per-node counted density: canonical + recovered uncle SLOTS
                           #      (per-block-id count only under legacy_block_count=True)
    q: np.ndarray          # (N,) honest active-slot fraction
    q_eff: np.ndarray      # (N,) uncle-recovered fraction
    orphan_rate: np.ndarray  # (N,)
    ref_total: np.ndarray  # (N,) distinct referenced uncles examined in the window
    ref_deep: np.ndarray   # (N,) of those, rejected by the parent-on-chain (first-fork) rule;
                           #      always 0 under the old model (no rule to reject on)
    agreement_window: float
    agreement_tip: float


def _uncles_csr(tree: BlockTree) -> tuple[np.ndarray, np.ndarray]:
    """Flatten the ragged per-block uncle lists into CSR (flat ids + offsets)."""
    nb = tree.n_blocks
    ptr = np.zeros(nb + 1, np.int64)
    for b in range(nb):
        ptr[b + 1] = ptr[b] + len(tree.uncles[b])
    flat = np.empty(int(ptr[-1]), np.int64)
    for b in range(nb):
        for j, u in enumerate(tree.uncles[b]):
            flat[ptr[b] + j] = u
    return flat, ptr


def _measure_tips_py(distinct_tips, parent, slot, uncle_flat, uncle_ptr, T, w, countable,
                     uncle_stamp, honest_stamp, chain_stamp):
    """Pure-Python per-distinct-tip walk (fallback / reference for the kernel)."""
    K = distinct_tips.shape[0]
    m = np.empty(K, np.int64)
    n_honest = np.empty(K, np.int64)
    n_rec = np.empty(K, np.int64)
    n_ref = np.empty(K, np.int64)
    n_deep = np.empty(K, np.int64)
    chain_len = np.empty(K, np.int64)
    fp = np.empty(K, np.uint64)
    for ki in range(K):
        # pass 1: chain -> honest count, mark honest slots + chain membership, fingerprint
        honest = 0
        clen = 0
        f = np.uint64(0)
        b = int(distinct_tips[ki])
        while b > 0:
            clen += 1
            chain_stamp[b] = ki              # chain membership (any slot, incl. outside T)
            s = int(slot[b])
            if 0 <= s < T:
                honest += 1
                honest_stamp[s] = ki
                f ^= _mix_py(np.uint64(b))
            b = int(parent[b])
        # pass 2: deduped referenced uncles in window + recovered orphan slots
        ucnt = 0
        rec = 0
        refs = 0
        deep = 0
        b = int(distinct_tips[ki])
        while b > 0:
            for j in range(int(uncle_ptr[b]), int(uncle_ptr[b + 1])):
                u = int(uncle_flat[j])
                su = int(slot[u])
                if 0 <= su < T and uncle_stamp[u] != ki:
                    uncle_stamp[u] = ki      # dedup uncles by id
                    refs += 1
                    if countable:
                        # spec counting rules, re-checked per reference:
                        d = int(slot[b]) - su
                        if d <= 0 or d > w:
                            continue                     # outside the reference window
                        if chain_stamp[u] == ki:
                            continue                     # uncle lies on the counting chain
                        pu = int(parent[u])
                        if pu != 0 and chain_stamp[pu] != ki:
                            deep += 1                    # not a first fork block: uncounted
                            continue
                    ucnt += 1
                    if honest_stamp[su] != ki:
                        rec += 1             # recovered slots deduped by slot
                        honest_stamp[su] = ki
            b = int(parent[b])
        m[ki] = honest + ucnt
        n_honest[ki] = honest
        n_rec[ki] = rec
        n_ref[ki] = refs
        n_deep[ki] = deep
        chain_len[ki] = clen
        fp[ki] = f
    return m, n_honest, n_rec, n_ref, n_deep, chain_len, fp


def _mix_py(x: np.uint64) -> np.uint64:
    with np.errstate(over="ignore"):     # splitmix64 intentionally wraps mod 2^64
        x = (x ^ (x >> np.uint64(30))) * np.uint64(0xBF58476D1CE4E5B9)
        x = (x ^ (x >> np.uint64(27))) * np.uint64(0x94D049BB133111EB)
        return x ^ (x >> np.uint64(31))


if _HAVE_NUMBA:
    @njit(cache=True)
    def _mix(x):
        x = (x ^ (x >> uint64(30))) * uint64(0xBF58476D1CE4E5B9)
        x = (x ^ (x >> uint64(27))) * uint64(0x94D049BB133111EB)
        return x ^ (x >> uint64(31))

    @njit(cache=True)
    def _measure_tips_nb(distinct_tips, parent, slot, uncle_flat, uncle_ptr, T, w, countable,
                         uncle_stamp, honest_stamp, chain_stamp):
        K = distinct_tips.shape[0]
        m = np.empty(K, np.int64)
        n_honest = np.empty(K, np.int64)
        n_rec = np.empty(K, np.int64)
        n_ref = np.empty(K, np.int64)
        n_deep = np.empty(K, np.int64)
        chain_len = np.empty(K, np.int64)
        fp = np.empty(K, np.uint64)
        for ki in range(K):
            honest = 0
            clen = 0
            f = uint64(0)
            b = distinct_tips[ki]
            while b > 0:
                clen += 1
                chain_stamp[b] = ki          # chain membership (any slot, incl. outside T)
                s = slot[b]
                if 0 <= s < T:
                    honest += 1
                    honest_stamp[s] = ki
                    f ^= _mix(uint64(b))
                b = parent[b]
            ucnt = 0
            rec = 0
            refs = 0
            deep = 0
            b = distinct_tips[ki]
            while b > 0:
                for j in range(uncle_ptr[b], uncle_ptr[b + 1]):
                    u = uncle_flat[j]
                    su = slot[u]
                    if 0 <= su < T and uncle_stamp[u] != ki:
                        uncle_stamp[u] = ki      # dedup uncles by id
                        refs += 1
                        ok = True
                        if countable:
                            d = slot[b] - su
                            if d <= 0 or d > w:
                                ok = False               # outside the reference window
                            elif chain_stamp[u] == ki:
                                ok = False               # uncle lies on the counting chain
                            else:
                                pu = parent[u]
                                if pu != 0 and chain_stamp[pu] != ki:
                                    deep += 1            # not a first fork block: uncounted
                                    ok = False
                        if ok:
                            ucnt += 1
                            if honest_stamp[su] != ki:
                                rec += 1             # recovered slots deduped by slot
                                honest_stamp[su] = ki
                b = parent[b]
            m[ki] = honest + ucnt
            n_honest[ki] = honest
            n_rec[ki] = rec
            n_ref[ki] = refs
            n_deep[ki] = deep
            chain_len[ki] = clen
            fp[ki] = f
        return m, n_honest, n_rec, n_ref, n_deep, chain_len, fp


def measure(tree: BlockTree, A, active_slots: np.ndarray, T: int, cutoff: int,
            use_numba: bool = True, legacy_block_count: bool = False,
            countable: bool = False, w: int = 0) -> Measurement:
    """Per-node m/q/q_eff + agreement, deduped by tip and (optionally) numba-accelerated.

    ``countable`` applies the spec's per-reference counting rules (window ``w``,
    not-on-chain, parent-on-chain); ``countable=False`` reproduces the old model where every
    baked reference counts. ``A`` is the full ``(N, n_blocks)`` arrival matrix or a pruned
    ``SlidingArrival`` — only ``tips_for_all_nodes`` reads it, so ``N`` is taken from the
    returned per-node tips.
    """
    tips = tips_for_all_nodes(tree, A, cutoff)
    N = tips.shape[0]
    n_real = tree.n_blocks - 1
    n_active = int((active_slots < T).sum())

    distinct_tips, inverse = np.unique(tips, return_inverse=True)
    inverse = inverse.ravel()
    uncle_flat, uncle_ptr = _uncles_csr(tree)
    uncle_stamp = np.full(tree.n_blocks, -1, np.int64)
    honest_stamp = np.full(max(T, 1), -1, np.int64)
    chain_stamp = np.full(tree.n_blocks, -1, np.int64)

    kernel = _measure_tips_nb if (_HAVE_NUMBA and use_numba) else _measure_tips_py
    m_d, nh_d, nrec_d, nref_d, ndeep_d, clen_d, fp_d = kernel(
        distinct_tips.astype(np.int64), tree.parent, tree.slot,
        uncle_flat, uncle_ptr, np.int64(T), np.int64(w), bool(countable),
        uncle_stamp, honest_stamp, chain_stamp)

    # correct slot counting: canonical slots + recovered (non-canonical, deduped) uncle slots.
    # legacy_block_count reproduces the earlier per-block-id count (kernel's m = honest + ucnt).
    m = m_d[inverse] if legacy_block_count else (nh_d + nrec_d)[inverse]
    q = (nh_d[inverse] / n_active) if n_active else np.full(N, np.nan)
    q_eff = ((nh_d[inverse] + nrec_d[inverse]) / n_active) if n_active else np.full(N, np.nan)
    orphan_rate = ((n_real - clen_d[inverse]) / n_real) if n_real else np.zeros(N)

    node_counts = np.bincount(inverse, minlength=distinct_tips.shape[0])
    agreement_tip = float(node_counts.max()) / N
    fp_counts: Counter = Counter()
    for ki in range(distinct_tips.shape[0]):
        fp_counts[int(fp_d[ki])] += int(node_counts[ki])
    agreement_window = max(fp_counts.values()) / N

    return Measurement(m=m, q=q, q_eff=q_eff, orphan_rate=orphan_rate,
                       ref_total=nref_d[inverse], ref_deep=ndeep_d[inverse],
                       agreement_window=agreement_window, agreement_tip=agreement_tip)
