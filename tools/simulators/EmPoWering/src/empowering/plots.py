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


# Set by main() so the caption names the config actually used, not an assumed one.
_CONFIG = "configs/specified.toml"


def _save(fig, out: Path, stem: str, p: Params, key: str) -> Path:
    """Save at 300 dpi with a caption saying exactly how to regenerate this figure.

    The caption is built from the dispatch key the CLI accepts, so it cannot name a
    command that does not work: if a figure is renamed or re-registered, the caption
    moves with it.
    """
    out.mkdir(parents=True, exist_ok=True)
    caption = (f"reproduce: cd tools/simulators/EmPoWering && "
               f"python -m empowering.plots --config {_CONFIG} {key}"
               f"   (all figures: make plots)   ·   parameter set: {p.name}")
    fig.text(0.005, 0.005, caption, fontsize=5.8, alpha=0.55, va="bottom", ha="left")
    path = out / f"{stem}.png"
    fig.savefig(path)
    import matplotlib.pyplot as plt
    plt.close(fig)
    return path


def pool_trajectory(p: Params, out: Path, horizon_years: float = 55.0) -> Path:
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
    ax.set(yscale="log", ylabel="reward pool (LGO)", xlim=(0, horizon_years),
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
    return _save(fig, out, "01_pool_trajectory", p, "pool")


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
    return _save(fig, out, "02_claim_share_vs_traffic", p, "share")


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
    return _save(fig, out, "03_beta_relation", p, "beta")


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
    return _save(fig, out, "04_endowment_ramp", p, "ramp")


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
    return _save(fig, out, "05_reward_controller", p, "controller")


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
    global _CONFIG
    _CONFIG = a.config              # so the caption names the config actually rendered
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
    cap = core.subordination_beta_cap(p)              # beta where PoW = 1/3 of the leader share

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
    return _save(fig, out, "06_operating_envelope", p, "envelope")


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
    need = p.T * p.rho_den
    closed = need > p.max_block_txs
    verdict = (f"impossible by construction\n({need:,} > cap {p.max_block_txs})" if closed
               else f"reachable, by {p.max_block_txs / need - 1:.1%}")
    ax.annotate(f"specified\nT = {p.T}, $\\rho$ = 1/{p.rho_den}\n{verdict}",
                xy=(p.T, p.rho_den), xytext=(24, 40), textcoords="offset points",
                fontsize=8.5, color=OKABE_ITO[7], zorder=6,
                arrowprops=dict(arrowstyle="->", color=OKABE_ITO[7], lw=1.2))

    ax.set(xlabel="TARGET_CLAIMS_PER_BLOCK  $T$",
           ylabel=r"$1/\rho$   (epochs of reserve; $\rho$ = 1/this)",
           title="Within-epoch drain: "
                 + ("the specified point is on the impossible side" if closed
                    else "the specified point sits just inside the reachable side"))
    fig.tight_layout()
    return _save(fig, out, "07_drain_margin", p, "drain")


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
    return _save(fig, out, "08_blend_envelope", p, "blendmap")


ALL.update({"envelope": operating_envelope, "drain": drain_margin, "blendmap": blend_envelope})


def sampled_arrivals(p: Params, out: Path) -> Path:
    """A2's Poisson arrivals, run: the per-block spread, and what survives to the epoch.

    Two panels because two scales tell opposite stories. Per block the spread is the 32 %
    A2 names. Per epoch the controller has corrected it, and what is left is three orders
    of magnitude smaller than an uncorrelated Poisson sum would give.
    """
    import matplotlib.pyplot as plt

    from . import sampled as smp
    _style()

    runs = [smp.simulate(p, 3_000 + s, 12) for s in range(4)]
    per_block = [c for r in runs for c in r["per_block"]] if "per_block" in runs[0] else None
    totals = [t for r in runs for t in r["epoch_totals"]]

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.4))
    if per_block is not None:
        lo, hi = 0, max(per_block)
        counts = [per_block.count(k) for k in range(lo, hi + 1)]
        ax.bar(range(lo, hi + 1), counts, color=OKABE_ITO[0], width=0.86,
               label="sampled claims per block")
    ax.axvline(p.T, color=OKABE_ITO[1], ls="--", lw=1.6, label=f"target T = {p.T}")
    mean = sum(r["mean_per_block"] for r in runs) / len(runs)
    ax.axvline(mean, color=OKABE_ITO[2], ls="-", lw=1.6,
               label=f"equilibrium rate {mean:.3f}  (+{mean - p.T:.3f})")
    ax.set(xlabel="claims in a block", ylabel="blocks",
           title=f"Per block: spread {runs[0]['rel_sd']:.0%}, and the rate sits above $T$")
    ax.legend(loc="upper right")

    m = sum(totals) / len(totals)
    ax2.plot(range(len(totals)), totals, "o-", color=OKABE_ITO[0], ms=4,
             label="epoch totals, sampled")
    ax2.axhline(m, color=OKABE_ITO[2], lw=1.4, label=f"mean {m:,.0f}")
    naive = (p.T * p.N_b) ** 0.5
    ax2.fill_between(range(len(totals)), m - naive, m + naive, color=OKABE_ITO[1],
                     alpha=0.18, label=f"±1 sd if arrivals were uncorrelated (±{naive:,.0f})")
    ax2.set(xlabel="epoch", ylabel="claims in the epoch",
            title="Per epoch: the retarget has corrected almost all of it")
    ax2.legend(loc="lower right", fontsize=7.5)
    fig.tight_layout()
    return _save(fig, out, "09_sampled_arrivals", p, "sampled")


ALL["sampled"] = sampled_arrivals


def fee_range(p: Params, out: Path) -> Path:
    """The working fee range on the model's one axis, and what it is in absolute terms.

    Left: the verdict as a function of a block's revenue counted in claim fees. Right: the
    same three thresholds in lepta, against the price level -- the absolute window slides
    with the market, the verdict does not.
    """
    import matplotlib.pyplot as plt
    _style()

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.6))

    loads = [10 * 1.03 ** i for i in range(220)]
    ratio = [core.sigma_over_phi_from_load(p, x) for x in loads]
    be, two = core.min_fee_load(p, 1.0), core.min_fee_load(p, 2.0)
    spec = core.fee_load(p)

    ax.axvspan(loads[0], be, color=FAIL, alpha=0.85)
    ax.axvspan(be, two, color=MARGINAL, alpha=0.85)
    ax.axvspan(two, loads[-1], color=WORKS, alpha=0.85)
    ax.plot(loads, ratio, color=OKABE_ITO[0], lw=2.2, zorder=4,
            label=r"$\sigma^*/\varphi = \beta\hat\Phi/T$")
    ax.axhline(1.0, color=MUTED, ls=":", lw=1.2, zorder=3)
    ax.annotate("under water", xy=(13, 12), fontsize=8.5, color="#8A4B2A", zorder=5)
    ax.annotate("thin", xy=(108, 12), fontsize=8.5, color="#8A6A2A", zorder=5)
    ax.annotate("works", xy=(320, 12), fontsize=11, color="#2A6A55", zorder=5, weight="bold")
    for x, lab in ((be, f"break-even\n$T/\\beta$ = {be:,.0f}"), (spec, f"specified\n{spec:,.0f}"),
                   (p.psi * p.max_block_txs, f"full block\n{p.psi * p.max_block_txs:,.0f}")):
        ax.plot([x], [core.sigma_over_phi_from_load(p, x)], "o", ms=8,
                color=OKABE_ITO[7], zorder=6)
        ax.annotate(lab, xy=(x, core.sigma_over_phi_from_load(p, x)), xytext=(6, -26),
                    textcoords="offset points", fontsize=8, color=OKABE_ITO[7], zorder=6)
    ax.set(xscale="log", yscale="log", xlim=(loads[0], loads[-1]),
           xlabel=r"fee load $\hat\Phi$ = block revenue $\div$ claim fee",
           ylabel=r"$\sigma^*/\varphi$",
           title="One axis: does a block collect $T/\\beta$ claim fees?")
    ax.legend(loc="lower right")

    mults = [10 ** k for k in range(0, 6)]
    prices = [p.price_resting * m for m in mults]
    u = p.base_units_per_lgo
    for i, (load, lab) in enumerate(((be, "break-even"), (two, "2x margin"), (spec, "specified"))):
        ax2.plot(prices, [load * p.claim_fee(pr) * u for pr in prices], "o-",
                 color=OKABE_ITO[i], lw=2, label=lab)
    ax2.set(xscale="log", yscale="log", xlabel="price level (lepta per unit of gas)",
            ylabel="block fee revenue (lepta)",
            title="The absolute window slides with the market;\nthe verdict above does not")
    ax2.legend(loc="upper left")
    ax2.annotate(f"at rest ({p.price_resting}): break-even\nis {be * p.phi * u:,.0f} lepta/block",
                 xy=(p.price_resting, be * p.phi * u), xycoords="data",
                 xytext=(0.42, 0.10), textcoords="axes fraction",
                 fontsize=8, color=MUTED,
                 arrowprops=dict(arrowstyle="->", color=MUTED, lw=1,
                                 connectionstyle="arc3,rad=-0.2"))
    fig.tight_layout()
    return _save(fig, out, "10_fee_range", p, "fees")


ALL["fees"] = fee_range


def t_beta_plane(p: Params, out: Path) -> Path:
    """T and beta are one degree of freedom for the economics, and two for the constraints.

    The margin depends only on T/beta, so it is constant along a ray from the origin. What
    is *not* constant along that ray is the drain margin (which needs T large) and
    subordination (which needs beta small) -- and between them they leave a short window.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    _style()

    T = np.linspace(4, 40, 500)
    B = np.linspace(0.01, 0.25, 500)
    TT, BB = np.meshgrid(T, B)
    ratio = p.psi * BB * p.n_tx_ref / TT
    cap = core.subordination_beta_cap(p)
    t_drain = core.drain_safe_T(p)
    lo, hi = core.iso_margin_window(p)

    fig, ax = plt.subplots(figsize=(8.2, 5.4))
    ok = (ratio >= 2.0) & (BB <= cap) & (TT > t_drain)
    ax.contourf(TT, 100 * BB, ok.astype(float), levels=[0.5, 1.5], colors=[WORKS])
    cs = ax.contour(TT, 100 * BB, ratio, levels=[1, 2, 5.02, 10],
                    colors=[OKABE_ITO[1], OKABE_ITO[4], OKABE_ITO[0], OKABE_ITO[2]],
                    linewidths=1.5)
    ax.clabel(cs, fmt=lambda v: f"$\\sigma^*/\\varphi$ = {v:g}", fontsize=7.5)

    ax.axvline(t_drain, color=OKABE_ITO[3], lw=2)
    ax.annotate(f"drain impossible by construction\nonly right of $T$ = {t_drain:.2f}",
                xy=(t_drain + 0.6, 3.0), fontsize=8, color="#7A4B63")
    ax.axhline(100 * cap, color=OKABE_ITO[1], lw=2, ls="--")
    ax.annotate(f"subordination cap  $\\beta$ = {100 * cap:.2f}%",
                xy=(26, 100 * cap + 0.6), fontsize=8, color="#8A4B2A")

    # the ray on which the economics is unchanged
    ray_T = np.linspace(4, 40, 2)
    ax.plot(ray_T, 100 * ray_T * p.beta / p.T, ":", color=MUTED, lw=1.6,
            label=r"same economics: $T/\beta$ = const")
    ax.plot([lo, hi], [100 * lo * p.beta / p.T, 100 * hi * p.beta / p.T], "-",
            color=OKABE_ITO[7], lw=3.5, solid_capstyle="round", zorder=5,
            label=f"window: $T \\in$ ({lo:.2f}, {hi:.2f}]")

    ax.plot([p.T], [100 * p.beta], "o", ms=11, color=OKABE_ITO[7], zorder=6)
    drain_note = ("drain closed" if p.T * p.rho_den > p.max_block_txs else "drain reachable")
    ax.annotate(f"specified\n$T$ = {p.T}, $\\beta$ = {p.beta:.0%}\n({drain_note})",
                xy=(p.T, 100 * p.beta), xytext=(-104, -46), textcoords="offset points",
                fontsize=8.5, color=OKABE_ITO[7], zorder=6,
                arrowprops=dict(arrowstyle="->", color=OKABE_ITO[7], lw=1.2))
    ints = [t for t in range(int(lo) + 1, int(hi) + 1)]
    if ints:
        t = ints[0]
        ax.plot([t], [100 * t * p.beta / p.T], "*", ms=18, color=OKABE_ITO[2], zorder=7)
        ax.annotate(f"$T$ = {t}, $\\beta$ = {t * p.beta / p.T:.0%}\nsame economics,\n"
                    "drain closed", xy=(t, 100 * t * p.beta / p.T), xytext=(20, -30),
                    textcoords="offset points", fontsize=8.5, color="#2A6A55", zorder=7)

    ax.set(xlabel="TARGET_CLAIMS_PER_BLOCK  $T$",
           ylabel=r"$\beta_{PoW}$  (% of fees to the pool)", ylim=(1, 25),
           title="$T$ and $\\beta$ are one degree of freedom for the economics,\n"
                 "two for the constraints — and the window between them is short")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    return _save(fig, out, "11_T_beta_plane", p, "plane")


ALL["plane"] = t_beta_plane


def funding_flows(p: Params, out: Path, horizon_years: float = 55.0) -> Path:
    """Where the distribution comes from, and how it compares with what leaders earn.

    Left: each epoch's payout split into the part fees refill and the part drawn down from
    the endowment -- the fee-funded fraction crosses one half only when the pool nears R*.
    Right: the same payout against leader income, fee and minted separately. This is the
    flow picture behind section 4.4.2's caveat: the fee-share subordination cap describes
    the mature network, and launch-era proportionality rests on minted block rewards.
    """
    import matplotlib.pyplot as plt
    _style()

    rows = core.simulate_pool(p, epochs=int(horizon_years * p.epochs_per_year))
    yrs = [r["years"] for r in rows]
    F = core.epoch_refill(p)
    dist = [p.T * p.N_b * r["sigma"] if r["enabled"] else 0.0 for r in rows]
    from_endow = [max(d - F, 0.0) for d in dist]
    leader_fees = p.leader_fee_share * (1 - p.beta) * p.N_b * p.n_tx_ref * p.transfer_fee()
    leader_mint = p.r_max * p.N_b

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.4))
    ax.stackplot(yrs, [min(d, F) for d in dist], from_endow,
                 colors=[OKABE_ITO[2], OKABE_ITO[0]], labels=["refilled by fees", "drawn from the endowment"])
    ax.set(yscale="log", ylim=(1, dist[0] * 2), xlabel="years from genesis",
           ylabel="distributed per epoch (LGO)",
           title="What funds the payout: endowment first, fees eventually")
    ax.legend(loc="upper right", fontsize=8)

    ax2.plot(yrs, dist, color=OKABE_ITO[0], lw=2, label="PoW distribution")
    ax2.axhline(leader_mint, color=OKABE_ITO[4], ls="--", lw=1.6,
                label=f"leader minted income (emission cap) = {leader_mint:,.0f}")
    ax2.axhline(leader_fees, color=OKABE_ITO[2], ls="-", lw=1.6,
                label=f"leader fee income = {leader_fees:,.1f}")
    ax2.axhline(leader_fees * p.subordination_ratio, color=OKABE_ITO[1], ls=":", lw=1.4,
                label="one third of leader fee income")
    ax2.set(yscale="log", ylim=(1, max(dist[0], leader_mint) * 3),
            xlabel="years from genesis", ylabel="LGO per epoch",
            title="PoW flow vs leader income: fees vs minted")
    ax2.legend(loc="upper right", fontsize=7.5)
    fig.tight_layout()
    return _save(fig, out, "12_funding_flows", p, "flows")


def adversary_over_time(p: Params, out: Path, horizon_years: float = 55.0) -> Path:
    """Section 4.1's answer as a trajectory rather than a single peak number.

    The share rises while the endowment drains, then flattens once the refill (tiny against
    the stake base) is all that is left -- which is why the 'peak' is a horizon figure and
    the fixed-D0 asymptote is centuries away, exactly as 4.1 says.
    """
    import matplotlib.pyplot as plt
    _style()

    rows = core.simulate_pool(p, epochs=int(horizon_years * p.epochs_per_year))
    h = p.adversary_h
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    for i, d0 in enumerate((0.005, 0.05, 0.30)):
        adv = pend_a = honest = pend_h = 0.0
        series = []
        for r in rows:
            adv += pend_a; honest += pend_h
            d = p.T * p.N_b * r["sigma"] if r["enabled"] else 0.0
            pend_a, pend_h = d * h, d * (1 - h)
            tot = d0 * p.S_tge + adv + honest
            series.append(adv / tot if tot else 0.0)
        ax.plot([r["years"] for r in rows], [100 * v for v in series], color=OKABE_ITO[i],
                lw=2, label=f"$D_0$ = {d0:.1%} of supply staked")
    ax.axhline(100 / 3, color=OKABE_ITO[1], ls="--", lw=1.4, label="one third")
    ax.axhline(100 * core.adversary_asymptote(h, 1.0), color=MUTED, ls=":", lw=1.2,
               label=f"fixed-$D_0$ asymptote {core.adversary_asymptote(h, 1.0):.0%} (artefact)")
    ax.set(xlabel="years from genesis", ylabel="adversary share of total stake (%)",
           title=f"Adversary at h = {h:.0%}: rises with the endowment, then flattens")
    ax.legend(loc="center right", bbox_to_anchor=(0.98, 0.42), fontsize=8)
    fig.tight_layout()
    return _save(fig, out, "13_adversary_over_time", p, "advtime")


def retarget_map(p: Params, out: Path) -> Path:
    """Section 3.6's stability argument as a picture: the retarget's return map.

    One stable fixed point at T (slope F/P < 1), a repelling one at zero (slope P/F > 1),
    no way to oscillate -- the cobwebs from either side walk monotonically home.
    """
    import matplotlib.pyplot as plt
    import numpy as np
    _style()

    g = lambda x: p.T * p.P_ema * x / np.maximum(1e-12, (p.P_ema - p.F_ema) * x + p.F_ema * p.T)
    hi = 3 * p.T
    xs = np.linspace(0.0, hi, 600)
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    ax.plot(xs, g(xs), color=OKABE_ITO[0], lw=2.2, label=r"$g(\lambda)$: next-block rate")
    ax.plot(xs, xs, color=MUTED, lw=1.2, ls="--", label="identity")
    for x0, col in ((2.6 * p.T, OKABE_ITO[1]), (0.05 * p.T, OKABE_ITO[2])):
        x = x0
        for _ in range(30):
            y = float(g(np.array([x]))[0])
            ax.plot([x, x], [x, y], color=col, lw=1.0, alpha=0.8)
            ax.plot([x, y], [y, y], color=col, lw=1.0, alpha=0.8)
            x = y
        ax.plot([x0], [x0], "o", ms=6, color=col, label=f"cobweb from λ = {x0:g}")
    ax.plot([p.T], [p.T], "o", ms=9, color=OKABE_ITO[7], zorder=6)
    ax.annotate(f"stable fixed point λ = T = {p.T}\nslope F/P = {p.F_ema / p.P_ema:.2f} < 1",
                xy=(p.T, p.T), xytext=(12, -38), textcoords="offset points", fontsize=8.5)
    ax.annotate(f"repelling at 0: slope P/F = {p.P_ema / p.F_ema:.2f} > 1\n"
                "(the no-claims state pushes away)", xy=(0, 0),
                xytext=(10, 46), textcoords="offset points", fontsize=8.5, color=MUTED)
    ax.set(xlim=(0, hi), ylim=(0, hi),
           xlabel=r"claims per block $\lambda_n$", ylabel=r"$\lambda_{n+1}$",
           title="The memoryless retarget: one stable point, no oscillation")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    return _save(fig, out, "14_retarget_map", p, "map")


ALL.update({"flows": funding_flows, "advtime": adversary_over_time, "map": retarget_map})

if __name__ == "__main__":
    raise SystemExit(main())
