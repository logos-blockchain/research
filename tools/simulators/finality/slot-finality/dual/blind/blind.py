"""Blind recheck (2026-11-17): K with three disturbances at once.
Disturbances: delay 15 s in place of 10 s; a tenth of the honest stake offline with the inference
corrected (share s' = s / (s + 0.9 (1 - s)), scale 1); a deflated inference (scale 1 / (1 - share
used)). Study's wait bound on the slot lottery, nonce unbiased, 1e-9, f = 1/30.
Usage: python blind.py <jobs>   writes out/blind.txt. The outputs it rechecks were not read.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import env  # noqa: E402,F401
from joblib import Parallel, delayed  # noqa: E402

F, EPS = 1 / 30, 1e-9
H18, H10 = 64800, 36000


def off(s):
    return s / (s + 0.9 * (1 - s))


def cfg(s, d, offline, deflated):
    a = off(s) if offline else s
    return a, d, (1 / (1 - a) if deflated else 1.0)


def run(tag, s, d, offline, deflated, t_max=400_000):
    from finality_sim.waitbound import wait_curve, wait_needed
    a, d, sc = cfg(s, d, offline, deflated)
    c = wait_curve(t_max, a, d, F, floor=EPS / 100, scale=sc)
    w = wait_needed(c, EPS)
    at = lambda t: float(c[t - 1]) if c.size >= t else 0.0
    return tag, s, a, d, sc, (w / 3600 if w > 0 else float("nan")), at(H10), at(H18)


def chance(a, d, sc, t):
    from finality_sim.waitbound import wait_curve
    c = wait_curve(t, a, d, F, floor=EPS / 100, scale=sc)
    return float(c[t - 1]) if c.size >= t else 0.0


def factor(name, a, d, t, lo, hi):
    """Largest scale (3 decimals) with chance after t at most EPS. lo holds, hi fails."""
    lo_i, hi_i = round(lo * 1000), round(hi * 1000)
    assert chance(a, d, lo_i / 1000, t) <= EPS and chance(a, d, hi_i / 1000, t) > EPS
    while hi_i - lo_i > 1:
        m = (lo_i + hi_i) // 2
        if chance(a, d, m / 1000, t) <= EPS:
            lo_i = m
        else:
            hi_i = m
    return name, lo_i / 1000, chance(a, d, lo_i / 1000, t), chance(a, d, hi_i / 1000, t)


PAIRS = {"15 s + offline": (15, True, False), "15 s + deflated": (15, False, True),
         "offline + deflated (10 s)": (10, True, True), "all three": (15, True, True)}

if __name__ == "__main__":
    n = int(sys.argv[1])
    out = open("out/blind.txt", "w")

    def say(line):
        print(line, flush=True); out.write(line + "\n"); out.flush()

    jobs = [("(1) 30 %, 10 s, offline, deflated", 0.30, 10, True, True),
            ("(1) 30 %, 15 s, offline", 0.30, 15, True, False),
            ("(1) 30 %, 15 s, offline, deflated", 0.30, 15, True, True),
            ("(2) third, 10 s, offline, deflated", 1 / 3, 10, True, True),
            ("(2) third, 15 s, offline, deflated", 1 / 3, 15, True, True)]
    jobs += [(f"(3) {k}", p / 100, v[0], v[1], v[2]) for k, v in PAIRS.items() for p in range(18, 37)]
    res = list(Parallel(n_jobs=n)(delayed(run)(*j) for j in jobs))
    for r in res[:5]:
        say(f"{r[0]:36s} share {r[2]:.4f} scale {r[4]:.4f}: wait {r[5]:.2f} h, after 10 h {r[6]:.3g}, after 18 h {r[7]:.3g}")
    for k in PAIRS:
        rows = [r for r in res[5:] if r[0] == f"(3) {k}"]
        for name, i in (("18 h", 7), ("10 h", 6)):
            ok = [r for r in rows if r[i] <= EPS]
            if not ok:
                say(f"(3) {k}, {name}: below 18 %"); continue
            best = max(ok, key=lambda r: r[1])
            nxt = [r for r in rows if abs(r[1] - best[1] - 0.01) < 1e-9]
            say(f"(3) {k}, {name}: largest share {best[1]:.0%} (wait {best[5]:.2f} h); at {best[1] + 0.01:.0%} the wait is {nxt[0][5]:.2f} h" if nxt else f"(3) {k}, {name}: {best[1]:.0%} or more (wait {best[5]:.2f} h)")
    fj = [("(4) third, 15 s, 18 h", 1 / 3, 15, H18, 1.0, 1.1), ("(4) 30 %, 15 s, 18 h", 0.30, 15, H18, 1.43, 1.75),
          ("(4) 30 %, 15 s, 10 h", 0.30, 15, H10, 1.05, 1.10)]
    for r in Parallel(n_jobs=3)(delayed(factor)(*j) for j in fj):
        say(f"{r[0]}: largest factor {r[1]:.3f} (chance {r[2]:.3g}; at +0.001: {r[3]:.3g})")
