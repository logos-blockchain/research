"""Phase K.9: the floor counted as the stake inference counts (SLOTS.md K.9).

    python scripts/k9_occupancy.py      # needs runs/a1; writes runs/k9/ (under a minute)

The inference counts occupied slots: a slot holding a canonical block or an uncle the chain
references, each slot once (cryptarchia-total-stake-inference.md). With one uncle a block it
recovers the honest stake at 0.998–1.001 under Blend (reports/tsi/README.md §3.2a). A floor on that
count reads the honest chain at OCC = 0.998 of its stake's occupancy under random delay, the lowest
completeness that sweep measured, binomial at OCC·occupancy(f, 1 − α), where K.3's floor on
canonical blocks reads it at A1's growth. A side at its
fastest holds one block per occupied slot, so it counts the same either way. Under the worst case
the count of occupied slots is at least the count of canonical blocks on every path, and no larger
worst-case floor is read: the protocol keeps the worst case's floor on blocks.

- floor.csv: the floor at K = ⌊k/f⌋ and 3⌊k/f⌋ against 25 %, 30 % and a third, on blocks under
  random delay and the worst case at 10 s (K.3) and on occupied slots under random delay, with the
  largest side each holds back.
- protection.csv: the days a side at its fastest takes to fix a fork under the depth form, at the
  worst case's floor and at the floor on occupied slots, on average and at the earliest with
  chance ε (floor.blocks_time).
- stall.csv: the least share whose chain reaches the worst case's floor within K with chance
  1 − ε (cap.resume_share), counted on blocks and on occupied slots under random delay; and the
  days until a block made as the active stake falls to r is fixed under the depth form, with no
  cap (cap.depth_finality).
- quorum.csv: the least window at which a floor separates the sides of every partition under random
  delay, both the honest chain and the side counted on occupied slots, beside K.3's on blocks
  (floor.least_quorum_window).
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

from k3_splits import growth
from finality_sim.cap import depth_finality, resume_share
from finality_sim.floor import (blocks_time, chain_rate, floor_for, least_quorum_window,
                                log_short, provisional_share, quorum)

HERE = pathlib.Path(__file__).resolve().parent.parent
OUT = HERE / "runs" / "k9"
F = 1 / 30
EPS = 1e-9
DELTA = 10
KF = math.floor(2160 / F)
EPOCH, PERIOD = 10 * KF, 6 * KF
WINDOWS = {"⌊k/f⌋": KF, "3⌊k/f⌋": 3 * KF}
ALPHAS = (0.25, 0.30, 1 / 3)
SIGMAS = (0.10, 0.20, 0.25, 0.30, 1 / 3)
FALLS = (0.70, 0.60, 0.50, 0.40)
DAY = 86_400
OCC = 0.998        # the least completeness of the occupied-slot count in the TSI report's design band


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    g = growth()
    counts = {"blocks, random delay": dict(growth=g), f"blocks, worst {DELTA} s": dict(delta=DELTA),
              "occupied slots, random delay": dict(growth=OCC)}

    rows = []
    for wname, w in WINDOWS.items():
        for a in ALPHAS:
            for cname, kw in counts.items():
                phi = floor_for(w, a, EPS, F, **kw)
                prov = provisional_share(w, phi, EPS)
                rows.append(dict(window=wname, slots=w, alpha=a, count=cname, phi=phi,
                                 expected=w * chain_rate(1.0 - a, F, **kw),
                                 log10_wait_full=log_short(w, phi, 1.0, F, **kw) / math.log(10),
                                 log10_wait_attacked=log_short(w, phi, 1.0 - a, F, **kw) / math.log(10),
                                 provisional_share=prov, provisional_honest=prov - a))
    fl = pd.DataFrame(rows)
    fl.to_csv(OUT / "floor.csv", index=False)

    def phi_of(wname: str, cname: str) -> int:
        r = fl[(fl.window == wname) & (abs(fl.alpha - 1 / 3) < 1e-9) & (fl["count"] == cname)]
        return int(r.phi.iloc[0])

    prot = []
    for wname, w in WINDOWS.items():
        for cname in (f"blocks, worst {DELTA} s", "occupied slots, random delay"):
            phi = phi_of(wname, cname)
            for s in SIGMAS:
                mean, early = blocks_time(phi + 1, s, EPS)
                prot.append(dict(window=wname, floor_from=cname, phi=phi, sigma=s,
                                 mean_days=max(w, mean) / DAY, early_days=max(w, early) / DAY))
    pd.DataFrame(prot).to_csv(OUT / "protection.csv", index=False)

    stall = []
    for wname, w in WINDOWS.items():
        phi = phi_of(wname, f"blocks, worst {DELTA} s")
        r_blocks = resume_share(w, phi, EPS, F, growth=g)
        r_occ = resume_share(w, phi, EPS, F, growth=OCC)
        for r in FALLS:
            stall.append(dict(window=wname, phi=phi, r=r, r_star_blocks=r_blocks, r_star_occupied=r_occ,
                              depth_blocks_days=depth_finality(r, phi, None, EPOCH, PERIOD, w, F, growth=g) / DAY,
                              depth_occupied_days=depth_finality(r, phi, None, EPOCH, PERIOD, w, F, growth=OCC) / DAY))
    pd.DataFrame(stall).to_csv(OUT / "stall.csv", index=False)

    q = []
    for a in (0.20, 0.25, 0.30, 1 / 3):
        for cname, kw in (("blocks, the side at one block per occupied slot", dict(live_growth=g, side_growth=1.0)),
                          ("occupied slots, both", dict(live_growth=OCC, side_growth=1.0))):
            w = least_quorum_window(a, EPS, F, **kw)
            q.append(dict(alpha=a, count=cname, least_slots=w if w is not None else -1,
                          least_days=w / DAY if w is not None else math.nan,
                          phi_at_least=quorum(w, a, EPS, F, **kw)[0] if w is not None else -1,
                          live_rate=chain_rate(1.0 - a, F, growth=kw["live_growth"]),
                          side_rate=chain_rate((1.0 + a) / 2, F, growth=kw["side_growth"])))
    pd.DataFrame(q).to_csv(OUT / "quorum.csv", index=False)

    with pd.option_context("display.max_rows", 200, "display.width", 220):
        for name in ("floor", "protection", "stall", "quorum"):
            print(pd.read_csv(OUT / f"{name}.csv").round(4).to_string(index=False), end="\n\n")


if __name__ == "__main__":
    main()
