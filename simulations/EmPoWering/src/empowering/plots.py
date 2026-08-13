"""Validation plots for the specified parameter set.

The text sections say what the numbers are; these say whether they behave. Each figure
answers one question a reviewer would actually ask of the specification, and each is
rendered from the same `Params` the analyses use, so a config edit moves the plots too.

matplotlib is an optional extra (`pip install -e '.[plots]'`) — the analysis package
itself stays stdlib-only, so nothing here is on the path of `make verify` or `make check`.

Palette: Okabe-Ito, the colourblind-safe qualitative set, assigned in fixed order and
never cycled; the same theme the blend simulator uses, so figures across the research
tree read as one set.
"""
from __future__ import annotations

from pathlib import Path

from . import core
from .params import P_FIELD, Params

OKABE_ITO = ["#0072B2", "#D55E00", "#009E73", "#CC79A7",
             "#E69F00", "#56B4E9", "#F0E442", "#000000"]
INK, MUTED = "#222222", "#666666"


def _style():
    import matplotlib as mpl

    mpl.rcParams.update({
        "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight",
        "font.size": 10, "font.family": "sans-serif",
        "axes.titlesize": 11, "axes.labelsize": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
        "legend.frameon": False, "legend.fontsize": 8.5,
        "lines.linewidth": 1.8, "mathtext.default": "regular",
        "axes.prop_cycle": mpl.cycler(color=OKABE_ITO),
        "text.color": INK, "axes.labelcolor": INK,
        "xtick.color": MUTED, "ytick.color": MUTED,
    })


def _save(fig, out: Path, stem: str, provenance: str) -> Path:
    out.mkdir(parents=True, exist_ok=True)
    fig.text(0.99, 0.005, provenance, fontsize=6, alpha=0.5, va="bottom", ha="right")
    path = out / f"{stem}.png"
    fig.savefig(path)
    import matplotlib.pyplot as plt
    plt.close(fig)
    return path


def pool_trajectory(p: Params, out: Path, horizon_years: float = 40.0) -> Path:
    """The pool from genesis to its fixed point, and what the reward does on the way.

    The question this answers: the endowment is five orders of magnitude above the fixed
    point, so does the reward ever fall through the floor on the way down? It does not --
    but the descent takes decades, which is the part the steady-state figure hides.
    """
    import matplotlib.pyplot as plt
    _style()
    import math

    epochs = int(horizon_years * p.epochs_per_year)
    rows = core.simulate_pool(p, epochs=epochs)
    yrs = [r["years"] for r in rows]
    R_star, R_floor = core.r_star(p), core.r_min(p)
    # epochs for the gap to R* to close to a factor of two
    e_half = math.log((p.R0 - R_star) / R_star) / -math.log(1 - p.rho)

    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(7.2, 6.4), sharex=True)
    ax.plot(yrs, [r["pool"] for r in rows], color=OKABE_ITO[0], label="pool $R_e$")
    ax.axhline(R_star, color=OKABE_ITO[2], ls="--", lw=1.4,
               label=f"fixed point $R^*$ = {R_star:,.0f} LGO")
    ax.axhline(R_floor, color=OKABE_ITO[1], ls=":", lw=1.4,
               label=f"floor $R_{{min}}$ = {R_floor:,.0f} LGO")
    ax.axvline(e_half / p.epochs_per_year, color=MUTED, lw=1.0, ls="-.")
    ax.annotate(f"within 2x of $R^*$\nafter {e_half / p.epochs_per_year:.0f} years",
                xy=(e_half / p.epochs_per_year, R_star * 30), fontsize=8,
                color=MUTED, ha="right", xytext=(-6, 0), textcoords="offset points")
    ax.set(yscale="log", ylabel="reward pool (LGO)",
           title="The pool spends decades on its genesis endowment, not on fee refill")
    ax.legend(loc="upper right")

    so = [r["sigma_over_phi"] for r in rows]
    ax2.plot(yrs, so, color=OKABE_ITO[0], label=r"reward per claim $\sigma_e/\varphi$")
    ax2.axhline(core.sigma_over_phi(p), color=OKABE_ITO[2], ls="--", lw=1.4,
                label=f"steady state = {core.sigma_over_phi(p):.2f}")
    ax2.axhline(1.0, color=OKABE_ITO[1], ls=":", lw=1.4,
                label=r"break-even ($\sigma_e = \varphi$)")
    ax2.set(yscale="log", xlabel="years from genesis",
            ylabel=r"$\sigma_e\,/\,\varphi$",
            title=f"Reward per claim falls {so[0] / so[-1]:,.0f}x over "
                  f"{horizon_years:.0f} years, never through the floor")
    ax2.legend(loc="upper right")
    fig.tight_layout()
    return _save(fig, out, "01_pool_trajectory", f"empowering · {p.name}")


def claim_share_vs_traffic(p: Params, out: Path) -> Path:
    """Assumption A10, re-read against traffic instead of capacity.

    A10 checks the claim load against MAX_BLOCK_TXS and finds 1%. That is the right test
    for whether claims *fit*. The test for whether they *pay* is against actual traffic,
    and it has a ceiling: v <= psi*beta, or the claim earns less than it costs.
    """
    import matplotlib.pyplot as plt
    _style()

    ns = [n for n in range(5, p.max_block_txs + 1)]
    v = [100.0 * p.T / n for n in ns]
    ceiling = 100.0 * p.psi * p.beta
    n_min = p.T / (p.psi * p.beta)

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.plot(ns, v, color=OKABE_ITO[0], label="claim share of transactions, $T/n_{tx}$")
    ax.axhline(ceiling, color=OKABE_ITO[1], ls="--", lw=1.4,
               label=fr"ceiling $\psi\beta$ = {ceiling:.1f}% (claim pays its own fee)")
    ax.fill_between(ns, ceiling, 100.0, color=OKABE_ITO[1], alpha=0.08)
    ax.annotate("claims cost more than they earn;\nthe endowment covers the difference",
                xy=(300, ceiling * 2.2), fontsize=8.5, color=MUTED)

    for n, label, colour in ((20, "ramp start", OKABE_ITO[3]),
                             (int(n_min), "break-even", OKABE_ITO[1]),
                             (p.n_tx_ref, "reference", OKABE_ITO[2]),
                             (p.max_block_txs, "capacity (A10)", OKABE_ITO[4])):
        if n < ns[0]:
            continue
        y = 100.0 * p.T / n
        ax.plot([n], [y], "o", ms=7, color=colour, zorder=5)
        ax.annotate(f"{label}\n{n:,} tx/blk · {y:.1f}%", xy=(n, y), xytext=(6, 8),
                    textcoords="offset points", fontsize=8, color=colour)

    ax.set(xscale="log", yscale="log", xlabel="transactions per block $n_{tx}$",
           ylabel="claims as % of block transactions",
           title="A10 against capacity says 1%; against traffic the binding number "
                 f"is {ceiling:.1f}%")
    ax.legend(loc="lower left")
    fig.tight_layout()
    return _save(fig, out, "02_claim_share_vs_traffic", f"empowering · {p.name}")


def beta_relation(p: Params, out: Path) -> Path:
    """What beta_PoW actually buys, given the claim count is fixed by the controller.

    Raising beta does not put more claims in a block -- the difficulty controller holds
    that at T. It moves the traffic floor below which mining stops paying for itself.
    """
    import matplotlib.pyplot as plt
    from dataclasses import replace
    _style()

    betas = [n / p.beta_den for n in range(1, 34)]
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.4))

    n_min = [p.T / (p.psi * b) for b in betas]
    ax.plot([100 * b for b in betas], n_min, color=OKABE_ITO[0],
            label=r"break-even traffic $T/(\psi\beta)$")
    ax.axhline(p.n_tx_ref, color=OKABE_ITO[2], ls="--", lw=1.4,
               label=f"reference traffic = {p.n_tx_ref}")
    ax.axhline(p.max_block_txs, color=OKABE_ITO[4], ls=":", lw=1.4,
               label=f"capacity = {p.max_block_txs}")
    ax.plot([100 * p.beta], [p.T / (p.psi * p.beta)], "o", ms=8,
            color=OKABE_ITO[1], zorder=5)
    ax.annotate(f"specified\n$\\beta$ = {p.beta:.0%} · {p.T / (p.psi * p.beta):,.0f} tx/blk",
                xy=(100 * p.beta, p.T / (p.psi * p.beta)), xytext=(10, 14),
                textcoords="offset points", fontsize=8.5, color=OKABE_ITO[1])
    ax.set(yscale="log", xlabel=r"$\beta_{PoW}$  (% of fees to the pool)",
           ylabel="transactions per block needed to break even",
           title="What $\\beta$ buys: traffic headroom, not claim volume")
    ax.legend(loc="upper right")

    for i, n in enumerate((100, 300, p.n_tx_ref, p.max_block_txs)):
        r = [core.sigma_over_phi(replace(p, beta_num=int(round(b * p.beta_den))), n)
             for b in betas]
        ax2.plot([100 * b for b in betas], r, color=OKABE_ITO[i],
                 label=f"{n:,} tx/block")
    ax2.axhline(1.0, color=MUTED, ls=":", lw=1.4, label="break-even")
    ax2.axvline(100 * p.beta, color=OKABE_ITO[1], lw=1.0, ls="-.")
    ax2.annotate(f"specified {p.beta:.0%}", xy=(100 * p.beta, 30), fontsize=8.5,
                 color=OKABE_ITO[1], rotation=90, ha="right", va="top")
    ax2.set(yscale="log", xlabel=r"$\beta_{PoW}$  (% of fees to the pool)",
            ylabel=r"$\sigma^*/\varphi$   (steady-state reward over the fee)",
            title=r"$\sigma^*/\varphi = \psi\beta\,n_{tx}/T$  —  proportional to $\beta$"
                  "\n(log axis, so proportionality reads as a shift, not a straight line)")
    ax2.legend(loc="lower right", title="traffic", title_fontsize=8)
    fig.tight_layout()
    return _save(fig, out, "03_beta_relation", f"empowering · {p.name}")


def endowment_ramp(p: Params, out: Path) -> Path:
    """Does the specified endowment carry an adoption ramp? By a wide margin."""
    import matplotlib.pyplot as plt
    _style()

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.4))
    ratio = None
    for i, years in enumerate((1, 2, 5, 10)):
        R_min0 = core.min_endowment_for_ramp(p, float(years))
        rows = core.ramp_trajectory(p, R_min0, float(years))
        ax.plot([r["years"] for r in rows], [r["n_tx"] for r in rows],
                color=OKABE_ITO[i], label=f"{years}-year ramp")
        # At the SPECIFIED R0 all four curves lie on top of each other -- the endowment so
        # dominates the refill that the ramp shape is invisible. Plotting each at its own
        # minimum endowment is what makes the test legible: every ramp then grazes the floor.
        ax2.plot([r["years"] for r in rows], [r["sigma_over_phi"] for r in rows],
                 color=OKABE_ITO[i], label=f"{years}-year ramp")
        if years == 5:
            ratio = p.R0 / R_min0
    ax.axhline(p.n_tx_ref, color=MUTED, ls=":", lw=1.2,
               label=f"reference = {p.n_tx_ref}")
    ax.set(xlabel="years from genesis", ylabel="transactions per block",
           title="Traffic ramps modelled for the endowment test")
    ax.legend(loc="lower right")

    ax2.axhline(1.0, color=OKABE_ITO[1], ls="--", lw=1.4, label="break-even")
    ax2.set(yscale="log", xlabel="years from genesis",
            ylabel=r"$\sigma_e\,/\,\varphi$",
            title="Each ramp at its own minimum endowment: all graze the floor\n"
                  f"(the specified $R_0$ is {ratio:,.0f}x the 5-year minimum)")
    ax2.legend(loc="upper right")
    fig.tight_layout()
    return _save(fig, out, "04_endowment_ramp", f"empowering · {p.name}")


def reward_controller(p: Params, out: Path) -> Path:
    """The memoryless retarget recovering from a mis-set genesis difficulty."""
    import matplotlib.pyplot as plt
    _style()

    d_eq = P_FIELD >> p.reward_difficulty_exp
    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for i, (mult, label) in enumerate(((100, "100x too permissive"),
                                       (10, "10x too permissive"),
                                       (0.1, "10x too hard"),
                                       (0.01, "100x too hard"))):
        d, series, conv = int(d_eq * mult), [], None
        for n in range(80):
            c = min(max(0, round(p.T * d / d_eq)), p.max_block_txs)
            series.append(c)
            if conv is None and abs(c - p.T) <= 0.1 * p.T:
                conv = n
            d = core.next_reward_difficulty(d, c, p)
        ax.plot(range(len(series)), series, color=OKABE_ITO[i], marker="o", ms=3.0,
                label=f"{label} — {conv} blocks")
    ax.axhline(p.T, color=MUTED, ls="--", lw=1.4, label=f"target T = {p.T}")
    # symlog, not log: a too-hard genesis produces blocks with zero claims, and a log axis
    # would silently drop them rather than show the stall they represent.
    ax.set_yscale("symlog", linthresh=1)
    ax.set_ylim(bottom=0)          # claims per block is non-negative; symlog would show -10^1
    ax.set(xlabel="blocks from genesis", ylabel="claims per block",
           title="Recovery is asymmetric: fast when too permissive, slow when too hard")
    ax.legend(loc="upper right")
    fig.tight_layout()
    return _save(fig, out, "05_reward_controller", f"empowering · {p.name}")


ALL = {"pool": pool_trajectory, "share": claim_share_vs_traffic, "beta": beta_relation,
       "ramp": endowment_ramp, "controller": reward_controller}


def main(argv: list[str] | None = None) -> int:
    import argparse

    from . import params

    ap = argparse.ArgumentParser(description="render the EmPoWering validation figures")
    ap.add_argument("--config", default="configs/specified.toml")
    ap.add_argument("--out", default="figures")
    ap.add_argument("which", nargs="?", choices=sorted(ALL), help="one figure (default: all)")
    a = ap.parse_args(argv)
    p = params.load(a.config)
    out = Path(a.out)
    todo = {a.which: ALL[a.which]} if a.which else ALL
    for name, fn in todo.items():
        print(f"  {fn(p, out)}")
    return 0



# --- region maps: where the parameter set works, and where it stops working ----------------
# Region fills are a status encoding, not a categorical one: one tint per verdict, ordered
# fail -> marginal -> works, with the boundary drawn in full strength and each region named
# in place. No rainbow, and no reliance on colour alone.
FAIL, MARGINAL, WORKS = "#F7D5C4", "#FBEAC8", "#CDE8DE"


def operating_envelope(p: Params, out: Path) -> Path:
    """Where mining funds itself, over the two axes that decide it: traffic and beta.

    Two independent walls, and the specified point sits between them:
      * below   sigma*/phi = psi*beta*n/T < 1 -- a claim earns less than it costs;
      * above   beta past the subordination cap -- mining stops being the junior path.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.colors import ListedColormap
    _style()

    n = np.linspace(20, p.max_block_txs, 400)
    b = np.linspace(0.005, 0.33, 400)
    N, B = np.meshgrid(n, b)
    ratio = p.psi * B * N / p.T                       # sigma*/phi
    cap = 0.4 / (3.0 + 0.4)                           # beta where PoW = 1/3 of the leader share

    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    ax.contourf(N, 100 * B, ratio, levels=[0, 1, 2, 1e9],
                colors=[FAIL, MARGINAL, WORKS])
    ax.contour(N, 100 * B, ratio, levels=[1, 2], colors=[OKABE_ITO[1], OKABE_ITO[2]],
               linewidths=1.6, linestyles=["--", "-"])
    ax.axhspan(100 * cap, 33, color=FAIL, alpha=0.85, zorder=2)
    ax.axhline(100 * cap, color=OKABE_ITO[3], lw=1.6, zorder=3)

    ax.annotate("mining is no longer the junior path\n"
                fr"($\beta$ > {100 * cap:.1f}%: PoW exceeds a third of the leader share)",
                xy=(540, 100 * cap + 5.6), fontsize=8.5, color="#7A4B63", zorder=4)
    ax.annotate("a claim earns less\nthan its own fee\n" r"($\sigma^*<\varphi$)",
                xy=(70, 1.6), fontsize=8.5, color="#8A4B2A", zorder=4)
    ax.annotate("thin: between one and\ntwo times the fee", xy=(120, 5.4), fontsize=8.5,
                color="#8A6A2A", zorder=4)
    ax.annotate("works", xy=(700, 7.2), fontsize=11, color="#2A6A55", zorder=4, weight="bold")

    ax.plot([p.n_tx_ref], [100 * p.beta], "o", ms=10, color=OKABE_ITO[7], zorder=6)
    ax.annotate(f"specified\n{p.n_tx_ref} tx/blk, $\\beta$ = {p.beta:.0%}\n"
                fr"$\sigma^*/\varphi$ = {core.sigma_over_phi(p):.2f}",
                xy=(p.n_tx_ref, 100 * p.beta), xytext=(-108, -52),
                textcoords="offset points", fontsize=8.5, color=OKABE_ITO[7], zorder=6,
                arrowprops=dict(arrowstyle="->", color=OKABE_ITO[7], lw=1.2))

    ax.set(xlabel="transactions per block $n_{tx}$",
           ylabel=r"$\beta_{PoW}$  (% of fees to the pool)", ylim=(0.5, 33),
           title="Operating envelope: the corridor between self-funding and subordination")
    fig.tight_layout()
    return _save(fig, out, "06_operating_envelope", f"empowering · {p.name}")


def drain_margin(p: Params, out: Path) -> Path:
    """Where the pool can be emptied inside one epoch: T/rho against MAX_BLOCK_TXS.

    Draining within an epoch needs T/rho claims in every block for the whole epoch. When
    that exceeds MAX_BLOCK_TXS it is impossible by construction; below it, only the
    difficulty controller stands in the way. The specified point is on the reachable side.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    _style()

    T = np.linspace(1, 100, 500)
    rho_den = np.linspace(20, 500, 500)
    TT, DD = np.meshgrid(T, rho_den)
    need = TT * DD                                    # T / rho = T * rho_den

    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    ax.contourf(TT, DD, need, levels=[0, p.max_block_txs, 1e9], colors=[FAIL, WORKS])
    ax.contour(TT, DD, need, levels=[p.max_block_txs], colors=[OKABE_ITO[1]], linewidths=2.0)

    ax.annotate("drain is REACHABLE inside one epoch\n"
                f"(needs $\\leq$ MAX_BLOCK_TXS = {p.max_block_txs} claims/block;\n"
                "only the difficulty controller prevents it)",
                xy=(15, 32), fontsize=8.5, color="#8A4B2A", zorder=4)
    ax.annotate("drain is impossible by construction\n"
                f"(needs > {p.max_block_txs} claims in every block)",
                xy=(30, 330), fontsize=9, color="#2A6A55", zorder=4)

    ax.plot([p.T], [p.rho_den], "o", ms=10, color=OKABE_ITO[7], zorder=6)
    margin = p.max_block_txs / (p.T * p.rho_den)
    ax.annotate(f"specified\nT = {p.T}, $\\rho$ = 1/{p.rho_den}\n"
                f"needs {p.T * p.rho_den:,}/block; cap is {p.max_block_txs}\n"
                f"reachable, by {margin - 1:.1%}",
                xy=(p.T, p.rho_den), xytext=(24, 40), textcoords="offset points",
                fontsize=8.5, color=OKABE_ITO[7], zorder=6,
                arrowprops=dict(arrowstyle="->", color=OKABE_ITO[7], lw=1.2))

    ax.set(xlabel="TARGET_CLAIMS_PER_BLOCK  $T$",
           ylabel=r"$1/\rho$   (epochs of reserve; $\rho$ = 1/this)",
           title="Within-epoch drain: the specified point sits just inside the reachable side")
    fig.tight_layout()
    return _save(fig, out, "07_drain_margin", f"empowering · {p.name}")


def blend_envelope(p: Params, out: Path) -> Path:
    """Which admission thresholds land in the design target, on which reference machine.

    The design target is about a minute of one core per message, of order a thousand
    messages a day. Whether the reference is one core or the whole board is still open
    (report 10.1) and is worth exactly two exponents.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    _style()

    exps = np.arange(15, 27)
    one = 2.0 ** exps * p.sec_per_candidate
    board = one / p.pi5_cores
    opt = 2.0 ** exps * p.sec_per_candidate_opt
    lo, hi = 30.0, 120.0                              # "about a minute", taken as a band

    fig, ax = plt.subplots(figsize=(7.6, 5.0))
    ax.axhspan(lo, hi, color=WORKS, zorder=0)
    ax.axhspan(0.1, lo, color=FAIL, alpha=0.7, zorder=0)
    ax.axhspan(hi, 1e5, color=FAIL, alpha=0.7, zorder=0)
    ax.annotate("design target\n~1 min/message, ~1k msgs/day", xy=(15.2, 52), fontsize=8.5,
                color="#2A6A55", zorder=5)
    ax.annotate("too cheap to be a cost", xy=(15.2, 5), fontsize=8.5, color="#8A4B2A", zorder=5)
    ax.annotate("not an on-ramp", xy=(15.2, 2200), fontsize=8.5, color="#8A4B2A", zorder=5)

    ax.plot(exps, one, "o-", color=OKABE_ITO[0], label="one Pi 5 core (specified basis)")
    ax.plot(exps, board, "s-", color=OKABE_ITO[2], label=f"whole board ({p.pi5_cores} cores)")
    ax.plot(exps, opt, "^--", color=OKABE_ITO[4], lw=1.4,
            label=f"optimising miner, one core ({p.sec_per_candidate / p.sec_per_candidate_opt:.2f}x edge)")

    ax.axvline(p.blend_base_exp, color=OKABE_ITO[7], lw=1.2, ls="-.", zorder=4)
    ax.annotate(f"specified\n$p/2^{{{p.blend_base_exp}}}$", xy=(p.blend_base_exp, 4000),
                fontsize=9, color=OKABE_ITO[7], ha="center", zorder=5)

    ax.set(yscale="log", xlabel="threshold exponent  $k$  in  $p/2^{k}$",
           ylabel="seconds per solution", ylim=(1, 1e4), xlim=(15, 26),
           title="Admission threshold: one-core basis puts the target at $2^{19}$, "
                 "the board at $2^{21}$")
    ax.legend(loc="lower right")
    fig.tight_layout()
    return _save(fig, out, "08_blend_envelope", f"empowering · {p.name}")


ALL.update({"envelope": operating_envelope, "drain": drain_margin, "blendmap": blend_envelope})

if __name__ == "__main__":
    raise SystemExit(main())
