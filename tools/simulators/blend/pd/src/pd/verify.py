"""Analytic sanity checks for pd (pd-verify): closed forms + graph invariants.

Random-placement observation/eclipse have exact closed forms on a random d-regular graph:
    observed_frac ~ 1 - (1 - f_adv)^degree      (an honest node has >=1 adversarial peer)
    eclipsed_frac ~ f_adv^degree                (all `degree` peers adversarial)
and the propagation full delay (mixing off) drops as the peering degree rises. Each check prints
PASS/FAIL; a non-zero exit signals failure.
"""

from __future__ import annotations

import numpy as np

from .adversary import adversary_metrics, deanon_metrics, place_adversary
from .config import SimConfig
from .graph import build_graph
from .rng import placement_seedseq


def _check(name: str, ok: bool, detail: str) -> bool:
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    return ok


def main(argv: list[str] | None = None) -> int:
    ok = True

    # 1. graph exactly d-regular + symmetric
    cfg = SimConfig(n_nodes=2000, degree=8, f_adv=0.0)
    g = build_graph(cfg)
    deg = np.diff(g.indptr)
    regular = bool(np.all(deg == g.degree))
    csr = g.weighted_csr(np.ones_like(g.base))
    symmetric = int((csr != csr.T).nnz) == 0
    ok &= _check("graph d-regular", regular, f"all degrees == {g.degree}: {regular}")
    ok &= _check("graph symmetric", symmetric, f"adj == adj.T: {symmetric}")

    # 2. random observation / eclipse vs closed form (avg over placements + a couple of seeds)
    for degree in (4, 8):
        for f in (0.1, 0.3):
            obs, ecl = [], []
            for seed in range(4):
                gg = build_graph(SimConfig(n_nodes=4000, degree=degree, graph_seed=seed))
                pc = SimConfig(n_nodes=4000, degree=degree, graph_seed=seed, f_adv=f)
                rng = np.random.default_rng(placement_seedseq(pc, f, "random", 0))
                m = adversary_metrics(gg, place_adversary(gg, f, "random", rng, 100_000))
                obs.append(m["observed_frac"])
                ecl.append(m["eclipsed_frac"])
            obs_m, ecl_m = float(np.mean(obs)), float(np.mean(ecl))
            obs_th = 1 - (1 - f) ** degree
            ecl_th = f ** degree
            ok &= _check(f"observed_frac d={degree} f={f}", abs(obs_m - obs_th) < 0.02,
                         f"sim {obs_m:.3f} vs theory {obs_th:.3f}")
            ok &= _check(f"eclipsed_frac d={degree} f={f}",
                         abs(ecl_m - ecl_th) < max(0.01, 0.2 * ecl_th),
                         f"sim {ecl_m:.4f} vs theory {ecl_th:.4f}")

    # 3. propagation full delay decreases as degree rises (mixing off, small jitter)
    from .engine import run_trajectory
    delays = {}
    for degree in (4, 16):
        c = SimConfig(n_nodes=4000, degree=degree, blend_hops=3, max_blend_delay=0,
                      transport_jitter_mean_ms=0.0, n_rounds=40)
        delays[degree] = run_trajectory(c)["propagation"]["full_delay_ms_mean"]
    ok &= _check("delay decreases with degree", delays[16] < delays[4],
                 f"d=4 {delays[4]:.0f} ms > d=16 {delays[16]:.0f} ms")

    # 4. message delivery-rate ~ (1 - u)^blend_hops (relays drawn blind to responsiveness; a high
    #    degree keeps legs routable so the only loss is a relay landing on an unresponsive node)
    for u in (0.1, 0.3):
        rates = []
        for seed in range(3):
            c = SimConfig(n_nodes=5000, degree=16, blend_hops=3, max_blend_delay=0,
                          transport_jitter_mean_ms=0.0, unresponsive_frac=u,
                          n_rounds=400, graph_seed=seed)
            rates.append(run_trajectory(c)["propagation"]["delivery_rate"])
        rate_m = float(np.mean(rates))
        rate_th = (1 - u) ** 3
        ok &= _check(f"delivery_rate u={u}", abs(rate_m - rate_th) < 0.03,
                     f"sim {rate_m:.3f} vs theory {rate_th:.3f}")

    # 5. deanonymization: the exact closed forms reproduce a direct Monte-Carlo of the SAME draw
    #    (honest sender + blend_hops relays picked blind to who is adversarial). deanon_rate ~
    #    f_adv^blend_hops (whole cascade adversarial); full adds the sender-has-an-adversary-peer
    #    factor. degree lifts the full rate (more peers -> sender more exposed), not deanon_rate.
    for degree, f, k in [(8, 0.33, 2), (16, 0.33, 2), (8, 0.33, 3), (16, 0.2, 3)]:
        cfg = SimConfig(n_nodes=3000, degree=degree, graph_seed=2, f_adv=f, blend_hops=k)
        g = build_graph(cfg)
        prng = np.random.default_rng(placement_seedseq(cfg, f, "random", 0))
        mask = place_adversary(g, f, "random", prng, cfg.worstcase_max_n)
        adv = adversary_metrics(g, mask)
        dz = deanon_metrics(g.n, adv["n_adv"], adv["observed_frac"], k)
        counts = np.add.reduceat(mask[g.indices].astype(np.int32), g.indptr[:-1])
        observed_node = counts >= 1
        honest = np.where(~mask)[0]
        n = g.n
        srng = np.random.default_rng(777 + degree + k)
        trials, d_hit, fd_hit = 60_000, 0, 0
        for _ in range(trials):
            s = int(srng.choice(honest))
            r = srng.choice(n - 1, size=k, replace=False)
            r[r >= s] += 1                       # blend_hops distinct nodes, all != sender
            if mask[r].all():
                d_hit += 1
                fd_hit += int(observed_node[s])
        d_emp, fd_emp = d_hit / trials, fd_hit / trials
        ok &= _check(f"deanon_rate d={degree} f={f} k={k}",
                     abs(dz["deanon_rate"] - d_emp) < max(0.006, 0.12 * d_emp),
                     f"closed {dz['deanon_rate']:.4f} vs MC {d_emp:.4f} (~f^k={f ** k:.4f})")
        ok &= _check(f"full_deanon d={degree} f={f} k={k}",
                     abs(dz["full_deanon_rate"] - fd_emp) < max(0.006, 0.15 * fd_emp),
                     f"closed {dz['full_deanon_rate']:.4f} vs MC {fd_emp:.4f}")

    # 6. messaging redundancy R and the linkability laws.
    #    deanon_R = 1-(1-d1)^R (any of R independent cascades whole-path-adversarial); delivery_R =
    #    1-(1-p1)^R (any of R cascades delivers); T_link ~ 30s*ln(1/(1-alpha))/(s*q).
    from .linkability import time_to_link_seconds
    from .propagation import assign_responsive, propagation_metrics
    from .rng import responsive_seedseq, round_seedseq
    f, k, degree = 0.33, 2, 8               # (a) deanon_R vs direct R-cascade Monte-Carlo
    cfg = SimConfig(n_nodes=3000, degree=degree, graph_seed=1, f_adv=f, blend_hops=k)
    g = build_graph(cfg)
    mask = place_adversary(g, f, "random",
                           np.random.default_rng(placement_seedseq(cfg, f, "random", 0)),
                           cfg.worstcase_max_n)
    adv = adversary_metrics(g, mask)
    honest, n = np.where(~mask)[0], g.n
    for R in (2, 3):
        dzR = deanon_metrics(n, adv["n_adv"], adv["observed_frac"], k, R)
        srng = np.random.default_rng(1234 + R)
        trials, hit = 40_000, 0
        for _ in range(trials):
            s = int(srng.choice(honest))
            captured = False
            for _c in range(R):
                r = srng.choice(n - 1, size=k, replace=False)
                r[r >= s] += 1
                if mask[r].all():
                    captured = True
                    break
            hit += int(captured)
        emp = hit / trials
        ok &= _check(f"deanon_rate R={R}", abs(dzR["deanon_rate"] - emp) < max(0.006, 0.1 * emp),
                     f"closed {dzR['deanon_rate']:.4f} vs MC {emp:.4f}")

    u = 0.3                                  # (b) simulated delivery_R vs 1-(1-p1)^R
    dc = SimConfig(n_nodes=5000, degree=16, blend_hops=3, max_blend_delay=0,
                   transport_jitter_mean_ms=0.0, unresponsive_frac=u, n_rounds=1500)
    gg = build_graph(dc)
    resp = assign_responsive(dc.n_nodes, u, np.random.default_rng(responsive_seedseq(dc, u)))
    deliveries = {}
    for R in (1, 2, 3):
        rng = np.random.default_rng(round_seedseq(dc, dc.blend_hops, dc.max_blend_delay, u, R))
        deliveries[R] = propagation_metrics(
            gg, dc.blend_hops, dc.max_blend_delay, u, R, resp, dc, rng)["delivery_rate"]
    for R in (2, 3):
        th = 1 - (1 - deliveries[1]) ** R    # cascades ~independent given the responsive mask
        ok &= _check(f"delivery_rate R={R}", abs(deliveries[R] - th) < 0.04,
                     f"sim {deliveries[R]:.3f} vs 1-(1-p1)^R {th:.3f}")

    s_stake, q = 0.02, 0.05                  # (c) time-to-link geometric law vs emission MC
    first = np.random.default_rng(99).geometric(s_stake * q, size=200_000)
    for alpha in (0.5, 0.9):
        emp = 30.0 * float(np.quantile(first, alpha))
        closed = time_to_link_seconds(s_stake, q, alpha)
        ok &= _check(f"time_to_link alpha={alpha}", abs(emp - closed) / closed < 0.03,
                     f"MC {emp:.0f}s vs closed {closed:.0f}s")

    # 7. churn percolation: the responsive sub-graph is site percolation on a d-regular graph, so
    #    its giant component survives only while the responsive fraction exceeds 1/(degree-1) --
    #    i.e. up to churn u_c = 1 - 1/(degree-1). Check it is giant below u_c and gone above.
    from scipy.sparse import csr_matrix
    from scipy.sparse.csgraph import connected_components
    n_p = 20_000
    for degree in (3, 6):
        u_c = 1.0 - 1.0 / (degree - 1)
        cfg = SimConfig(n_nodes=n_p, degree=degree, graph_seed=0)
        g = build_graph(cfg)
        giant = {}
        for u in (u_c - 0.15, min(u_c + 0.15, 0.99)):
            resp = assign_responsive(n_p, u, np.random.default_rng(responsive_seedseq(cfg, u)))
            keep = resp[g.src] & resp[g.indices]
            m = csr_matrix((np.ones(int(keep.sum())), (g.src[keep], g.indices[keep])),
                           shape=(n_p, n_p))
            _, lab = connected_components(m, directed=False)
            giant[round(u, 3)] = float(np.bincount(lab[resp]).max() / n_p)
        below, above = giant[round(u_c - 0.15, 3)], giant[round(min(u_c + 0.15, 0.99), 3)]
        ok &= _check(f"percolation d={degree} (u_c={u_c:.2f})", below > 0.1 and above < 0.02,
                     f"giant {below:.3f} at u_c-0.15 -> {above:.4f} at u_c+0.15")

    # 8. correlated (regional) churn vs uniform, at an identical number of dead nodes. With most
    #    peers inside the failure domain, losing whole domains leaves the survivors fully connected
    #    -- so every live relay is still routable and delivery equals the live-relay rate -- while
    #    the same number of scattered failures breaks routes and loses delivery below it.
    n_c, nr_c, u_c2 = 4000, 20, 0.5
    cc = SimConfig(n_nodes=n_c, degree=4, n_regions=nr_c, region_locality=0.75, blend_hops=1,
                   max_blend_delay=0, transport_jitter_mean_ms=0.0, unresponsive_frac=u_c2,
                   n_rounds=1500, graph_seed=0)
    gc = build_graph(cc)
    res = {}
    for cm in ("uniform", "regional"):
        mask = assign_responsive(
            n_c, u_c2, np.random.default_rng(responsive_seedseq(cc, u_c2, cm)), cm, nr_c)
        ok &= _check(f"churn mode {cm} kills the same count",
                     int((~mask).sum()) == int(round(u_c2 * n_c)),
                     f"{int((~mask).sum())} dead of {n_c}")
        prng = np.random.default_rng(round_seedseq(cc, 1, 0, u_c2, 1))
        m = propagation_metrics(gc, 1, 0, u_c2, 1, mask, cc, prng)
        res[cm] = m
    ok &= _check("regional churn spares the live network",
                 res["regional"]["frac_reached_live"] > 0.98
                 and res["regional"]["frac_reached_live"] > res["uniform"]["frac_reached_live"],
                 f"live coverage regional {res['regional']['frac_reached_live']:.3f}"
                 f" vs uniform {res['uniform']['frac_reached_live']:.3f}")
    ok &= _check("uniform churn loses more delivery to broken routes",
                 res["regional"]["delivery_rate"] > res["uniform"]["delivery_rate"],
                 f"delivery regional {res['regional']['delivery_rate']:.3f}"
                 f" vs uniform {res['uniform']['delivery_rate']:.3f}")

    print("OK" if ok else "FAILURES PRESENT")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
