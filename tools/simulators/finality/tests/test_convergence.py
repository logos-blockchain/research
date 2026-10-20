"""Gates for the convergence-opportunity region on the slot lottery (finality_sim.convergence)."""

import math

from finality_sim import convergence
from finality_sim.balance import threshold


def test_the_rate_is_the_lotterys():
    for f, alpha, delta in ((0.1, 1 / 3, 5), (1 / 30, 1 / 3, 10)):
        n = 10_000_000
        sampled, count = convergence.simulated_rate(f, alpha, delta, n, seed=7)
        sem = math.sqrt(count) / (n - 2 * delta)
        assert abs(sampled - convergence.rate(f, alpha, delta)) < 4 * sem


def test_finer_slots_reach_the_continuous_region():
    """Slots a hundred times finer reach rho_a < rho_h exp(-2 rho_h Delta), the region Gaži,
    Motaqy and Russell give for this technique (ePrint 2024/1830, revision 2025-02-20, p. 2)."""
    for f, delta in ((1 / 30, 10), (0.1, 5)):
        lam = -math.log(1 - f)
        lo, hi = 0.0, 0.5
        for _ in range(100):
            mid = (lo + hi) / 2
            if mid < (1 - mid) * math.exp(-2 * (1 - mid) * lam * delta):
                lo = mid
            else:
                hi = mid
        fine = convergence.edge(1 - math.exp(-lam / 100), 100 * delta)
        assert abs(fine - lo) < 1e-3


def test_the_technique_certifies_less_than_ghosts_region():
    """The tight region with ties steered by the adversary is strictly larger than the one this
    technique certifies (ePrint 2024/1830, p. 2)."""
    for f in (1 / 30, 1 / 20, 1 / 15, 0.1, 0.25):
        for delta in (1, 2, 5, 10, 20):
            assert convergence.edge(f, delta) < threshold(f, delta, "adversarial")


def test_with_retraction_every_edge_tends_to_a_third():
    """When a second copy of a win retracts the first, each win answers two phases. With no
    delay every honest block is its own phase, so the balance holds once 2·λ_a exceeds λ_h:
    the edges tend to a third in fine slots, and at today's rate they lie below the edges with
    one move per win at every delay."""
    for ties in ("adversarial", "deterministic"):
        assert abs(convergence.retraction_threshold(1 / 3000, 1, ties) - 1 / 3) < 1e-3
        for delta in (1, 2, 5, 10, 20):
            assert convergence.retraction_threshold(1 / 30, delta, ties) < threshold(1 / 30, delta, ties)
    assert abs(convergence.edge(1 / 3000, 1, events=2) - 1 / 3) < 1e-3


class _Tree:
    """Blocks with win tags; a child of ``c`` weighs the tags under it found under no sibling;
    equal weights go to the child with the smaller tag (J.1)."""

    def __init__(self):
        self.parent, self.tag, self.kids = {0: None}, {0: -1}, {0: []}

    def add(self, parent, tag):
        b = len(self.parent)
        self.parent[b], self.tag[b], self.kids[b] = parent, tag, []
        self.kids[parent].append(b)
        return b

    def tags(self, b):
        out, stack = set(), [b]
        while stack:
            v = stack.pop()
            out.add(self.tag[v])
            stack.extend(self.kids[v])
        return out

    def weights(self, c):
        t = {k: self.tags(k) for k in self.kids[c]}
        return {k: len(t[k] - set().union(*(t[j] for j in t if j != k))) for k in t}

    def preferred(self, c):
        w = self.weights(c)
        return max(w, key=lambda k: (w[k], -self.tag[k]))


def test_a_retraction_answers_a_second_honest_block():
    """With no delay, a coalition answers each honest block with one move and keeps the two sides
    of a fork within one, the side it trails always the one the honest blocks join. Answering on
    the trailing side with fresh wins for a stretch, then leading the other side by one and
    retracting those wins one by one, costs n + 1 wins for 2n honest blocks."""
    t, n = _Tree(), 6
    x, y = t.add(0, 2000), t.add(0, 5)          # equal weights favour y, whose first tag is smaller
    honest, fresh, placed = 3000, 0, []        # coalition tags are 100 + the wins spent
    for _ in range(n):                          # each honest block joins y; a fresh win on x answers
        assert t.preferred(0) == y
        t.add(y, honest)
        honest += 1
        fresh += 1
        t.add(x, 100 + fresh)
        placed.append(100 + fresh)
        w = t.weights(0)
        assert w[x] == w[y]
    fresh += 1                                  # one more on x: x leads by one
    t.add(x, 100 + fresh)
    placed.append(100 + fresh)
    for _ in range(n):                          # each honest block joins x; a retraction answers
        assert t.preferred(0) == x
        t.add(x, honest)
        honest += 1
        t.add(y, placed.pop(0))                 # the same tag under y: it weighs on neither side
        w = t.weights(0)
        assert w[x] == w[y] + 1
    assert fresh == n + 1 and honest - 3000 == 2 * n
