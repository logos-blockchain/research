# A synced node: the attacker forfeits one win and publishes a child of the tip whose four entries name
# nothing. The block is longer than c_loc, so the node downloads its entries until a block it can adopt
# arrives at that height (the next honest block). A failed entry is repeated no sooner than T_round.
import math, random
f, alpha, T_ROUND, PEERS = 1 / 30, 0.3, 1.0, 32
p_honest = 1 - (1 - f) ** (1 - alpha)          # chance that an honest leader wins a slot
mean_wait = 1 / p_honest
def attempts(wait, backoff):
    n, t, w = 0, 0.0, T_ROUND
    while t <= wait:
        n += 1; t += w
        if backoff: w *= 2
    return n
rng = random.Random(1)
waits = [rng.expovariate(p_honest) for _ in range(100000)]
for backoff in (False, True):
    a = sum(attempts(w, backoff) for w in waits) / len(waits) * 4
    print(f"{'doubling wait' if backoff else 'every T_round'}: mean wait for an honest block {mean_wait:.0f} s,"
          f" {a:6.1f} downloads per node per forfeited win, {a*PEERS:7.0f} peer requests;"
          f" 1,000 nodes: {a*PEERS*1000/1e6:.2f} M requests")
