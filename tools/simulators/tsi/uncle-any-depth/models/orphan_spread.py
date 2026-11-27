"""The same block X, broadcast while its parent is held by one node only: how many nodes hold X after their orphan downloads?

N nodes. At receipt every node asks 16 + 16 random peers once for X. A peer that holds X serves it and its parent (the target is the only
holder at first). After a failed try the node asks again after one second, up to `tries` tries in all (the node of today: 1).
`serve`: the target serves the block (today), or does not because its parent was never disseminated.
"""
import random
rng = random.Random(4)
def run(N, tries, fan, serve):
    hold = {0}; served = {0} if serve else set()
    for t in range(tries):
        new = set()
        for i in range(1, N):
            if i in hold: continue
            if any(p in served for p in rng.sample(range(N), fan)): new.add(i)
        hold |= new; served |= new
    return len(hold) / N
for N in (200, 1000, 5000):
    for serve in (True, False):
        print(f"N = {N:4d}, the target {'serves' if serve else 'does not serve'} the block: share of the nodes that hold X after 1 / 2 / 3 / 4 tries: "
              + " / ".join(f"{sum(run(N, t, 32, serve) for _ in range(5)) / 5:.3f}" for t in (1, 2, 3, 4)))
