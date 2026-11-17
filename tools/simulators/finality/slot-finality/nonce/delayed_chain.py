# Design D1: one sequential delay on today's hash-chain value, read at the cut-off.
#   pre-nonce = eta of the last block before the cut-off (today's rule, unchanged)
#   nonce     = hash(delay(pre-nonce)); the delay takes T on the coalition's fastest machine.
# A candidate is a fork point and a subset of the coalition's wins after it. Its pre-nonce exists
# once the fork point's block exists. The coalition sees its nonce T later. The candidate counts
# only if its branch can still be published then (model.survival). With E delay machines the
# coalition sees at most E candidates of a surviving branch. The honest value is seen T after the
# cut-off, and counts as a blind switch if a choice is still open then (model.open_after).
#   factor per nonce <= 1 + open(T - one gap) + open(2T)
#                        + E * sum over rounds k >= 1 and fork points of survival(max(kT, age at the cut-off))
# E is the coalition's total number of delay machines; the bound gives each fork point all E, so it
# overstates. A branch counts while it leads by one block (the finality study's convention); if a
# tie could be kept alive by delivery order, survival would be about 1.3 times larger.
# The wait is read off the finality study's wait bound (wait_curves.py), the factor squared for an
# attack that meets two nonces.
# Usage: python delayed_chain.py > delayed_chain.out
import numpy as np

from model import Walk, clock

EPS = 1e-9
STEP = 60
HMAX = 14
CELLS = [(0.30, 10), (0.30, 15), (1 / 3, 10), (1 / 3, 15)]


def name(alpha):
    return "30 %" if alpha == 0.30 else "a third"


def tag(alpha):
    return "30" if alpha == 0.30 else "33"


def curves(alpha, delta):
    w = Walk(alpha, delta)
    ts = list(range(STEP, HMAX * 3600 + 1, STEP))
    return np.array(ts), w.curve(w.start_at_block(), ts), w.curve(w.start_at_cutoff(), ts)


def wait_hours(alpha, delta, factor):
    c = np.load(f"wait_curve_{tag(alpha)}_{delta}.npy")
    hit = np.nonzero(c <= EPS / factor)[0]
    return (hit[0] + 1) / 3600 if hit.size else float("nan")


def largest_factor(alpha, delta, hours):
    c = np.load(f"wait_curve_{tag(alpha)}_{delta}.npy")
    return EPS / c[int(hours * 3600) - 1]


class D1:
    def __init__(self, alpha, delta):
        self.alpha, self.delta = alpha, delta
        self.ts, self.s, self.o = curves(alpha, delta)
        self.rate = 1 / clock(alpha, delta)

    def parts(self, hours):
        i = int(round(hours * 3600 / STEP)) - 1
        t = self.ts[i]
        # A machine can run again on the same fork point: its rounds end k*T after the fork point,
        # k = 1, 2, ... A fork point of age u at the cut-off counts in round k if its branch survives
        # max(k*T, u). Sums over ages are taken from above (the curve falls).
        seen, k = 0.0, 1
        while k * (i + 1) - 1 < self.ts.size:
            j = k * (i + 1) - 1
            seen += self.rate * (self.ts[j] * self.s[j] + STEP * self.s[j:].sum())
            k += 1
        # The honest value is known from the last honest block before the cut-off (one step of
        # 60 s earlier covers a gap), and can be switched blind again at 2T.
        blind = self.o[max(i - 1, 0)] + (self.o[2 * i] if 2 * i < self.o.size else 0.0)
        return blind, seen

    def factor(self, hours, machines):
        o, seen = self.parts(hours)
        return 1 + o + machines * seen


if __name__ == "__main__":
    ds = {c: D1(*c) for c in CELLS}
    np.savez("delayed_chain_curves.npz", **{f"{tag(a)}_{d}_{k}": getattr(ds[(a, d)], k) for a, d in CELLS for k in ("ts", "s", "o")})
    print("0. check of the wait curves: factor 1 and 1.21")
    for a, d in CELLS:
        print(f"   {name(a):8s} {d} s: {wait_hours(a, d, 1):.2f} h, {wait_hours(a, d, 1.21):.2f} h;  "
              f"largest two-nonce factor that 18 h absorbs {largest_factor(a, d, 18):.3g}, 10 h {largest_factor(a, d, 10):.3g}")
    print("\n1. factor per nonce, by delay T (hours on the coalition's fastest machine) and number of delay machines E")
    print("share | delay | T (h) | blind switch | seen per machine | E=1 | E=100 | E=1e4 | E=1e6 | wait (h), two nonces: E=1 | 100 | 1e4 | 1e6")
    for a, d in CELLS:
        for hours in (1, 2, 3, 4, 4.5, 6, 9, 12):
            o, seen = ds[(a, d)].parts(hours)
            fs = [ds[(a, d)].factor(hours, e) for e in (1, 100, 1e4, 1e6)]
            ws = [wait_hours(a, d, f * f) for f in fs]
            print(f"{name(a):8s} | {d:2d} s | {hours:4.1f} | {o:8.2e} | {seen:8.2e} | " + " | ".join(f"{f:9.4g}" for f in fs)
                  + " | " + " | ".join(f"{w:6.2f}" for w in ws))
    print("\n2. the shortest delay T (hours, steps of 0.1) that keeps the factor per nonce at or below 1.10, by E")
    print("share | delay | E=1 | 100 | 1e4 | 1e6 | 1e8")
    for a, d in CELLS:
        row = []
        for e in (1, 100, 1e4, 1e6, 1e8):
            t = next((h / 10 for h in range(2, 139) if ds[(a, d)].factor(h / 10, e) <= 1.10), float("nan"))
            row.append(t)
        print(f"{name(a):8s} | {d:2d} s | " + " | ".join(f"{t:4.1f}" for t in row))
    print("\n3. a coalition whose machine is s times faster than the design assumes: the design sets T = 4.5 h, 6 h, 9 h")
    print("share | delay | design T (h) | speed s | E | factor per nonce | wait (h), two nonces")
    for a, d in CELLS:
        for t0 in (4.5, 6, 9):
            for s in (1, 1.5, 2, 3, 5):
                for e in (1, 100, 1e4):
                    f = ds[(a, d)].factor(max(t0 / s, 0.2), e)
                    print(f"{name(a):8s} | {d:2d} s | {t0:3.1f} | {s:3.1f} | {e:6.0f} | {f:10.4g} | {wait_hours(a, d, f * f):6.2f}")
