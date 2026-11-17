# The inputs of attack_rules.py for coalitions of 1, 5, 10, 15, 20 and 25 % (30 % and a third exist):
# the law of the choices at a cut-off (as today_choices.py) and the chance of the playable attack
# against a wait (as attack_today.py, up to 19 h), at worst cases of 10 s and 15 s.
# Usage: python by_share.py > by_share.out
import numpy as np
from joblib import Parallel, delayed

SHARES = (0.01, 0.05, 0.10, 0.15, 0.20, 0.25)


def tag(alpha):
    return f"{int(round(alpha * 100)):02d}"


def choices(alpha, delta):
    from model import rates
    from today_choices import log2_tail_table, sample
    a, h = rates(alpha)
    lg, lm, lm0, zs = sample(4_000_000, a, h, delta, 8000, 6000, 12345, log2_tail_table())
    np.save(f"today_log2G_{tag(alpha)}_{delta}.npy", np.sort(lg)[-400_000:].astype(np.float32))
    n0 = np.log2(1.0 + 2.0 ** np.minimum(lm0, 300.0))
    np.save(f"today_log2M0_{tag(alpha)}_{delta}.npy", np.sort(n0)[-400_000:].astype(np.float32))
    q = np.quantile(lg, [0.5, 0.9, 0.99, 0.999, 0.9999])
    return (f"{tag(alpha)} % | {delta} s | a choice complete at the cut-off {np.mean(lm0 > -np.inf):.4f}, with hindsight {np.mean(lg > 0):.4f} | "
            f"log2 choices at 50/90/99/99.9/99.99 %: " + " / ".join(f"{v:.1f}" for v in q)
            + " | P(choices complete at the cut-off >= 2^8, 2^16, 2^24): " + ", ".join(f"{np.mean(n0 >= x):.2e}" for x in (8, 16, 24)))


def attack(alpha, delta):
    import attack_today as at
    from model import rates
    at.HOURS_MAX = 19
    a, _ = rates(alpha)
    big, small, g, snaps = at.snapshots(alpha, delta)
    grid = np.arange(0, 65)
    rows = [at.chance(big, small, g, p, (i + 1) * at.QUARTER, a, grid) for i, p in enumerate(snaps)]
    np.save(f"attack_today_{tag(alpha)}_{delta}.npy", np.array(rows))
    return f"{tag(alpha)} % | {delta} s | attack rows saved: {len(rows)}"


if __name__ == "__main__":
    cells = [(a, d) for a in SHARES for d in (10, 15)]
    for a, d in cells:                     # the sampler is parallel inside
        print(choices(a, d), flush=True)
    for line in Parallel(n_jobs=12)(delayed(attack)(a, d) for a, d in cells):
        print(line, flush=True)
