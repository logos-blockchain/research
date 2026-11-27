"""Is the inferred stake non-decreasing in the counted slots, under master's integer algorithm?"""
import random
PREC = 1000
def tdiv(a, b):                     # Rust i128 division truncates toward zero
    q = abs(a) // abs(b); return q if (a >= 0) == (b >= 0) else -q
def infer(tse, N, PERIOD, f=1/30, beta=1.0):
    beta_p, f_p = int(beta * PREC), int(f * PREC)
    tse_p = tse * PREC
    meas, exp = N * PREC, PERIOD * f_p
    err = tdiv(tse_p * (exp - meas), exp)
    corr = tdiv(beta_p * err, PREC)
    return max(tdiv(tse_p - corr, PREC), 1)
rng = random.Random(1); checked = 0
for _ in range(3000):
    PERIOD = rng.choice([60, 600, 6 * 64800]); tse = rng.choice([1, 7, 1000, 10**9, rng.randrange(1, 10**15)])
    beta = rng.choice([1.0, 0.75, 0.5, 1.5, 2.0])
    Ns = sorted(rng.randrange(0, PERIOD + 1) for _ in range(40))
    vals = [infer(tse, N, PERIOD, beta=beta) for N in Ns]
    assert all(a <= b for a, b in zip(vals, vals[1:])), (PERIOD, tse, beta)
    checked += len(Ns)
print("monotone in N over", checked, "evaluations (beta 0.5..2)")
E = 6 * 64800
print("genuine N = 21,600:", infer(10**9, 21600, E), "| with 1 block's 4 forged entries:", infer(10**9, 21604, E),
      "| relative:", infer(10**9, 21604, E) / infer(10**9, 21600, E) - 1)
