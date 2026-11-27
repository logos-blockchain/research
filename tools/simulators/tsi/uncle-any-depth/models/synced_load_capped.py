# synced_load.py with the drafted retry rule: the wait starts at T_round, doubles, and never exceeds f^-1 slots.
import random
f, alpha, T_ROUND, PEERS, CAP = 1 / 30, 0.3, 1.0, 32, 30.0
p_honest = 1 - (1 - f) ** (1 - alpha)
def attempts(wait, mode):
    n, t, w = 0, 0.0, T_ROUND
    while t <= wait:
        n += 1; t += w
        if mode != "const": w = min(w * 2, CAP) if mode == "capped" else w * 2
    return n
rng = random.Random(1)
waits = [rng.expovariate(p_honest) for _ in range(100000)]
for mode in ("const", "doubling", "capped"):
    a = sum(attempts(w, mode) for w in waits) / len(waits) * 4
    print(f"{mode:9s}: {a:6.1f} downloads, {a*PEERS:6.0f} peer requests per node per forfeited win")
