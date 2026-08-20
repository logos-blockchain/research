"""The Phase D scenario matrix, as one reproducible run.

Prints the numbers the report cites; `plots.py` renders the same runs. Keeping the matrix in
one module means the report's tables, the figures, and the gates all read the same code path.
"""
from __future__ import annotations

import numpy as np

from . import arrivals, engine, power, scenarios
from .params import Triple


def hashrate_draw(cfg, seed: int = 2):
    """The default field: a Pareto spread floored at a whole Pi 5 board.

    The board basis (all four cores) rather than one core, which is what
    `empowering_sim.elevation` has always used -- the two simulators disagreed by a factor of
    four until this was fixed, in studies whose numbers are compared with each other. See
    `power.py` for the bracket this sits inside and for why the Pareto shape is indicative
    rather than measured.
    """
    return arrivals.pi5_pareto(np.random.default_rng(seed), power.board(cfg).candidates_per_second)


def arrival_shapes(epochs: int = 220, per_epoch: int = 130) -> dict[str, np.ndarray]:
    total = epochs * per_epoch
    return {
        "uniform": arrivals.uniform(epochs, per_epoch),
        "spike x10": arrivals.spike(epochs, per_epoch, at=30, factor=10),
        "spike x100": arrivals.spike(epochs, per_epoch, at=30, factor=100),
        "front-loaded": arrivals.front_loaded(epochs, total),
        "back-loaded": arrivals.back_loaded(epochs, total),
    }


def run_shapes(d, epochs: int = 220, per_epoch: int = 130, horizon: int = 360):
    """Arrivals land inside ``epochs``; the engine runs to ``horizon`` so the late shapes
    (back-loaded especially) get room to convert before the comparison is read."""
    return {name: engine.run(d, a, hashrate_draw(d.cfg), epochs=horizon)
            for name, a in arrival_shapes(epochs, per_epoch).items()}


def cohort_table(result, cohorts) -> list[dict]:
    pop = result.pop
    out = []
    for e in cohorts:
        m = pop.arrived == e
        got = pop.bonded_at[m]
        ok = got != engine.NOT_SET
        out.append(dict(
            cohort=e, n=int(m.sum()), bonded=int(ok.sum()),
            bonded_frac=float(ok.mean()) if m.any() else 0.0,
            median_epochs_to_bond=float(np.median(got[ok] - e)) if ok.any() else float("nan"),
        ))
    return out


def main() -> int:
    d = Triple().derived().check()
    cfg = d.cfg

    print("=== arrival shapes: the same field, differently timed ===")
    runs = run_shapes(d)
    for name, r in runs.items():
        rows = r.rows
        sat30 = rows[30].saturation_block
        print(f"  {name:<13} bonds {rows[-1].bonds_total:>6,}  transition {r.transition_epoch:>3}"
              f"  fullest block {max(q.max_block_claims for q in rows):>5}"
              f"  sat@30 {sat30 if sat30 >= 0 else '-':>6}")

    print("\n=== the x100 cohort, close up (R5) ===")
    for row in cohort_table(runs["spike x100"], (28, 29, 30, 31, 32)):
        print(f"  cohort {row['cohort']}: n={row['n']:>6,}  bonded {row['bonded']:>6,}"
              f" ({row['bonded_frac']:.1%})  median epochs-to-bond"
              f" {row['median_epochs_to_bond']:.0f}")

    print("\n=== the whale (MODEL 8.2) ===")
    for mult in (1.0, 10.0):
        r = scenarios.whale_run(d, 130, whale_epoch=30, whale_multiple=mult, epochs=220)
        whale_bal = int(r.pop.balance.max())
        print(f"  whale {mult:>4}x the field: transition {r.transition_epoch:>3}"
              f"  bonds {r.rows[-1].bonds_total:>6,}"
              f"  whale holds {whale_bal / d.endowment_genesis:.1%} of the endowment")

    print("\n=== the oscillation probe (MODEL 8.1) ===")
    for eta in (0.5, 2.0, 8.0):
        r = scenarios.elastic_run(d, 130, epochs=120,
                                  threshold_lepta=2_000_000_000, eta=eta)
        amp = scenarios.amplitude(r.rows, 40, 110)
        print(f"  eta={eta:>4}: relative amplitude {amp:.3f}")

    print("\n=== the sparse post-phase (MODEL 8.4) ===")
    rs = engine.run(d, arrivals.uniform(240, 130), hashrate_draw(cfg), epochs=240,
                    txs_per_block=20)
    post = [q for q in rs.rows if not q.bootstrap][3:]
    cap = cfg.pow_share_num * 20 * cfg.blocks_per_epoch // (cfg.pow_share_den * 2)
    if post:
        sats = [q.saturation_block for q in post if q.saturation_block >= 0]
        line = (f"  capacity {cap:,}/epoch = {cap / cfg.blocks_per_epoch:.2f}/block"
                f"  claims {post[5].claims_paid:,}")
        line += (f"  median saturation {np.median(sats):,.0f} of {cfg.blocks_per_epoch:,}"
                 if sats else "  never saturated in horizon")
        print(line)
    else:
        print(f"  no post epochs in horizon (transition {rs.transition_epoch})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
