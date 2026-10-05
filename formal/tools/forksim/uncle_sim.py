"""How many honest-won slots does the TSI count see?

Slots 1..T. Each slot: honest winners ~ Poisson(lh) (each makes a block), the
adversary wins w.p. a. Honest proposers build on the longest chain they see and
include uncles by the specification's rule:
  U.parent on the chain, U not on it, U.slot < s, s - slot(U.parent) <= 360,
  U.slot not already occupied on the chain, at most 4, oldest (parent slot, slot, id) first.
Count N = distinct slots of the final chain's blocks and their uncles, inside a
middle window; H = slots with an honest block there.

Strategies:
  S0  delays uniform 1..D, ties random, adversary idle
  S1  delays D, ties chosen to keep forks balanced, adversary idle
  S2  S1, plus a balance attack: when the visible longest tip leads a competing
      branch by one, the adversary releases a block on the competing branch
      (from a won slot it has not used) to tie it again.
"""
import sys, math, random

UW, MAXU = 360, 4


class Sim:
    def __init__(self, T, h, a, D, strat, seed):
        self.T, self.D, self.strat = T, D, strat
        self.rng = random.Random(seed)
        self.lh = -math.log(1 - h)
        self.a = a
        # block: [id, parent, slot, height, honest, visible_from, uncles]
        self.blocks = [[0, -1, 0, 0, True, 0, []]]
        self.children = {0: []}
        self.adv_slots = []          # unused adversarial winning slots

    def poisson(self, lam):
        L, k, p = math.exp(-lam), 0, 1.0
        while True:
            p *= self.rng.random()
            if p <= L: return k
            k += 1

    def visible(self, s):
        return [b for b in self.blocks if b[5] <= s]

    def chain(self, bid, lo):
        out = []
        while bid != -1:
            b = self.blocks[bid]
            out.append(bid)
            if b[2] < lo: break
            bid = b[1]
        return out

    def pending_height(self, tip, s):
        """height reachable on tip's subtree counting blocks not yet visible"""
        best, stack = self.blocks[tip][3], [tip]
        while stack:
            x = stack.pop()
            best = max(best, self.blocks[x][3])
            stack.extend(self.children.get(x, []))
        return best

    def choose_tip(self, s, vis):
        mh = max(b[3] for b in vis)
        tips = [b[0] for b in vis if b[3] == mh]
        if len(tips) == 1 or self.strat == 'S0':
            return self.rng.choice(tips)
        # keep forks balanced: extend the tip whose subtree is least advanced
        return min(tips, key=lambda t: (self.pending_height(t, s), self.rng.random()))

    def uncles_for(self, parent, s, vis):
        ch = self.chain(parent, s - 2 * UW)
        chs = set(ch)
        occ = set()
        for x in ch:
            b = self.blocks[x]
            occ.add(b[2])
            for u in b[6]: occ.add(self.blocks[u][2])
        cands = [b for b in vis if b[2] >= s - UW - 50 and b[0] not in chs and b[1] in chs
                 and b[2] < s and s - self.blocks[b[1]][2] <= UW and b[2] not in occ]
        cands.sort(key=lambda b: (self.blocks[b[1]][2], b[2], b[0]))
        out, used = [], set()
        for b in cands:
            if b[2] in used: continue
            out.append(b[0]); used.add(b[2])
            if len(out) == MAXU: break
        return out

    def add(self, parent, s, honest, vis_from, uncles):
        bid = len(self.blocks)
        self.blocks.append([bid, parent, s, self.blocks[parent][3] + 1, honest, vis_from, uncles])
        self.children.setdefault(parent, []).append(bid)
        self.children[bid] = []
        return bid

    def balance(self, s):
        """release an adversarial block that ties the visible longest tip"""
        vis = self.visible(s)
        mh = max(b[3] for b in vis)
        leaders = [b for b in vis if b[3] == mh]
        if len(leaders) != 1: return
        lead = leaders[0]
        lch = set(self.chain(lead[0], s - 3 * UW))
        # competing tips at height mh - 1 not on the leader's chain
        comp = [b for b in vis if b[3] == mh - 1 and b[0] not in lch]
        if not comp: return
        tip = max(comp, key=lambda b: b[2])
        usable = [u for u in self.adv_slots if tip[2] < u <= s]
        if not usable: return
        u = min(usable)
        self.adv_slots.remove(u)
        self.add(tip[0], u, False, s, [])

    def run(self):
        for s in range(1, self.T + 1):
            if self.rng.random() < self.a:
                self.adv_slots.append(s)
            if self.strat == 'S2':
                self.balance(s)
            k = self.poisson(self.lh)
            if k:
                vis = self.visible(s)
                for _ in range(k):
                    par = self.choose_tip(s, vis)
                    unc = self.uncles_for(par, s, vis)
                    d = self.D if self.strat != 'S0' else self.rng.randint(1, self.D)
                    self.add(par, s, True, s + d, unc)
        return self

    def count(self, lo, hi):
        H = {b[2] for b in self.blocks if b[4] and lo <= b[2] < hi and b[0] != 0}
        mh = max(b[3] for b in self.blocks)
        res = []
        for tip in [b[0] for b in self.blocks if b[3] == mh]:
            ch = self.chain(tip, -1)
            slots = set()
            for x in ch:
                b = self.blocks[x]
                if lo <= b[2] < hi:
                    slots.add(b[2])
                    for u in b[6]:
                        if lo <= self.blocks[u][2] < hi: slots.add(self.blocks[u][2])
            res.append((len(slots), len(slots & H)))
        N, NH = min(res)
        return len(H), N, NH


if __name__ == "__main__":
    T = int(sys.argv[1]) if len(sys.argv) > 1 else 40000
    for label, h, a in [("nominal b=0.2", 1 - (1 - 1 / 30) ** 0.8, 1 - (1 - 1 / 30) ** 0.2),
                        ("fast member b=0.2", 1 - math.exp(-0.037), 1 - math.exp(-0.25 * 0.037))]:
        for strat in ['S0', 'S1', 'S2']:
            tot = [0, 0, 0]
            for seed in range(3):
                Hc, N, NH = Sim(T, h, a, 11, strat, seed).run().count(2000, T - 2000)
                tot = [tot[0] + Hc, tot[1] + N, tot[2] + NH]
            print(f"{label:18s} {strat}: H={tot[0]:6d}  N/H={tot[1]/tot[0]:.3f}  "
                  f"honest counted={tot[2]/tot[0]:.3f}  mu_eff={1 - tot[1]/tot[0]:.3f}", flush=True)
