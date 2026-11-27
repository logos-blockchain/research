# A node whose c_loc lags (after IBD, or held back by a missing uncle) prefers every chain that is
# longer than c_loc. It must fetch H honest uncles of the chain of best_tip(). The attacker has pushed
# one sibling per past win (same slot, same proof, same parent as its chain block, four entries naming
# nothing), and each sibling is longer than c_loc, so it is "a chain the node would prefer to c_loc".
# The per-win rule groups a sibling with the attacker's chain block of the same win only; across wins
# nothing orders or limits the downloads. Downloads run one after another; a failed entry comes back
# no sooner than T_ROUND after it failed (bb03ffaf). An honest entry succeeds with probability P_OK.
import random, statistics

def run(H, F, policy, seed, T_ROUND=1.0, L_FAIL=0.5, L_OK=0.5, P_OK=0.9):
    rng = random.Random(seed)
    entries = [("h", i) for i in range(H)] + [("f", i) for i in range(F)]
    next_ok = {e: 0.0 for e in entries}        # earliest time an entry may be requested again
    fails = {e: 0 for e in entries}
    have = set(); t = 0.0; futile = 0
    while len(have) < H:
        ready = [e for e in entries if e not in have and next_ok[e] <= t]
        if not ready:
            t = min(next_ok[e] for e in entries if e not in have); continue
        if policy == "best_tip first":
            honest = [e for e in ready if e[0] == "h"]
            e = rng.choice(honest) if honest else rng.choice(ready)
        else:
            e = rng.choice(ready)
        if e[0] == "h" and rng.random() < P_OK:
            t += L_OK; have.add(e)
        else:
            t += L_FAIL; fails[e] += 1
            futile += e[0] == "f"
            wait = T_ROUND * (2 ** (fails[e] - 1) if policy == "backoff" else 1)
            next_ok[e] = t + wait
    return t, futile

H = 600                                          # honest uncles of the last k blocks (490 to 700 at design load)
for F in (0, 4 * 100, 4 * 648):                  # 648 = alpha*k past attacker wins at alpha = 0.3
    for policy in ("as written", "best_tip first", "backoff"):
        if F == 0 and policy != "as written":
            continue
        rs = [run(H, F, policy, sd) for sd in range(5)]
        t = statistics.mean(r[0] for r in rs); fut = statistics.mean(r[1] for r in rs)
        print(f"F={F:5d} fake entries, {policy:15s}: all {H} honest uncles after {t/60:6.1f} min, "
              f"{fut:7.0f} futile downloads ({fut*32:9.0f} peer requests)")
