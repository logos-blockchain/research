# Reference code for slot-based finality, the text that enters the specifications.
# fork-choice.md: common_prefix_depth, density, bootstrap_fork_choice, online_fork_choice.
# cryptarchia-total-stake-inference.md: density_over_slots.
# cryptarchia-v1-protocol.md: on_block, commit, prune_forks, prune_blocks, finality_floor.
# cryptarchia-v1-bootstr-sync.md: last_round, download_blocks from one peer, switch_to_online.
import hashlib
from itertools import count
from math import exp, lgamma, log

_serial = count()  # distinguishes blocks that share a parent and a slot

f = 1 / 30
k = 2160
KK = int(k / f + 0.5)  # K = floor(k / f); f is 1/30 exactly, so k/f is an integer
S_GEN = KK // 4        # s_gen = floor(k / 4f)
T_M = 15               # the message traversal time of the Blend Protocol, in slots
EPSILON = 1e-9


class Block:
    __slots__ = ("parent", "slot", "height", "uncles", "id")

    def __init__(self, parent, slot, uncles=()):
        self.parent = parent
        self.slot = slot
        self.height = parent.height + 1 if parent else 0
        self.uncles = tuple(uncles)
        self.id = hashlib.blake2b(
            (parent.id if parent else b"") + slot.to_bytes(8, "little") + next(_serial).to_bytes(8, "little"),
            digest_size=32).digest()

    def __repr__(self):
        return f"B(h={self.height},sl={self.slot})"


def ancestors(b):
    """b and every block below it, tip first."""
    while b is not None:
        yield b
        b = b.parent


def is_ancestor(a, b):
    return any(x is a for x in ancestors(b))


def block_id(b):
    return b.id


def tips(T):
    parents = {id(b.parent) for b in T if b.parent is not None}
    return [b for b in T if id(b) not in parents]


def grandparent(b, d):
    for _ in range(d):
        b = b.parent
    return b


def common_prefix_depth(b1, b2):
    seen = {id(x): d for d, x in enumerate(ancestors(b1))}
    for d2, x in enumerate(ancestors(b2)):
        if id(x) in seen:
            return seen[id(x)], d2
    raise ValueError("no common ancestor")


def density(b_i, d, s_gen):
    """Blocks of the chain of b_i in the s_gen slots following its d-th grandparent."""
    sl_t = grandparent(b_i, d).slot
    return sum(1 for x in ancestors(b_i) if sl_t < x.slot <= sl_t + s_gen)


def bootstrap_fork_choice(c_local, forks, K, s_gen, B_imm):
    c_max = c_local
    for c_fork in sorted(forks, key=block_id):
        if not is_ancestor(B_imm, c_fork):
            continue
        depth_max, depth_fork = common_prefix_depth(c_max, c_fork)
        sl_div = grandparent(c_max, depth_max).slot
        sl_top = max(c_max.slot, c_fork.slot)
        if sl_div + K > sl_top:
            if depth_max < depth_fork:
                c_max = c_fork
        else:
            if density(c_max, depth_max, s_gen) < density(c_fork, depth_fork, s_gen):
                c_max = c_fork
    return c_max


def online_fork_choice(c_local, forks, B_imm):
    c_max = c_local
    for c_fork in sorted(forks, key=block_id):
        if not is_ancestor(B_imm, c_fork):
            continue
        depth_max, depth_fork = common_prefix_depth(c_max, c_fork)
        if depth_max < depth_fork:
            c_max = c_fork
    return c_max


def density_over_slots(c, s, p):
    """Distinct occupied slots in [s, s + p) of the chain of c."""
    occupied = set()
    for x in ancestors(c):
        if x.slot < s:
            break
        if x.slot < s + p:
            occupied.add(x.slot)
            occupied.update(u.slot for u in x.uncles if s <= u.slot < s + p)
    return len(occupied)


def prune_blocks(B_new, B_old, T):
    B, Tp = B_new, set(T)
    while B is not B_old:
        Tp.discard(B)
        B = B.parent
    return Tp


def common_ancestor(a, b):
    d, _ = common_prefix_depth(a, b)
    return grandparent(a, d)


def prune_forks(T, B):
    Tp = set(T)
    for B_tip in tips(T):
        B_div = common_ancestor(B_tip, B)
        if B_div is not B:
            Tp = prune_blocks(B_tip, B_div, Tp)
    return Tp


def child_on_chain(B, c):
    child = None
    for x in ancestors(c):
        if x is B:
            return child
        child = x
    raise ValueError("B is not on the chain of c")


def commit(T, c_loc, B_imm, K, phi):
    B = B_imm
    while B is not c_loc:
        C = child_on_chain(B, c_loc)
        if C.slot + K > c_loc.slot or density_over_slots(c_loc, C.slot + 1, c_loc.slot - C.slot) < phi:
            break
        B = C
    return prune_forks(T, B), B


def blocks_short(n, K, f, t_m):
    """P(N < n), N the blocks of the chain in K slots while all of the stake builds, each gap
    t_m slots plus a geometric wait at f."""
    p_h = f
    slots = K - n * t_m
    if slots < n:
        return 1.0
    return sum(
        exp(lgamma(slots + 1) - lgamma(i + 1) - lgamma(slots - i + 1)
            + i * log(p_h) + (slots - i) * log(1 - p_h))
        for i in range(n)
    )


def finality_floor(K, f, t_m, epsilon):
    n = 0
    while blocks_short(n + 1, K, f, t_m) <= epsilon:
        n += 1
    return n


class State:
    def __init__(self, genesis, K, s_gen, phi, rule, t_off=None):
        self.c_loc = genesis
        self.B_imm = genesis
        self.T = {genesis}
        self.K, self.s_gen, self.phi, self.rule = K, s_gen, phi, rule
        self.t_off = t_off if t_off is not None else max(1, K // 54)  # T_offline in slots; K/54 as specified
        self.recorded = genesis  # the block recorded when the Prolonged Bootstrap Period started


def on_block(st, B):
    """Chain maintenance, with block validation reduced to rules 5, 7 and 8."""
    if B in st.T or B.parent not in st.T or B.slot <= B.parent.slot or B.height <= st.B_imm.height:
        return
    T = st.T | {B}
    c = B if B.parent is st.c_loc else st.c_loc
    if st.rule == "BOOTSTRAP":
        c = bootstrap_fork_choice(c, tips(T), st.K, st.s_gen, st.B_imm)
    elif B.parent is not st.c_loc:
        c = online_fork_choice(st.c_loc, tips(T), st.B_imm)
    st.c_loc, st.T = c, T
    if st.rule == "ONLINE":
        st.T, st.B_imm = commit(st.T, st.c_loc, st.B_imm, st.K, st.phi)


MAX_ADDITIONAL_BLOCKS = 5  # the limit on KnownBlocks.additional_blocks


class Peer:
    """A peer as the last round sees it."""

    def __init__(self, tip, serve=None, ibd=False, tips=None, batch=None):
        self.tip = tip        # what it returns to GetTipRequest; None if the request fails
        self._tips = list(tips) if tips is not None else None  # successive answers; the last repeats
        self._serve = serve   # a stream of its own, for a peer that misbehaves
        self.ibd = ibd        # an IBD peer; otherwise another connected peer
        self.batch = batch    # the most blocks it returns to one request; None for no limit

    def get_tip(self):
        if self._tips is None:
            return self.tip
        return self._tips.pop(0) if len(self._tips) > 1 else self._tips[0]

    def holds(self, b):
        tips = [self.tip] + (self._tips or [])
        return any(t is not None and is_ancestor(b, t) for t in tips)

    def stream(self, target, known_blocks):
        """What an honest peer streams when asked for the blocks up to `target`, parents first.
        It starts after the highest block that the chain of `target` shares with a known block
        it holds. It rejects a request with too many known blocks."""
        if len(known_blocks) > 2 + MAX_ADDITIONAL_BLOCKS:
            return []
        path = list(ancestors(target))[::-1]                 # the Genesis block first
        index = {id(b): i for i, b in enumerate(path)}
        start = 0                                             # every peer holds the Genesis block
        for kb in known_blocks:
            if self.holds(kb):
                start = max(start, next(index[id(x)] for x in ancestors(kb) if id(x) in index))
        return path[start + 1:][:self.batch]

    def serve(self, target, known_blocks):
        if self._serve is not None:
            return self._serve(target, known_blocks)
        return self.stream(target, known_blocks)


def blocks_behind_tip(st, gaps):
    """For each gap, the latest block of the local chain whose slot lies at least that far behind
    the slot of its tip, where one exists."""
    out = []
    for gap in gaps:
        for x in ancestors(st.c_loc):
            if x.slot + gap <= st.c_loc.slot:
                out.append(x)
                break
    return out


def start_bootstrap_period(st):
    """What the node records when the Prolonged Bootstrap Period starts."""
    behind = blocks_behind_tip(st, [st.K])
    st.recorded = behind[0] if behind else st.B_imm


def download_blocks(st, target, peer, known=()):
    """The blocks up to `target` from one peer, as cryptarchia-v1-bootstr-sync.md prints it. A
    generator: it yields each valid block the peer delivered, so that several downloads can take
    turns. It ends when the target is in the tree, when a request brings no block, or when a
    block fails."""
    latest = None
    while True:
        if target in st.T:
            return
        additional = list(known) + ([latest] if latest is not None else [])
        received = 0
        for b in peer.serve(target, [st.c_loc, st.B_imm] + additional):
            received += 1
            latest = b
            on_block(st, b)
            if b not in st.T:
                return
            yield b
            if b is target:
                return
        if received == 0:
            return


def last_round(st, peers, limit):
    """Every peer is handled on its own, here one step of each in turn. In a step the node asks
    the peer's tip if no download is running, and takes one block of the download. A step in
    which a download has returned, or a tip request has failed, stands for the wait of T_round.
    `limit` steps stand for T_offline.

    The requests of a download name the block recorded when the Prolonged Bootstrap Period
    started. They also name the last valid block the peer delivered in an earlier download of
    the round, or, if there is none, the latest blocks of the local chain at least T_offline,
    s_gen and K behind its tip.

    The handling of a peer ends when the tip it returns is in the local block tree. Otherwise
    the handling of an IBD peer ends once the peer has delivered no block that counts for
    `limit` steps, and the handling of any other peer `limit` steps after the round started.
    A block counts if it is valid and the peer has not delivered it earlier in the round."""
    handled = [(p, None, 0, set(), None) for p in peers]
    step = 0
    while handled:
        still = []
        for p, download, idle, seen, last in handled:
            if (idle if p.ibd else step) >= limit:
                continue                                   # its handling has ended
            counts = False
            if download is None:
                tip = p.get_tip()
                if tip is not None and tip in st.T:
                    continue                               # its tip is in the local block tree
                if tip is not None:
                    known = [st.recorded] + ([last] if last is not None else
                                             blocks_behind_tip(st, [st.t_off, st.s_gen, st.K]))
                    download = download_blocks(st, tip, p, known)
            if download is not None:
                b = next(download, None)
                if b is None:
                    download = None                        # it returned; ask the tip again
                else:
                    last = b
                    if b not in seen:
                        seen.add(b)
                        counts = True
            still.append((p, download, 0 if counts else idle + 1, seen, last))
        handled, step = still, step + 1


def switch_to_online(st):
    st.rule = "ONLINE"
    st.T, st.B_imm = commit(st.T, st.c_loc, st.B_imm, st.K, st.phi)
