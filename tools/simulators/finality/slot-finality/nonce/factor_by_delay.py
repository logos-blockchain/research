# The two-nonce factor of design D1 (one delay on today's chain value) by worst-case delay, 5 to 15 s,
# read by ../dual/delay/delay_nonce.py. Per nonce: delayed_chain.D1.factor; squared for two nonces.
# Usage: python factor_by_delay.py > factor_by_delay.out
from joblib import Parallel, delayed

CASES = [(4.5, 1), (4.5, 100), (4.5, 10000), (6.0, 100), (6.0, 10000), (9.0, 10000)]


def row(alpha, delta):
    from delayed_chain import D1
    m = D1(alpha, delta)
    return alpha, delta, [m.factor(t, e) ** 2 for t, e in CASES]


if __name__ == "__main__":
    jobs = [(a, d) for a in (0.30, 1 / 3) for d in range(5, 16)]
    print("two-nonce factor of D1; columns: (delay T in hours, coalition's delay machines) = " + ", ".join(str(c) for c in CASES))
    for a, d, fs in Parallel(n_jobs=11)(delayed(row)(a, d) for a, d in jobs):
        print(f"{'30 %' if a == 0.30 else 'a third':8s} | {d:2d} s | " + " | ".join(f"{f:10.6g}" for f in fs))
