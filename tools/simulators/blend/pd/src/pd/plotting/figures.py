"""Figure builders for pd. Each takes (prop_df, adv_df) and returns a Figure or None.

Propagation full delay (ms) vs peering degree / blend-path length / network size, and adversary
observation + eclipse fractions vs adversary fraction / degree (with the worst-case envelope) plus
heatmaps. Slices default to the largest N and a representative setting.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import style

_MS = "full propagation delay (ms)"


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
