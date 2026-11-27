"""Option 'age' when the chain grows faster than the target, with a reference window that is short against k/f (as in reality)."""
import contextlib, io, sys
with contextlib.redirect_stdout(io.StringIO()):
    import verdicts
from verdicts import *
from option_ab import NA
def fast(opt, growth, seeds=4, k=60, n=8, f0=1/10):
    ok = 0; lag = []
    for s in range(seeds):
        p = P(k=k, f=f0, W=6, n=n); p.f = growth * f0; age = int(k / f0)
        net = mk(opt, p, s)
        for nd in net.N:
            if hasattr(nd, "AGE"): nd.AGE = age
        net.N[n - 1].up = False
        for _ in range(2 * age): net.step()
        net.N[n - 1].up = True
        for _ in range(age // 4): net.step()
        best = max(net.N[i].c.h for i in range(n - 1)); lag.append(best - net.N[n - 1].c.h); ok += lag[-1] <= 4
    return f"{opt:8s} growth x{growth}: {age//4} slots after it starts, the syncing node is on the chain in {ok} of {seeds}, behind by {sorted(lag)} blocks (k = {k}, k/f = {age} slots, window {p.w} slots)"
if __name__ == "__main__":
    for g in (1.0, 1.5, 2.0):
        for opt in ("drafted", "age"): print(fast(opt, g), flush=True)
