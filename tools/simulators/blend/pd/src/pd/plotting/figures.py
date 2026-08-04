"""Figure builders for pd. Each takes (prop_df, adv_df) and returns a Figure or None.

Propagation full delay (ms) vs peering degree / blend-path length / network size, and adversary
observation + eclipse fractions vs adversary fraction / degree (with the worst-case envelope) plus
heatmaps. Slices default to the largest N and a representative setting.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..linkability import capture_prob, time_to_link_seconds, time_to_stake_seconds
from . import style

_MS = "full propagation delay (ms)"
_DAY = 86400.0


def _prov(*dfs: pd.DataFrame) -> str:
    ns, seeds = set(), set()
    for df in dfs:
        if df is not None and len(df):
            ns |= set(df["n_nodes"].unique())
            seeds |= set(df["graph_seed"].unique())
    return f"pd  |  N={sorted(int(x) for x in ns)}  seeds={len(seeds)}"


def _largest_n(df: pd.DataFrame) -> int:
    return int(sorted(df["n_nodes"].unique())[-1])


def delay_vs_degree(prop: pd.DataFrame, adv: pd.DataFrame):
    if prop is None or not len(prop):
        return None
    import matplotlib.pyplot as plt
    style.apply_style()
    n = _largest_n(prop)
    mbd = int(sorted(prop["max_blend_delay"].unique())[0])
    d = prop[(prop.n_nodes == n) & (prop.max_blend_delay == mbd)]
    fig, ax = plt.subplots()
    for i, bh in enumerate(sorted(d.blend_hops.unique())):
        s = d[d.blend_hops == bh].groupby("degree").full_delay_ms_mean.mean().reset_index()
        ax.plot(s.degree, s.full_delay_ms_mean, "-o", ms=4, color=style.color_for(i),
                label=f"blend_hops={bh}")
    ax.set_xlabel("peering degree")
    ax.set_ylabel(_MS)
    ax.set_title(f"Blend full delay vs peering degree (N={n:,}, max_blend_delay={mbd}s)")
    ax.legend()
    return fig


def _median_degree(d: pd.DataFrame) -> int:
    degs = sorted(d.degree.unique())
    return int(degs[len(degs) // 2])


def delivery_vs_unresponsive(prop: pd.DataFrame, adv: pd.DataFrame):
    """Message success-delivery-rate vs the unresponsive fraction, one line per blend-path length.

    A message is delivered only if every relay on its (responsiveness-blind) path forwards, so the
    rate tracks the analytic ``(1-u)^blend_hops`` cascade-survival law (dashed) and is dominated by
    path length, not degree.
    """
    if prop is None or not len(prop) or prop["unresponsive_frac"].nunique() < 2:
        return None
    import matplotlib.pyplot as plt
    style.apply_style()
    n = _largest_n(prop)
    mbd = int(sorted(prop["max_blend_delay"].unique())[0])
    d = prop[(prop.n_nodes == n) & (prop.max_blend_delay == mbd)]
    deg = _median_degree(d)
    d = d[d.degree == deg]
    fig, ax = plt.subplots()
    for i, bh in enumerate(sorted(d.blend_hops.unique())):
        s = d[d.blend_hops == bh].groupby("unresponsive_frac").delivery_rate.mean().reset_index()
        c = style.color_for(i)
        ax.plot(s.unresponsive_frac, s.delivery_rate, "-o", ms=4, color=c,
                label=f"blend_hops={bh}")
        u = np.linspace(0.0, float(s.unresponsive_frac.max()), 50)
        ax.plot(u, (1.0 - u) ** bh, "--", lw=0.8, color=c, alpha=0.6)
    ax.set_xlabel("unresponsive fraction  u")
    ax.set_ylabel("message delivery rate")
    ax.set_ylim(0.0, 1.02)
    ax.set_title(f"Cascade delivery vs unresponsive nodes "
                 f"(N={n:,}, degree={deg}); dashed = $(1-u)^{{hops}}$")
    ax.legend()
    return fig


def coverage_vs_unresponsive(prop: pd.DataFrame, adv: pd.DataFrame):
    """Flood coverage of *delivered* messages vs the unresponsive fraction, one line per degree.

    Unresponsive nodes still receive but do not forward, so they strand pockets of the network; a
    higher peering degree supplies redundant paths that keep coverage high as ``u`` rises.
    """
    if prop is None or not len(prop) or prop["unresponsive_frac"].nunique() < 2:
        return None
    import matplotlib.pyplot as plt
    style.apply_style()
    n = _largest_n(prop)
    mbd = int(sorted(prop["max_blend_delay"].unique())[0])
    bh = int(sorted(prop["blend_hops"].unique())[0])
    d = prop[(prop.n_nodes == n) & (prop.max_blend_delay == mbd) & (prop.blend_hops == bh)]
    fig, ax = plt.subplots()
    for i, deg in enumerate(sorted(d.degree.unique())):
        s = d[d.degree == deg].groupby("unresponsive_frac").frac_reached.mean().reset_index()
        ax.plot(s.unresponsive_frac, s.frac_reached, "-o", ms=4, color=style.color_for(i),
                label=f"degree={deg}")
    ax.set_xlabel("unresponsive fraction  u")
    ax.set_ylabel("flood coverage  (fraction reached | delivered)")
    ax.set_title(f"Flood coverage vs unresponsive nodes (N={n:,}, blend_hops={bh})")
    ax.legend()
    return fig


def coverage_percolation(prop: pd.DataFrame, adv: pd.DataFrame):
    """Flood coverage vs churn across the percolation threshold, one line per degree.

    Unresponsive nodes relay nothing, so the network that carries a flood is the sub-graph induced
    on the responsive nodes -- site percolation on a random d-regular graph, whose giant component
    survives only while the responsive fraction exceeds ``1/(degree-1)``. The dotted verticals mark
    the predicted collapse ``u_c = 1 - 1/(degree-1)``; each degree's curve falls off its own mark.
    Needs a churn grid that reaches past 0.5 (see configs/percolation.yaml).
    """
    if prop is None or not len(prop) or float(prop["unresponsive_frac"].max()) <= 0.5:
        return None
    import matplotlib.pyplot as plt
    style.apply_style()
    n = _largest_n(prop)
    bh = int(sorted(prop["blend_hops"].unique())[0])
    d = prop[(prop.n_nodes == n) & (prop.blend_hops == bh)]
    if "redundancy" in d:
        d = d[d.redundancy == d.redundancy.min()]
    fig, ax = plt.subplots()
    for i, deg in enumerate(sorted(d.degree.unique())):
        c = style.color_for(i)
        s = d[d.degree == deg].groupby("unresponsive_frac").frac_reached.mean().reset_index()
        ax.plot(s.unresponsive_frac, s.frac_reached, "-o", ms=4, color=c, label=f"degree={deg}")
        if deg > 2:
            ax.axvline(1.0 - 1.0 / (deg - 1), ls=":", lw=0.8, color=c, alpha=0.7)
    ax.set_xlabel("unresponsive fraction  u")
    ax.set_ylabel("flood coverage  (fraction reached | delivered)")
    ax.set_ylim(-0.02, 1.02)
    ax.set_title(f"Churn percolation: coverage collapses at $u_c=1-1/(d-1)$ (N={n:,})")
    ax.legend()
    return fig


def delay_vs_blendhops(prop: pd.DataFrame, adv: pd.DataFrame):
    if prop is None or not len(prop) or prop["blend_hops"].nunique() < 2:
        return None
    import matplotlib.pyplot as plt
    style.apply_style()
    n = _largest_n(prop)
    mbd = int(sorted(prop["max_blend_delay"].unique())[0])
    d = prop[(prop.n_nodes == n) & (prop.max_blend_delay == mbd)]
    fig, ax = plt.subplots()
    for i, deg in enumerate(sorted(d.degree.unique())):
        s = d[d.degree == deg].groupby("blend_hops").full_delay_ms_mean.mean().reset_index()
        ax.plot(s.blend_hops, s.full_delay_ms_mean, "-o", ms=4, color=style.color_for(i),
                label=f"degree={deg}")
    ax.set_xlabel("blend-path hops")
    ax.set_ylabel(_MS)
    ax.set_title(f"Blend full delay vs path length (N={n:,}, max_blend_delay={mbd}s)")
    ax.legend()
    return fig


def delay_vs_N(prop: pd.DataFrame, adv: pd.DataFrame):
    if prop is None or not len(prop) or prop["n_nodes"].nunique() < 2:
        return None
    import matplotlib.pyplot as plt
    style.apply_style()
    mbd = int(sorted(prop["max_blend_delay"].unique())[0])
    bh = int(sorted(prop["blend_hops"].unique())[0])
    d = prop[(prop.max_blend_delay == mbd) & (prop.blend_hops == bh)]
    fig, ax = plt.subplots()
    for i, deg in enumerate(sorted(d.degree.unique())):
        s = d[d.degree == deg].groupby("n_nodes").full_delay_ms_mean.mean().reset_index()
        ax.plot(s.n_nodes, s.full_delay_ms_mean, "-o", ms=4, color=style.color_for(i),
                label=f"degree={deg}")
    ax.set_xscale("log")
    ax.set_xlabel("network size N")
    ax.set_ylabel(_MS)
    ax.set_title(f"Blend full delay vs network size (blend_hops={bh}, max_blend_delay={mbd}s)")
    ax.legend()
    return fig


def _adv_vs_fadv(adv: pd.DataFrame, col: str, ylabel: str, title: str):
    if adv is None or not len(adv):
        return None
    import matplotlib.pyplot as plt
    style.apply_style()
    n = _largest_n(adv)
    degs = sorted(adv[adv.n_nodes == n].degree.unique())
    deg = int(degs[len(degs) // 2])
    d = adv[(adv.n_nodes == n) & (adv.degree == deg)]
    fig, ax = plt.subplots()
    for i, mode in enumerate(sorted(d.adversary_mode.unique())):
        s = d[d.adversary_mode == mode].groupby("f_adv")[col].mean().reset_index()
        ax.plot(s.f_adv, s[col], "-o", ms=4, color=style.color_for(i), label=mode)
    ax.set_xlabel("adversary fraction  f_adv")
    ax.set_ylabel(ylabel)
    ax.set_title(f"{title} (N={n:,}, degree={deg})")
    ax.legend()
    return fig


def observed_vs_fadv(prop, adv):
    return _adv_vs_fadv(adv, "observed_frac", "honest observed (fraction)",
                        "Adversary observation vs f_adv")


def eclipse_vs_fadv(prop, adv):
    return _adv_vs_fadv(adv, "eclipsed_frac", "honest eclipsed (fraction)",
                        "Honest eclipse vs f_adv")


def _adv_vs_degree(adv: pd.DataFrame, col: str, ylabel: str, title: str):
    if adv is None or not len(adv) or adv["degree"].nunique() < 2:
        return None
    import matplotlib.pyplot as plt
    style.apply_style()
    n = _largest_n(adv)
    d = adv[adv.n_nodes == n]
    favs = sorted(d.f_adv.unique())
    f = favs[len(favs) // 2]
    d = d[d.f_adv == f]
    fig, ax = plt.subplots()
    for i, mode in enumerate(sorted(d.adversary_mode.unique())):
        s = d[d.adversary_mode == mode].groupby("degree")[col].mean().reset_index()
        ax.plot(s.degree, s[col], "-o", ms=4, color=style.color_for(i), label=mode)
    ax.set_xlabel("peering degree")
    ax.set_ylabel(ylabel)
    ax.set_title(f"{title} (N={n:,}, f_adv={f})")
    ax.legend()
    return fig


def observed_vs_degree(prop, adv):
    return _adv_vs_degree(adv, "observed_frac", "honest observed (fraction)",
                          "Adversary observation vs degree")


def eclipse_vs_degree(prop, adv):
    return _adv_vs_degree(adv, "eclipsed_frac", "honest eclipsed (fraction)",
                          "Honest eclipse vs degree")


def _heatmap(adv: pd.DataFrame, col: str, title: str):
    if adv is None or not len(adv) or adv["degree"].nunique() < 2 or adv["f_adv"].nunique() < 2:
        return None
    import matplotlib.pyplot as plt
    style.apply_style()
    n = _largest_n(adv)
    d = adv[(adv.n_nodes == n) & (adv.adversary_mode == "random")]
    if not len(d):
        d = adv[adv.n_nodes == n]
    piv = d.groupby(["degree", "f_adv"])[col].mean().unstack("f_adv")
    fig, ax = plt.subplots()
    im = ax.imshow(piv.values, origin="lower", aspect="auto", cmap=style.SEQUENTIAL_CMAP)
    ax.set_xticks(range(len(piv.columns)), [f"{c:g}" for c in piv.columns])
    ax.set_yticks(range(len(piv.index)), [str(int(i)) for i in piv.index])
    ax.set_xlabel("adversary fraction  f_adv")
    ax.set_ylabel("peering degree")
    ax.set_title(f"{title} (N={n:,})")
    fig.colorbar(im, ax=ax, shrink=0.85)
    return fig


def heatmap_observed(prop, adv):
    return _heatmap(adv, "observed_frac", "Honest observed fraction")


def heatmap_eclipse(prop, adv):
    return _heatmap(adv, "eclipsed_frac", "Honest eclipsed fraction")


# --- deanonymization: propagation paths x the adversary set (3-arg builders) -------------------

def _pos(s: pd.Series) -> pd.Series:
    """Blank out non-positive rates so they vanish on a log axis instead of erroring."""
    return s.where(s > 0)


def deanon_vs_blendhops(prop, adv, deanon):
    """P(whole blend path adversarial) vs path length, one line per f_adv (log-y).

    Relays are drawn blind to who is adversarial, so the rate is the exact hypergeometric ~
    ``f_adv**blend_hops`` (dashed) -- lengthening the blend path is the dominant defence, and it is
    independent of peering degree.
    """
    if deanon is None or not len(deanon) or deanon["blend_hops"].nunique() < 2:
        return None
    import matplotlib.pyplot as plt
    style.apply_style()
    n = _largest_n(deanon)
    d = deanon[(deanon.n_nodes == n) & (deanon.adversary_mode == "random") & (deanon.f_adv > 0)]
    if not len(d):
        return None
    deg = _median_degree(d)
    d = d[d.degree == deg]
    fig, ax = plt.subplots()
    for i, f in enumerate(sorted(d.f_adv.unique())):
        s = d[d.f_adv == f].groupby("blend_hops").deanon_rate.mean().reset_index()
        c = style.color_for(i)
        ax.plot(s.blend_hops, _pos(s.deanon_rate), "-o", ms=4, color=c, label=f"f_adv={f:g}")
        ax.plot(s.blend_hops, f ** s.blend_hops, "--", lw=0.8, color=c, alpha=0.6)
    ax.set_yscale("log")
    ax.set_xlabel("blend-path hops")
    ax.set_ylabel("deanonymization rate\nP(whole path adversarial)")
    ax.set_title(f"Deanonymization vs path length (N={n:,}, degree={deg}); "
                 f"dashed = $f_{{adv}}^{{hops}}$")
    ax.legend()
    return fig


def full_deanon_vs_blendhops(prop, adv, deanon):
    """P(whole path adversarial AND sender peered with an adversary) vs path length, per f_adv.

    Dashed = the closed form ``f_adv**hops * (1-(1-f_adv)**degree)`` at the plotted degree.
    """
    if deanon is None or not len(deanon) or deanon["blend_hops"].nunique() < 2:
        return None
    import matplotlib.pyplot as plt
    style.apply_style()
    n = _largest_n(deanon)
    d = deanon[(deanon.n_nodes == n) & (deanon.adversary_mode == "random") & (deanon.f_adv > 0)]
    if not len(d):
        return None
    deg = _median_degree(d)
    d = d[d.degree == deg]
    fig, ax = plt.subplots()
    for i, f in enumerate(sorted(d.f_adv.unique())):
        s = d[d.f_adv == f].groupby("blend_hops").full_deanon_rate.mean().reset_index()
        c = style.color_for(i)
        ax.plot(s.blend_hops, _pos(s.full_deanon_rate), "-o", ms=4, color=c, label=f"f_adv={f:g}")
        ax.plot(s.blend_hops, f ** s.blend_hops * (1.0 - (1.0 - f) ** deg), "--",
                lw=0.8, color=c, alpha=0.6)
    ax.set_yscale("log")
    ax.set_xlabel("blend-path hops")
    ax.set_ylabel("full-deanonymization rate\nP(path adversarial & sender exposed)")
    ax.set_title(f"Full deanonymization vs path length (N={n:,}, degree={deg})")
    ax.legend()
    return fig


def full_deanon_vs_fadv(prop, adv, deanon):
    """Full deanonymization vs adversary fraction, random vs worst-case placement (log-y).

    The whole-path-adversarial rate is placement-independent (thin grey ceiling); full
    deanonymization adds the sender-peer factor ``observed_frac``, which the worst-case-coverage
    adversary maximizes -- so the placements fan out below that ceiling.
    """
    if deanon is None or not len(deanon) or deanon["f_adv"].nunique() < 2:
        return None
    import matplotlib.pyplot as plt
    style.apply_style()
    n = _largest_n(deanon)
    bhs = sorted(deanon.blend_hops.unique())
    bh = int(bhs[len(bhs) // 2])
    d = deanon[(deanon.n_nodes == n) & (deanon.blend_hops == bh) & (deanon.f_adv > 0)]
    if not len(d):
        return None
    deg = _median_degree(d)
    d = d[d.degree == deg]
    fig, ax = plt.subplots()
    for i, mode in enumerate(sorted(d.adversary_mode.unique())):
        s = d[d.adversary_mode == mode].groupby("f_adv").full_deanon_rate.mean().reset_index()
        ax.plot(s.f_adv, _pos(s.full_deanon_rate), "-o", ms=4, color=style.color_for(i),
                label=f"full ({mode})")
    ceil = d[d.adversary_mode == "random"].groupby("f_adv").deanon_rate.mean().reset_index()
    if len(ceil):
        ax.plot(ceil.f_adv, _pos(ceil.deanon_rate), ":", lw=1.0, color="0.5",
                label="whole path (any placement)")
    ax.set_yscale("log")
    ax.set_xlabel("adversary fraction  f_adv")
    ax.set_ylabel("deanonymization rate")
    ax.set_title(f"Full deanonymization vs f_adv (N={n:,}, degree={deg}, blend_hops={bh})")
    ax.legend()
    return fig


def full_deanon_vs_degree(prop, adv, deanon):
    """Full deanonymization vs peering degree, per f_adv (fixed path length, log-y).

    ``deanon_rate`` (dashed) is degree-flat -- relays are uniform -- but the sender-peer factor
    ``1-(1-f_adv)**degree`` rises with degree, so *full* deanonymization worsens as degree grows
    even though a higher degree speeds propagation. The peering-degree tension, in one plot.
    """
    if deanon is None or not len(deanon) or deanon["degree"].nunique() < 2:
        return None
    import matplotlib.pyplot as plt
    style.apply_style()
    n = _largest_n(deanon)
    bhs = sorted(deanon.blend_hops.unique())
    bh = int(bhs[len(bhs) // 2])
    d = deanon[(deanon.n_nodes == n) & (deanon.blend_hops == bh)
               & (deanon.adversary_mode == "random") & (deanon.f_adv > 0)]
    if not len(d):
        return None
    fig, ax = plt.subplots()
    for i, f in enumerate(sorted(d.f_adv.unique())):
        c = style.color_for(i)
        s = d[d.f_adv == f].groupby("degree").agg(
            full=("full_deanon_rate", "mean"), whole=("deanon_rate", "mean")).reset_index()
        ax.plot(s.degree, _pos(s.full), "-o", ms=4, color=c, label=f"full, f_adv={f:g}")
        ax.plot(s.degree, _pos(s.whole), "--", lw=0.8, color=c, alpha=0.6)
    ax.set_yscale("log")
    ax.set_xlabel("peering degree")
    ax.set_ylabel("deanonymization rate")
    ax.set_title(f"Full deanonymization vs degree (N={n:,}, blend_hops={bh}); "
                 f"dashed = whole-path (degree-flat)")
    ax.legend()
    return fig


# --- linkability over time: how fast an emitter is linked / its stake learned (3-arg builders) ---

def _repr_linkability(deanon) -> tuple[float, int, int, float]:
    """Representative (f_adv, blend_hops, degree, observed_frac) for the linkability figures, taken
    from the middle of the swept grid (defaults when no deanon table is present)."""
    if deanon is None or not len(deanon):
        return 0.2, 3, 8, 1.0 - 0.8 ** 8
    d = deanon[deanon.f_adv > 0] if (deanon.f_adv > 0).any() else deanon
    fs = sorted(d.f_adv.unique())
    f = float(fs[len(fs) // 2])
    bhs = sorted(d.blend_hops.unique())
    bh = int(bhs[len(bhs) // 2])
    degs = sorted(d.degree.unique())
    deg = int(degs[len(degs) // 2])
    return f, bh, deg, float(1.0 - (1.0 - f) ** deg)


def time_to_link_vs_stake(prop, adv, deanon):
    """Time to link an emitter vs its stake, one line per accuracy alpha (log-log).

    A node emits with probability = stake per 30 s slot; a linkable node (>=1 adversary peer) is
    linked the first time a whole cascade is adversarial (prob ``q = f_adv^blend_hops`` per
    emission), so ``T_link ~ 30s*ln(1/(1-alpha))/(stake*q)`` -- inversely proportional to stake."""
    import matplotlib.pyplot as plt
    style.apply_style()
    f, bh, deg, obs = _repr_linkability(deanon)
    q = f ** bh
    stakes = np.logspace(-5, -1, 60)
    fig, ax = plt.subplots()
    for i, alpha in enumerate((0.5, 0.9, 0.99)):
        days = [time_to_link_seconds(s, q, alpha) / _DAY for s in stakes]
        ax.plot(stakes, days, color=style.color_for(i), label=f"$\\alpha$ = {alpha}")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("node stake fraction  s")
    ax.set_ylabel("time to link (days)")
    ax.set_title(f"Time to link vs stake (f_adv={f:g}, blend_hops={bh}, degree={deg}; "
                 f"linkable fraction {obs:.2f})")
    ax.legend()
    return fig


def time_to_link_vs_stake_redundancy(prop, adv, deanon):
    """Time to link vs stake, one line per messaging redundancy R (alpha=0.9, log-log).

    With R independent cascades the per-emission capture rate rises to ``1-(1-f_adv^hops)^R ~ R*``,
    so redundancy cuts the time to link by roughly R -- reliability bought at anonymity's cost."""
    import matplotlib.pyplot as plt
    style.apply_style()
    f, bh, deg, _ = _repr_linkability(deanon)
    d1 = f ** bh
    stakes = np.logspace(-5, -1, 60)
    fig, ax = plt.subplots()
    for i, R in enumerate((1, 2, 3, 4)):
        q = capture_prob(d1, 1.0, R)
        days = [time_to_link_seconds(s, q, 0.9) / _DAY for s in stakes]
        ax.plot(stakes, days, color=style.color_for(i), label=f"R = {R}")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("node stake fraction  s")
    ax.set_ylabel("time to link (days)")
    ax.set_title(f"Redundancy speeds linking (f_adv={f:g}, blend_hops={bh}, $\\alpha$=0.9)")
    ax.legend()
    return fig


def time_to_stake_vs_threshold(prop, adv, deanon):
    """Time to certify a node holds at least a stake threshold, vs the threshold (log-log).

    Attributable observations arrive at rate ``stake*q``; ``N`` of them pin the stake to relative
    precision ``~1/sqrt(N)``. Lines: identity (N=1), stake to +-10% (N=100), +-5% (N=400). Small
    thresholds take astronomically long -- a hard floor on how finely stake can be learned."""
    import matplotlib.pyplot as plt
    style.apply_style()
    f, bh, deg, _ = _repr_linkability(deanon)
    q = f ** bh
    thresholds = np.array([0.05, 0.01, 0.005, 0.001, 5e-4, 1e-4, 5e-5, 1e-5])
    fig, ax = plt.subplots()
    for i, (nobs, lab) in enumerate([(1, "identity link (N=1)"),
                                     (100, "stake $\\pm$10% (N=100)"),
                                     (400, "stake $\\pm$5% (N=400)")]):
        days = [time_to_stake_seconds(th, q, nobs) / _DAY for th in thresholds]
        ax.plot(thresholds * 100, days, "-o", ms=4, color=style.color_for(i), label=lab)
    for yr, txt in [(365.0, "1 yr"), (3650.0, "10 yr")]:
        ax.axhline(yr, ls=":", lw=0.8, color="0.6")
        ax.text(ax.get_xlim()[0], yr, f" {txt}", va="bottom", ha="left", fontsize=7, color="0.5")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("stake threshold  $\\theta$  (%)")
    ax.set_ylabel("time to certify stake $\\geq \\theta$ (days)")
    ax.set_title(f"Time to learn stake vs threshold (f_adv={f:g}, blend_hops={bh}, degree={deg})")
    ax.legend()
    return fig


def redundancy_time_to_link(prop, adv, deanon):
    """The redundancy trade in its two natural units at once: the delivery rate R buys (left axis,
    measured) against the time to link the emitter that it spends (right axis, log days, per stake).

    Redundancy multiplies the per-emission capture probability by ~R, so it divides the time to link
    by ~R -- four copies of every message roughly quarter a node's anonymity lifetime.
    """
    if (prop is None or not len(prop) or "redundancy" not in prop
            or prop["redundancy"].nunique() < 2):
        return None
    import matplotlib.pyplot as plt
    style.apply_style()
    n = _largest_n(prop)
    deg = _median_degree(prop[prop.n_nodes == n])
    bhs = sorted(prop.blend_hops.unique())
    bh = int(bhs[len(bhs) // 2])
    ufs = [u for u in sorted(prop.unresponsive_frac.unique()) if u > 0]
    u = ufs[len(ufs) // 2] if ufs else 0.0
    pr = prop[(prop.n_nodes == n) & (prop.degree == deg) & (prop.blend_hops == bh)
              & (prop.unresponsive_frac == u)]
    deliv = pr.groupby("redundancy").delivery_rate.mean().reset_index()
    if not len(deliv):
        return None
    f, _, _, _ = _repr_linkability(deanon)
    d1 = f ** bh
    rs = [int(r) for r in deliv.redundancy]

    fig, ax = plt.subplots()
    ax.plot(rs, deliv.delivery_rate, "-o", ms=6, color=style.color_for(0),
            label=f"delivery rate (u={u:g})   ↑ good")
    ax.set_xlabel("messaging redundancy  R  (independent cascades)")
    ax.set_ylabel("message delivery rate")
    ax.set_ylim(0.0, 1.02)
    ax.set_xticks(rs)
    ax2 = ax.twinx()
    ax2.grid(False)
    for i, (s, lab) in enumerate([(0.05, "5%"), (0.01, "1%"), (0.001, "0.1%")]):
        days = [time_to_link_seconds(s, capture_prob(d1, 1.0, r), 0.9) / _DAY for r in rs]
        ax2.plot(rs, days, "--s", ms=4, color=style.color_for(i + 1),
                 label=f"time to link, stake {lab}   ↓ bad")
    ax2.set_yscale("log")
    ax2.set_ylabel("time to link (days), $\\alpha$ = 0.9")
    h1, l1 = ax.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax.legend(h1 + h2, l1 + l2, fontsize=7, loc="center right")
    ax.set_title(f"Redundancy buys delivery, spends anonymity time\n"
                 f"(N={n:,}, degree={deg}, {bh} hops, f_adv={f:g})")
    return fig


def redundancy_tradeoff(prop, adv, deanon):
    """Reliability gain vs anonymity cost of messaging redundancy R (log-y).

    Delivery (from the churn sweep) and whole-path / full deanonymization (exact) both rise as
    ``1-(1-x)^R`` -- redundancy amplifies the wanted (delivery) and the unwanted (capture) together.
    """
    if (prop is None or not len(prop) or "redundancy" not in prop
            or prop["redundancy"].nunique() < 2):
        return None
    import matplotlib.pyplot as plt
    style.apply_style()
    n = _largest_n(prop)
    deg = _median_degree(prop[prop.n_nodes == n])
    bhs = sorted(prop.blend_hops.unique())
    bh = int(bhs[len(bhs) // 2])
    ufs = [u for u in sorted(prop.unresponsive_frac.unique()) if u > 0]
    u = ufs[len(ufs) // 2] if ufs else 0.0
    pr = prop[(prop.n_nodes == n) & (prop.degree == deg) & (prop.blend_hops == bh)
              & (prop.unresponsive_frac == u)]
    deliv = pr.groupby("redundancy").delivery_rate.mean().reset_index()
    fig, ax = plt.subplots()
    ax.plot(deliv.redundancy, _pos(deliv.delivery_rate), "-o", ms=5, color=style.color_for(0),
            label=f"delivery (u={u:g})  ↑ good")
    if deanon is not None and len(deanon) and "redundancy" in deanon:
        f, _, _, _ = _repr_linkability(deanon)
        dz = deanon[(deanon.n_nodes == deanon.n_nodes.max()) & (deanon.degree == deg)
                    & (deanon.blend_hops == bh) & (deanon.f_adv == f)
                    & (deanon.adversary_mode == "random")]
        if len(dz):
            g = dz.groupby("redundancy").agg(dr=("deanon_rate", "mean"),
                                             fd=("full_deanon_rate", "mean")).reset_index()
            ax.plot(g.redundancy, _pos(g.dr), "-s", ms=5, color=style.color_for(1),
                    label=f"whole-path capture (f_adv={f:g})  ↓ good")
            ax.plot(g.redundancy, _pos(g.fd), "-^", ms=5, color=style.color_for(2),
                    label="full deanonymization  ↓ good")
    ax.set_yscale("log")
    ax.set_xticks([1, 2, 3, 4])
    ax.set_xlabel("messaging redundancy  R  (independent cascades)")
    ax.set_ylabel("per-emission probability")
    ax.set_title(f"Redundancy: reliability vs anonymity (N={n:,}, degree={deg}, blend_hops={bh})")
    ax.legend()
    return fig
