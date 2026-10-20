"""Phase J, J.2: every attack within a delay ``Δ`` on a fork choice that weighs every honest block
(PLAN.md Phase J).

**The fork choice.** Both variants of phase J weigh each side of a conflict by its blocks since the
closest common ancestor, one weight per win: (a) the chain with GHOST's weight, whose uncles carry
the orphans, and (b) Areon-Base with E's corrections, whose honest blocks reference only their
preferred frontier (E4). An honest block adds one to the side its producer prefers, and a coalition
win adds one to the side it is placed on. The attacks below act on that weight alone, so they are
the same on both variants; DAG.md J.2 states what the DAG's window changes.

**The lottery.** A slot holds Poisson numbers of honest blocks and of coalition wins, at rates
``-(1 - alpha) ln(1 - f)`` and ``-alpha ln(1 - f)`` (``finality_sim.balance``). A win placed later
keeps its slot, so it can sign a block on either side of a conflict that began before it.

**The delay.** The adversary delivers each honest block to each honest node at most ``delta``
slots late: a block of slot ``t`` is in every view from slot ``t + delta + 1`` on, and can be
withheld from a producer before. A phase is a run of honest blocks each at most ``delta`` slots
after the previous one; it closes ``delta`` slots after its last block, when every view holds it.

**The balance** (Gaži, Motaqy and Russell, ePrint 2024/1830, App. D). Two conflicting sides,
balanced. Each producer of a phase is shown every block of the phase but the latest, so the
phase's honest blocks alternate between the sides. A move shifts the difference of the sides by
one.

- *Ties the adversary steers* (a first-seen rule with the order of delivery the adversary's):
  pairs cancel, and a phase with an odd number of honest blocks costs one move, made when the
  phase closes on the side its first block did not take.
- *A fixed tie rule*: a producer at a tie extends the side the rule favours, so the second block
  of a phase reaches the other side only if its producer is first shown a move there. One move per
  phase that holds an honest block, due when its second block is made, or when it closes with one
  block. The balanced states are the tie and the other side one ahead; a phase with an even number
  of blocks passes from one to the other, and every move a state needs points the same way:
  toward the side the tie rule does not favour from the tie, back toward it from the other.

**Moves.** With ``moves = 1`` a move is a withheld win placed on a side. With ``moves = 2`` a
placed win can also be retracted once: a second block with the same win on the other side makes
its tag weigh on neither (E3), which moves the difference back by one.

- Ties steered: the adversary steers each phase's first block to a side holding a placement it can
  retract, so every win is worth two moves in either direction. The reserve ``s`` counts moves,
  two per withheld win and one per retractable placement.
- A fixed rule, *relaxed*: the same count of moves, as if the direction were free. It bounds what
  retraction can buy from above.
- A fixed rule, *realised*: a placement can be retracted only by a move that points the other way,
  so it serves the other balanced state. ``s`` counts withheld wins and ``r`` placements: those
  that serve the current state when ``r > 0``, the other when ``r < 0``. A move spends a
  placement that serves the current state if there is one, else places a win, which serves the
  other state. A phase with an even count turns ``r`` round. At each close the adversary may
  spend one more move to pass to the other state, and so turn ``r`` round: by the rule, when
  ``-r`` reaches ``max(1, s // 2)``; at best, whenever that serves it better, which
  ``curve(policy="best")`` decides by dynamic programming.

**The walk.** While the sides are balanced, ``s`` (and ``r``) is the reserve. When a move falls due
and the reserve has none, the honest blocks of that phase all go to the target's side ``X``, and
``s = R - D`` becomes negative: the withheld wins ``R`` less the lead ``D`` of ``X``; placements are
dropped. While ``s < 0`` every honest block adds to ``X`` and every win to ``R``, the private race;
at a phase's close, or between phases, with ``s >= 0`` the adversary places ``D`` wins on the other
side and balances again with the ``s`` wins left (``2 s`` moves with retraction and a free
direction). The modes:

- ``BALANCE``: the balance alone, which ends at the first move it cannot make (J.2.1);
- ``ATTACK``: the walk above (J.2.2);
- ``REFLECT``: the walk before the target, abandoned for a fresh conflict when it cannot make a
  move; its reserve when the target's phase opens is the premined reserve of ``ATTACK``;
- ``PRIVATE``: the private race of E2 and E5, never balanced: honest blocks of the first ``delta``
  slots after the target do not see it and count for neither side.

**Success.** The target opens a phase at slot ``t0``. A client accepts it at the end of slot
``t0 + k``. The attack succeeds at depth ``k`` if, at the end of some slot from ``t0 + k`` on, the
sides are balanced and the moves at hand cover the phase's pending move plus ``s_win``: 0 with ties
the adversary steers, or with a fixed rule that favours the adversary's side (the tie exploit of
J.1), and 1 with a fixed rule that favours the target's side. While balanced, each view can be made
to prefer either side, so the client that accepted the target can be moved off it. In ``PRIVATE``
the race succeeds when ``s >= s_win``.

A win can sit only below a block of an earlier slot. The walk lets a win made before both sides of
a conflict exist sit on either, which can overstate a conflict's reserve by the wins of its first
phase.
"""

from __future__ import annotations

import math

import numpy as np
from numba import njit

BALANCE, ATTACK, REFLECT, PRIVATE = 0, 1, 2, 3
MODES = {"balance": BALANCE, "attack": ATTACK, "reflect": REFLECT, "private": PRIVATE}


def rates(f: float, alpha: float) -> tuple[float, float]:
    """Honest blocks and coalition wins per slot."""
    lam = -math.log(1.0 - f)
    return (1.0 - alpha) * lam, alpha * lam


def model(ties: str, moves: int = 1, relaxed: bool = False) -> tuple[bool, bool, bool]:
    """``(fixed, unit, realised)``: a fixed tie rule; wins worth two moves in a free direction;
    a fixed rule's retraction with its direction kept."""
    fixed = {"steered": False, "fixed": True}[ties]
    if moves not in (1, 2):
        raise ValueError("moves is 1 or 2")
    unit = moves == 2 and (not fixed or relaxed)
    realised = moves == 2 and fixed and not relaxed
    return fixed, unit, realised


# --- the walk, one slot at a time -------------------------------------------------------------
# A state is (s, r, q, ps, u): s and r as above (r is 0 unless realised); q the quiet slots since
# the open phase's last honest block; ps 0 between phases, and in an open phase 1 / 2 for an even /
# odd count (ties steered), or 1 for one block with its move unpaid and 2 / 3 for a paid phase with
# an even / odd count (a fixed rule); u 0 balanced, 1 unbalanced (ATTACK), waiting for the phase to
# close (REFLECT) or racing (PRIVATE), and 2 for a balance that has failed (BALANCE).

@njit(cache=True)
def _wins(s, u, a, mode, unit):
    """The slot's wins join the reserve; they count before the slot's honest blocks."""
    if mode == REFLECT and u == 1:
        return s
    if unit and u == 0 and mode != PRIVATE:
        return s + 2 * a
    return s + a


@njit(cache=True)
def _move(s, r, realised):
    """One move the balance needs: ``(made, s, r)``."""
    if realised:
        if r > 0:
            return True, s, r - 1
        if s >= 1:
            return True, s - 1, r - 1
        return False, s, r
    if s >= 1:
        return True, s - 1, r
    return False, s, r


@njit(cache=True)
def _close(s, r, ps, u, fixed, mode, unit, realised, switch):
    """The phase closes: every view now holds its blocks. ``switch`` decides whether a realised
    fixed rule passes to the other state: -1 by the rule, 0 never, 1 whenever it can."""
    if mode == PRIVATE:
        return s, r, 0, 0, 1
    if u == 1:
        if mode == REFLECT:
            return 0, 0, 0, 0, 0
        if s >= 0:
            return (2 * s if unit else s), 0, 0, 0, 0
        return s, 0, 0, 0, 1
    due = (ps == 1) if fixed else (ps == 2)
    if due:
        made, s, r = _move(s, r, realised)
        if not made:
            if mode == BALANCE:
                return s, r, 0, 0, 2
            if mode == REFLECT:
                return 0, 0, 0, 0, 0
            return -1, 0, 0, 0, 1
    if realised:
        if ps == 2:                             # an even count passes to the other state
            r = -r
        if switch < 0:
            go = r <= -max(1, s // 2) and s >= 1
        else:
            go = switch == 1 and (s >= 1 or r > 0)
        if go:                                  # one more move, then the other state
            made, s, r = _move(s, r, realised)
            r = -r
    return s, r, 0, 0, 0


@njit(cache=True)
def _honest(s, r, q, ps, u, h, delta, fixed, mode, unit, realised, switch):
    """The slot's ``h`` honest blocks, then the close of the phase if this slot ends it."""
    if u == 2:
        return s, r, q, ps, u
    if mode == PRIVATE:
        return s - h, r, 0, 0, 1
    if mode == ATTACK and u == 1 and ps == 0 and s >= 0:
        s, r, u = (2 * s if unit else s), 0, 0  # between phases every view holds every block
    if h > 0:
        if u == 1:
            if mode == ATTACK:
                s -= h
            ps = 2
        elif fixed:
            before = 0 if ps == 0 else (1 if ps == 1 else 2)
            odd = (ps == 1 or ps == 3) != (h % 2 == 1)
            if before <= 1 and before + h >= 2:
                made, s, r = _move(s, r, realised)
                if not made:
                    if mode == BALANCE:
                        return s, r, 0, 0, 2
                    if mode == REFLECT:
                        s, r, ps, u = 0, 0, 2, 1        # wait for the close; start afresh
                    else:
                        s, r, ps, u = s - before - h, 0, 2, 1  # every block on the target's side
                else:
                    ps = 3 if odd else 2
            elif before == 0:
                ps = 1
            else:
                ps = 3 if odd else 2
        else:
            odd = (ps == 2) != (h % 2 == 1)
            ps = 2 if odd else 1
        if delta == 0:
            return _close(s, r, ps, u, fixed, mode, unit, realised, switch)
        return s, r, 0, ps, u
    if ps == 0:
        return s, r, 0, 0, u
    q += 1
    if q >= delta:
        return _close(s, r, ps, u, fixed, mode, unit, realised, switch)
    return s, r, q, ps, u


@njit(cache=True)
def _success(s, r, ps, u, fixed, mode, s_win, realised):
    if mode == PRIVATE:
        return s >= s_win
    if u != 0:
        return False
    pending = (1 if ps == 1 else 0) if fixed else (1 if ps == 2 else 0)
    hand = s + (max(r, 0) if realised else 0)
    return hand >= s_win + pending


# --- the exact distribution over slots ----------------------------------------------------------

def pmf(lam: float, n_max: int) -> np.ndarray:
    """Poisson probabilities of 0..n_max, the tail lumped into n_max."""
    p = np.array([math.exp(-lam) * lam ** n / math.factorial(n) for n in range(n_max + 1)])
    p[-1] += max(0.0, 1.0 - p.sum())
    return p


class Space:
    """The states of the walk for one point, and the slot's transitions as index tables."""

    def __init__(self, delta: int, fixed: bool, mode: int, unit: bool = False,
                 realised: bool = False, s_lo: int = -60, s_hi: int = 150, r_max: int = 0,
                 n_max: int = 6):
        self.delta, self.fixed, self.mode = int(delta), bool(fixed), int(mode)
        self.unit, self.realised = bool(unit), bool(realised)
        self.s_lo, self.s_hi, self.n_max = int(s_lo), int(s_hi), int(n_max)
        self.r_max = int(r_max) if realised else 0
        self.nq = max(int(delta), 1)
        self.nr = 2 * self.r_max + 1
        self.size = (s_hi - s_lo + 1) * self.nr * self.nq * 4 * 2
        self.win_next, self.hon_next, self.hon_keep, self.hon_go = _tables(
            self.s_lo, self.s_hi, self.r_max, self.nq, self.delta, self.fixed, self.mode,
            self.unit, self.realised, self.n_max)

    def index(self, s: int, r: int = 0, q: int = 0, ps: int = 0, u: int = 0) -> int:
        return _index(s, r, q, ps, u, self.s_lo, self.r_max, self.nq)

    def success(self, s_win: int) -> np.ndarray:
        return _success_mask(self.s_lo, self.s_hi, self.r_max, self.nq, self.fixed, self.mode,
                             s_win, self.realised)


@njit(cache=True)
def _index(s, r, q, ps, u, s_lo, r_max, nq):
    return ((((s - s_lo) * (2 * r_max + 1) + (r + r_max)) * nq + q) * 4 + ps) * 2 + u


@njit(cache=True)
def _tables(s_lo, s_hi, r_max, nq, delta, fixed, mode, unit, realised, n_max):
    """The wins' next states, and the honest blocks' next states with the switch of a realised
    fixed rule made by the rule, never, and whenever possible."""
    size = (s_hi - s_lo + 1) * (2 * r_max + 1) * nq * 4 * 2
    win_next = np.full((size, n_max + 1), -1, np.int64)
    hon = np.full((3, size, n_max + 1), -1, np.int64)
    for s in range(s_lo, s_hi + 1):
        for r in range(-r_max, r_max + 1):
            for q in range(nq):
                for ps in range(4):
                    for u in range(2):
                        i = _index(s, r, q, ps, u, s_lo, r_max, nq)
                        for n in range(n_max + 1):
                            s2 = min(_wins(s, u, n, mode, unit), s_hi)
                            win_next[i, n] = _index(s2, r, q, ps, u, s_lo, r_max, nq)
                            for k in range(3):
                                s3, r3, q3, ps3, u3 = _honest(s, r, q, ps, u, n, delta, fixed,
                                                              mode, unit, realised, k - 1)
                                if u3 == 2 or s3 < s_lo:
                                    continue
                                r3 = max(-r_max, min(r3, r_max))
                                hon[k, i, n] = _index(min(s3, s_hi), r3, q3, ps3, u3, s_lo,
                                                      r_max, nq)
    return win_next, hon[0], hon[1], hon[2]


@njit(cache=True)
def _success_mask(s_lo, s_hi, r_max, nq, fixed, mode, s_win, realised):
    size = (s_hi - s_lo + 1) * (2 * r_max + 1) * nq * 4 * 2
    out = np.zeros(size, np.bool_)
    for s in range(s_lo, s_hi + 1):
        for r in range(-r_max, r_max + 1):
            for q in range(nq):
                for ps in range(4):
                    for u in range(2):
                        out[_index(s, r, q, ps, u, s_lo, r_max, nq)] = _success(
                            s, r, ps, u, fixed, mode, s_win, realised)
    return out


@njit(cache=True)
def _forward(p, win_next, hon_next, pa, ph):
    """One slot: the wins, then the honest blocks."""
    mid = np.zeros_like(p)
    for i in range(p.size):
        m = p[i]
        if m == 0.0:
            continue
        for n in range(pa.size):
            mid[win_next[i, n]] += m * pa[n]
    out = np.zeros_like(p)
    for i in range(p.size):
        m = mid[i]
        if m == 0.0:
            continue
        for n in range(ph.size):
            j = hon_next[i, n]
            if j >= 0:
                out[j] += m * ph[n]
    return out


@njit(cache=True)
def _backward(e, win_next, hon_next, pa, ph):
    """The expectation of ``e`` one slot later, from each state."""
    mid = np.zeros_like(e)
    for i in range(e.size):
        acc = 0.0
        for n in range(ph.size):
            j = hon_next[i, n]
            if j >= 0:
                acc += ph[n] * e[j]
        mid[i] = acc
    out = np.zeros_like(e)
    for i in range(e.size):
        acc = 0.0
        for n in range(pa.size):
            acc += pa[n] * mid[win_next[i, n]]
        out[i] = acc
    return out


@njit(cache=True)
def _backward_best(e, win_next, hon_keep, hon_go, pa, ph):
    """``_backward`` with the switch chosen, after each slot's draws, to maximise ``e``."""
    mid = np.zeros_like(e)
    for i in range(e.size):
        acc = 0.0
        for n in range(ph.size):
            j, k = hon_keep[i, n], hon_go[i, n]
            v = e[j] if j >= 0 else 0.0
            if k >= 0 and e[k] > v:
                v = e[k]
            acc += ph[n] * v
        mid[i] = acc
    out = np.zeros_like(e)
    for i in range(e.size):
        acc = 0.0
        for n in range(pa.size):
            acc += pa[n] * mid[win_next[i, n]]
        out[i] = acc
    return out


@njit(cache=True)
def _eventually_best(win_next, hon_keep, hon_go, pa, ph, success, tol, max_iter):
    """``_eventually`` under the best switches."""
    e = success.astype(np.float64)
    for _ in range(max_iter):
        nxt = _backward_best(e, win_next, hon_keep, hon_go, pa, ph)
        change = 0.0
        for i in range(e.size):
            v = 1.0 if success[i] else nxt[i]
            d = abs(v - e[i])
            if d > change:
                change = d
            e[i] = v
        if change < tol:
            break
    return e


@njit(cache=True)
def _eventually(win_next, hon_next, pa, ph, success, tol, max_iter):
    """P(a success state is reached at some slot's end), from each state at a slot's end."""
    e = success.astype(np.float64)
    for _ in range(max_iter):
        nxt = _backward(e, win_next, hon_next, pa, ph)
        change = 0.0
        for i in range(e.size):
            v = 1.0 if success[i] else nxt[i]
            d = abs(v - e[i])
            if d > change:
                change = d
            e[i] = v
        if change < tol:
            break
    return e


@njit(cache=True)
def _stationary(p, win_next, hon_next, pa, ph, tol, max_iter):
    """Iterate the slot until the distribution moves by less than ``tol`` (L1)."""
    for _ in range(max_iter):
        nxt = _forward(p, win_next, hon_next, pa, ph)
        tot = nxt.sum()
        if tot > 0:
            nxt /= tot
        change = np.abs(nxt - p).sum()
        p = nxt
        if change < tol:
            break
    return p


def premine(f: float, alpha: float, delta: int, ties: str, moves: int = 1,
            relaxed: bool = False, s_lo: int = -60, s_hi: int = 150, r_max: int = 0,
            n_max: int = 6, tol: float = 1e-14, max_iter: int = 400_000) -> np.ndarray:
    """The reserve between phases, at the start of a slot, for a coalition that has balanced every
    conflict it could before the target (``REFLECT``): a distribution over ``(s, r)``, as an array
    indexed ``[s, r + r_max]`` for ``s = 0..s_hi``."""
    fixed, unit, realised = model(ties, moves, relaxed)
    lam_h, lam_a = rates(f, alpha)
    sp = Space(delta, fixed, REFLECT, unit, realised, s_lo, s_hi, r_max, n_max)
    p = np.zeros(sp.size)
    p[sp.index(0)] = 1.0
    p = _stationary(p, sp.win_next, sp.hon_next, pmf(lam_a, n_max), pmf(lam_h, n_max), tol,
                    max_iter)
    idle = np.array([[p[sp.index(s, r)] for r in range(-sp.r_max, sp.r_max + 1)]
                     for s in range(0, s_hi + 1)])
    return idle / idle.sum()


def private_premine(f: float, alpha: float, s_hi: int = 150, n_max: int = 6,
                    tol: float = 1e-15, max_iter: int = 2_000_000) -> np.ndarray:
    """The private race's premined lead at a slot's end, ``L' = max(0, L + A - H)`` (E2)."""
    lam_h, lam_a = rates(f, alpha)
    pa, ph = pmf(lam_a, n_max), pmf(lam_h, n_max)
    p = np.zeros(s_hi + 1)
    p[0] = 1.0
    for _ in range(max_iter):
        mid = np.zeros_like(p)
        for n in range(n_max + 1):
            mid[n:] += pa[n] * p[:p.size - n]
            mid[-1] += pa[n] * p[p.size - n:].sum()
        nxt = np.zeros_like(p)
        for n in range(n_max + 1):
            nxt[:p.size - n] += ph[n] * mid[n:]
            nxt[0] += ph[n] * mid[:n].sum()
        change = np.abs(nxt - p).sum()
        p = nxt / nxt.sum()
        if change < tol:
            break
    return p


def curve(f: float, alpha: float, delta: int, ties: str, mode: str, horizon: int,
          s_win: int | None = None, premined: bool = True, stop: float = 1e-11,
          moves: int = 1, relaxed: bool = False, policy: str = "rule", s_lo: int = -60,
          s_hi: int = 150, r_max: int = 24, n_max: int = 6) -> dict[str, np.ndarray]:
    """The attack's success against the depth ``k = 0..`` in slots, exactly.

    ``ties`` is "steered" or "fixed"; ``s_win`` defaults to 0 for steered ties and 1 for a fixed
    rule (pass 0 for the tie exploit); ``moves`` and ``relaxed`` as in ``model``, ``r_max`` the
    placements a realised fixed rule keeps. Returns ``ever`` (success at some slot from ``t0 + k``)
    and ``at`` (success at ``t0 + k``) for ``ATTACK`` and ``PRIVATE``, ``hold`` (the balance still
    standing) for ``BALANCE``. The curve stops once it falls below ``stop`` or at ``horizon``.

    ``policy = "best"`` lets a realised fixed rule choose each switch to maximise the curve at
    every depth: by backward induction, ``V_0`` the chance of success from each state (``ATTACK``)
    or 1 (``BALANCE``) and ``V_k`` the best expectation of ``V_{k - 1}`` one slot later. The
    target's own slot follows the rule (it closes no phase when ``delta >= 1``), and ``at`` is
    not computed.
    """
    fixed, unit, realised = model(ties, moves, relaxed)
    m = MODES[mode]
    if s_win is None:
        s_win = 1 if fixed else 0
    lam_h, lam_a = rates(f, alpha)
    pa, ph = pmf(lam_a, n_max), pmf(lam_h, n_max)
    ph_target = ph.copy()
    ph_target[0] = 0.0
    ph_target /= ph_target.sum()
    sp = Space(delta, fixed, m, unit, realised, s_lo, s_hi, r_max, n_max)
    p = np.zeros(sp.size)
    if m == PRIVATE:
        lead = private_premine(f, alpha, s_hi, n_max) if premined else np.eye(1, s_hi + 1)[0]
        for s, w in enumerate(lead):            # the target's slot: its wins, the target itself
            for n in range(n_max + 1):
                p[sp.index(min(s + n, s_hi) - 1, 0, 0, 0, 1)] += w * pa[n]
    else:
        if premined:
            start = premine(f, alpha, delta, ties, moves, relaxed, s_lo, s_hi, sp.r_max, n_max)
        else:
            start = np.zeros((s_hi + 1, sp.nr))
            start[0, sp.r_max] = 1.0
        for s in range(s_hi + 1):
            for j in range(sp.nr):
                if start[s, j] > 0:
                    p[sp.index(s, j - sp.r_max)] += start[s, j]
        p = _forward(p, sp.win_next, sp.hon_next, pa, ph_target)
    out = {"hold" if m == BALANCE else "ever": [], "at": []}
    none = np.eye(1, n_max + 1)[0]
    if policy == "best" and realised and m in (BALANCE, ATTACK):
        if m == BALANCE:
            v_k = np.ones(sp.size)
        else:
            v_k = _eventually_best(sp.win_next, sp.hon_keep, sp.hon_go, pa, ph,
                                   sp.success(s_win), 1e-16, 1_000_000)
        key = "hold" if m == BALANCE else "ever"
        for k in range(horizon + 1):
            if k > 0:
                v_k = _backward_best(v_k, sp.win_next, sp.hon_keep, sp.hon_go, pa, ph)
            v = float(p @ v_k)
            out[key].append(v)
            out["at"].append(float("nan"))
            if v < stop:
                break
        return {key: np.asarray(val) for key, val in out.items()}
    if m != BALANCE:
        success = sp.success(s_win)
        e = [_eventually(sp.win_next, sp.hon_next, pa, ph, success, 1e-16, 1_000_000)]
        if m == PRIVATE:                        # e[j]: j more slots whose honest blocks are blind
            for _ in range(delta):
                e.append(np.where(success, 1.0,
                                  _backward(e[-1], sp.win_next, sp.hon_next, pa, none)))
    for k in range(horizon + 1):
        if k > 0:
            quiet = m == PRIVATE and k <= delta
            p = _forward(p, sp.win_next, sp.hon_next, pa, none if quiet else ph)
        if m == BALANCE:
            v = p.sum()
            out["hold"].append(v)
            out["at"].append(v)
        else:
            v = float(p @ e[max(0, delta - k) if m == PRIVATE else 0])
            out["ever"].append(v)
            out["at"].append(float(p[success].sum()))
        if v < stop:
            break
    return {key: np.asarray(val) for key, val in out.items()}


def depth(values: np.ndarray, eps: float) -> int | None:
    """The first ``k`` from which ``values`` stays at or below ``eps``, or None."""
    v = np.asarray(values)
    above = np.nonzero(v > eps)[0]
    if above.size == 0:
        return 0
    k = int(above[-1]) + 1
    return k if k < v.size else None


def edge(f: float, delta: int, ties: str, moves: int = 1) -> float:
    """The largest share whose balance cannot last for ever: the moves a phase brings,
    ``moves`` per win, against the moves it costs, from the phase statistics of
    ``finality_sim.balance``. ``moves = 1`` is E5's edge."""
    from finality_sim.balance import phase_stats

    def gain(alpha):
        a, odd, busy = phase_stats(f, alpha, delta)
        return moves * a - (odd if ties == "steered" else busy)

    lo, hi = 1e-9, 0.5
    for _ in range(100):
        mid = (lo + hi) / 2
        if gain(mid) < 0:
            lo = mid
        else:
            hi = mid
    return lo


# --- the same walk, sampled -------------------------------------------------------------------

@njit(cache=True)
def draws(n_slots, lam_h, lam_a, seed):
    """Honest blocks and coalition wins of ``n_slots`` slots."""
    np.random.seed(seed)
    h = np.empty(n_slots, np.int64)
    a = np.empty(n_slots, np.int64)
    for t in range(n_slots):
        h[t] = np.random.poisson(lam_h)
        a[t] = np.random.poisson(lam_a)
    return h, a


@njit(cache=True)
def _play(h, a, delta, fixed, mode, s_win, k_max, extra, premined, s_lo, s_hi, unit, realised,
          r_max):
    """The walk replayed on draws: for each target, success at each depth ``0..k_max``.

    Targets open a phase (``PRIVATE``: every occupied slot). Before each, the coalition's reserve
    follows ``REFLECT`` (``PRIVATE``: the premined lead) when ``premined``, else it is 0. The
    reserve is capped at ``s_hi`` and the placements at ``r_max``, as in ``Space``. Returns
    the counts of targets that succeed at the end of slot ``t0 + k`` (``at``), at some slot from
    ``t0 + k`` to ``t0 + k_max + extra`` (``ever``), or whose balance still stands (``hold``,
    ``BALANCE``), and the number of targets.
    """
    n = h.size
    at = np.zeros(k_max + 1, np.int64)
    ever = np.zeros(k_max + 1, np.int64)
    targets = 0
    rs, rr, rq, rps, ru = 0, 0, 0, 0, 0           # the reserve before the target (REFLECT)
    lead = 0                                      # the private race's premined lead
    horizon = k_max + extra
    for t0 in range(n - horizon - 1):
        opens = h[t0] > 0 and (rps == 0 if mode != PRIVATE else True)
        if opens:
            targets += 1
            last = -1
            r = 0
            if mode == PRIVATE:
                s = (lead if premined else 0) + a[t0] - 1
                q, ps, u = 0, 0, 1
                if _success(s, r, ps, u, fixed, mode, s_win, realised):
                    last = 0
                    at[0] += 1
            else:
                s = rs if premined else 0
                r = rr if premined else 0
                q, ps, u = 0, 0, 0
                s = min(_wins(s, u, a[t0], mode, unit), s_hi)
                s, r, q, ps, u = _honest(s, r, q, ps, u, h[t0], delta, fixed, mode, unit,
                                         realised, -1)
                s, r = min(s, s_hi), max(-r_max, min(r, r_max))
                if mode == BALANCE:
                    if u == 2:
                        last = -2
                elif _success(s, r, ps, u, fixed, mode, s_win, realised):
                    last = 0
                    at[0] += 1
            died = -1 if last != -2 else 0
            for k in range(1, horizon + 1 if died < 0 else 1):
                t = t0 + k
                if mode == PRIVATE:
                    s += a[t]
                    if k > delta:
                        s -= h[t]
                    ok = _success(s, r, ps, u, fixed, mode, s_win, realised)
                else:
                    s = min(_wins(s, u, a[t], mode, unit), s_hi)
                    s, r, q, ps, u = _honest(s, r, q, ps, u, h[t], delta, fixed, mode, unit,
                                             realised, -1)
                    s, r = min(s, s_hi), max(-r_max, min(r, r_max))
                    if mode == BALANCE:
                        if u == 2:
                            died = k
                            break
                        continue
                    ok = _success(s, r, ps, u, fixed, mode, s_win, realised)
                if ok:
                    last = k
                    if k <= k_max:
                        at[k] += 1
                if s < s_lo and (mode == PRIVATE or u == 1):
                    break
            if mode == BALANCE:
                stood = k_max + 1 if died < 0 else min(died, k_max + 1)
                for k in range(stood):
                    ever[k] += 1
            else:
                for k in range(min(last, k_max) + 1):
                    ever[k] += 1
        # the coalition's state before the next slot
        if mode == PRIVATE:
            lead = max(0, lead + a[t0] - h[t0])
        else:
            rs = min(_wins(rs, ru, a[t0], REFLECT, unit), s_hi)
            rs, rr, rq, rps, ru = _honest(rs, rr, rq, rps, ru, h[t0], delta, fixed, REFLECT,
                                          unit, realised, -1)
            rs, rr = min(rs, s_hi), max(-r_max, min(rr, r_max))
    return at, ever, targets


def play(f: float, alpha: float, delta: int, ties: str, mode: str, n_slots: int, k_max: int,
         seed: int, s_win: int | None = None, extra: int = 4000, premined: bool = True,
         moves: int = 1, relaxed: bool = False, s_lo: int = -60, s_hi: int = 150,
         r_max: int = 24) -> tuple[np.ndarray, np.ndarray, int]:
    """``_play`` on fresh draws: ``(at, ever, targets)``; for ``BALANCE``, ``ever`` holds the
    balances still standing."""
    fixed, unit, realised = model(ties, moves, relaxed)
    if s_win is None:
        s_win = 1 if fixed else 0
    lam_h, lam_a = rates(f, alpha)
    h, a = draws(n_slots, lam_h, lam_a, seed)
    return _play(h, a, int(delta), fixed, MODES[mode], int(s_win), int(k_max), int(extra),
                 premined, int(s_lo), int(s_hi), unit, realised, int(r_max) if realised else 0)


# --- the private race without delay, as B3 and E2 score it ---------------------------------------

@njit(cache=True)
def private_race_blocks(h, a, k_max, give_up, win_at, first, last):
    """E2's private race (``areon.dag_race`` with ``descendants_only``, no window) on per-slot
    draws without delay, every honest block a target and depth in occupied slots.

    Honest blocks are numbered in slot order; targets are blocks ``first..last-1``. Before each,
    the premined lead follows ``L = max(0, L - 1)`` per honest block with the slot's wins counted
    first. The race starts at ``L - 1``; the target's later siblings in its slot do not descend from
    it and count for neither side; each later honest block counts for the target's side. Returns
    successes per depth (index ``K - 1``) and the scored targets.
    """
    n = h.size
    succ = np.zeros(k_max, np.int64)
    scored = 0
    total = 0
    for t in range(n):
        total += h[t]
    lead_before = np.zeros(total, np.int64)
    slot_of = np.zeros(total, np.int64)
    rank = np.zeros(total, np.int64)
    b = 0
    lead = 0
    for t in range(n):
        lead += a[t]
        for j in range(h[t]):
            lead_before[b] = lead
            slot_of[b] = t
            rank[b] = j
            b += 1
            lead = lead - 1 if lead > 0 else 0
    best = np.empty(k_max, np.int64)
    for b in range(first, min(last, total)):
        t0 = slot_of[b]
        r = lead_before[b] - 1
        for kk in range(k_max):
            best[kk] = -(1 << 40)
        depth = 0
        truncated = True
        for t in range(t0 + 1, n):
            if a[t] > 0:
                r += a[t]
                for kk in range(min(depth, k_max)):
                    if r > best[kk]:
                        best[kk] = r
                if r < -give_up and depth >= k_max:
                    truncated = False
                    break
            if h[t] > 0:
                depth += 1
                r -= 1
                for kk in range(min(depth, k_max)):
                    if r > best[kk]:
                        best[kk] = r
                r -= h[t] - 1
                if r < -give_up and depth >= k_max:
                    truncated = False
                    break
        if truncated and depth < k_max:
            continue
        scored += 1
        for kk in range(k_max):
            if best[kk] >= win_at:
                succ[kk] += 1
    return succ, scored
