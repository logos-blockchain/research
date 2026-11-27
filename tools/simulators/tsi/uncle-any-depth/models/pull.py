"""How fast does a missing uncle spread by pull, when few nodes hold it as the referencing block is gossiped?

Each node that receives A without holding X sends its request to up to 16 of its connected peers and 16
random other peers (Selecting Peers for Downloading), takes the first answer, then can serve X itself.
A request round takes rtt seconds. retry = None models a node that gives up after one failed request.
"""
import random, statistics as st
import heapq

def run(n=1000, conn=20, holders0=1, rtt=0.5, retry=1.0, gossip=1.5, seed=0):
    rng = random.Random(seed)
    nb = [set() for _ in range(n)]
    for i in range(n):
        while len(nb[i]) < conn:
            j = rng.randrange(n)
            if j != i: nb[i].add(j); nb[j].add(i)
    t_have = [float("inf")] * n
    for i in rng.sample(range(n), holders0): t_have[i] = 0.0
    ev = []
    for i in range(n):
        if t_have[i] > 0: heapq.heappush(ev, (rng.uniform(0, gossip), i))
    gave_up = 0
    while ev:
        t, i = heapq.heappop(ev)
        asked = rng.sample(sorted(nb[i]), min(16, len(nb[i]))) + rng.sample(range(n), 16)
        if any(t_have[j] <= t + rtt / 2 for j in asked):
            t_have[i] = t + rtt
        elif retry is None: gave_up += 1
        elif t < 120: heapq.heappush(ev, (t + rtt + retry, i))
    got = sorted(x for x in t_have if x < float("inf"))
    q = lambda p: got[int(p * n) - 1] if len(got) >= p * n else float("nan")
    return q(.5), q(.9), q(.99), len(got) / n

for holders, label in ((1, "only the proposer"), (10, "1 % of the nodes"), (100, "10 %"), (500, "50 %")):
    for retry in (1.0, None):
        R = [run(holders0=holders, retry=retry, seed=s) for s in range(20)]
        m = [st.mean(r[i] for r in R) for i in range(4)]
        print(f"X held by {label:18s} retry {str(retry):5s}: half the nodes hold X after {m[0]:.1f} s, 90 % {m[1]:.1f} s, 99 % {m[2]:.1f} s; final share {100*m[3]:.1f} %")
