"""SIGNERS.md's tables, read from runs/m1 to runs/m7; tables.py dispatches m* here.

    python scripts/tables.py m1anon | m1public | m1delegation | m2budget | m2blend | m2compare |
                             m3privacy | m4cost | m4blend | m5quorum | m7supply | m7seats |
                             m7wait | m7edge | m7declared
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

from tables import duration, md

RUNS = pathlib.Path(__file__).resolve().parent.parent / "runs"
EVERY = "anonymous seats, every honest seat counting"
ERROR = "anonymous seats, the inference's error up to 1.05"
LEADERS = "the chain's own leaders, counted, every honest leader online"
LEADERS95 = "the chain's own leaders, counted, 95 % online"


def _share(a: float) -> str:
    return "a third" if abs(a - 1 / 3) < 1e-9 else f"{100 * a:.0f} %"


def _pct(v: float, digits: int = 1) -> str:
    return "none" if not math.isfinite(v) else f"{100 * v:.{digits}f} %"


def _count(v: float) -> str:
    return "none" if not math.isfinite(v) else f"{v:,.0f}"


def _time(seconds: float) -> str:
    if not math.isfinite(seconds):
        return "none"
    if seconds < 3600:
        return f"{seconds / 60:.1f} min"
    if seconds < 48 * 3600:
        return f"{seconds / 3600:.1f} h"
    return f"{seconds / 86400:.1f} d"


def _hours(h: float) -> str:
    return "–" if not math.isfinite(h) else f"{h:.2f}"


def m1anon() -> None:
    t = pd.read_csv(RUNS / "m1" / "anonymous.csv")

    def wins(n, h):
        return "none" if not math.isfinite(n) else f"{n:,.0f} / {_time(3600 * h)}"

    print(md(pd.DataFrame({
        "coalition": t.alpha.map(_share),
        "anonymous seats a round: every honest seat counting / the inference's error up to 1.05 / a tenth of the honest votes lost": [
            f"{_count(a)} / {_count(b)} / {_count(c)}"
            for a, b, c in zip(t.seats_all, t.seats_inflated, t.seats_lost)],
        "the chain's own leaders, counted: wins / the time the chain takes to record them, every honest leader online": [
            wins(n, h) for n, h in zip(t.wins_u1, t.window_u1_h)],
        "the same, 95 % of the honest leaders online": [
            wins(n, h) for n, h in zip(t.wins_u095, t.window_u095_h)],
        "the same, 90 % online": [
            wins(n, h) for n, h in zip(t.wins_u09, t.window_u09_h)],
    })))


def m1public() -> None:
    t = pd.read_csv(RUNS / "m1" / "public.csv")
    print(md(pd.DataFrame({
        "coalition": t.alpha.map(_share),
        "an opt-in set: the honest stake declared, uptime 1 / 0.95": [
            f"{_pct(a, 0)} / {_pct(b, 0)}" for a, b in zip(t.optin_u1, t.optin_u095)],
        "every leading note declared: the honest stake online, at least": t.declared_least_uptime.map(
            lambda v: _pct(v, 2)),
        "with 5 % of the honest stake below the minimum stake: the coalition's share of the weight / the honest stake online, at least": [
            f"{_pct(a, 2)} / {_pct(u, 2)}" for a, u in zip(t.below_share, t.below_least_uptime)],
        "the honest stake below the minimum stake that breaks it at full uptime": [
            "–" if a >= 1 / 3 - 1e-12 else _pct(v, 1) for a, v in zip(t.alpha, t.below_breaks)],
    })))


def m1delegation() -> None:
    t = pd.read_csv(RUNS / "m1" / "delegation.csv")
    rows = []
    for a, g in t.groupby("alpha", sort=True):
        g = g.set_index("uptime")
        full = g.loc[1.0]
        rows.append({
            "coalition": _share(a),
            "uptime 1": _pct(full.attracted, 2),
            "uptime 0.95": _pct(g.loc[0.95].attracted, 2),
            "uptime 0.9": _pct(g.loc[0.9].attracted, 2),
            "Cardano's largest pools that hold it, uptime 1": (
                "–" if not math.isfinite(full.attracted)
                else f"{int(full.pools)} of {int(full.of_pools):,}")})
    print(md(pd.DataFrame(rows)))


def m2budget() -> None:
    t = pd.read_csv(RUNS / "m2" / "budget.csv")
    print(md(pd.DataFrame({"budget": t["mode"],
                           "votes a second, network-wide": t.votes_per_s.map(lambda v: f"{v:.3f}")})))


def m2blend() -> None:
    t = pd.read_csv(RUNS / "m2" / "blend.csv")
    rows = []
    for (a, s), g in t.groupby(["alpha", "set"], sort=False):
        g = g.set_index("mode")
        low, card, eq, up = (g.loc[m] for m in ("no vote in a node's cover", "Cardano's pools",
                                                 "equal stakes", "cover raised"))
        ok = math.isfinite(low.n)
        rows.append({
            "coalition": _share(a), "set": s,
            "committee / quorum": f"{_count(low.n)} / {_count(low.quorum)}" if ok else "none",
            "no vote in a node's cover: round / gadget, mean / gadget, latest / single certificate, mean": (
                f"{_time(low.round_s)} / {_time(low.gadget_s)} / {_time(low.latest_s)} / "
                f"{_time(low.single_s)}" if ok else "none"),
            "Cardano's pools: round / gadget, mean": (
                f"{_time(card.round_s)} / {_time(card.gadget_s)}" if ok else "none"),
            "equal stakes: round / gadget, mean": (
                f"{_time(eq.round_s)} / {_time(eq.gadget_s)}" if ok else "none"),
            "cover raised: round / gadget, mean": (
                f"{_time(up.round_s)} / {_time(up.gadget_s)}" if ok else "none")})
    print(md(pd.DataFrame(rows)))


def m2compare() -> None:
    y = pd.read_csv(RUNS / "m2" / "yardstick.csv")
    b = pd.read_csv(RUNS / "m2" / "blend.csv")
    on_top = ("no vote in a node's cover", "Cardano's pools", "equal stakes")

    def gadget(a, s, mode):
        g = b[(abs(b.alpha - a) < 1e-9) & (b.set == s) & (b["mode"] == mode)]
        return float(g.gadget_s.iloc[0]) / 3600

    def three(a, s):
        return " / ".join(_hours(gadget(a, s, m)) for m in on_top)

    rows = []
    for _, r in y.iterrows():
        a = r.alpha
        rows.append({
            "coalition": _share(a),
            "the chain's own wait, random delay (h)": _hours(r.chain_random_h),
            "anonymous seats, every honest seat counting, on top of today's cover: no vote in a node's cover / Cardano's pools / equal stakes (h)": three(a, EVERY),
            "the chain's own leaders, counted, every honest leader online, the same three (h)": three(a, LEADERS),
            "the same, 95 % of the honest leaders online (h)": three(a, LEADERS95),
            "with the cover raised, the fastest set: the chain's own leaders, every one online (h)": _hours(
                gadget(a, LEADERS, "cover raised")),
            "the chain's own wait, worst case at 10 s: without grinding / the new nonce of `slots.md` §4 after a deflation (h)": (
                f"{_hours(r.chain_worst_h)} / {_hours(r.chain_deflated_h)}")})
    print(md(pd.DataFrame(rows)))


def m3privacy() -> None:
    t = pd.read_csv(RUNS / "m3" / "privacy.csv")
    rows = []
    for name, g in t.groupby("setting", sort=False):
        g = g.set_index("share")
        first = g.iloc[0]
        label = name
        if math.isfinite(first.round_s):
            label = f"{name}, rounds of {_time(first.round_s)}"
        row = {"votes": label,
               "votes a second, network-wide": (
                   "–" if first.votes_per_s == 0 else f"{first.votes_per_s:.3f}"),
               "a node's lottery emissions, times blocks alone": f"{first.emission_multiple:.2f}",
               "the quota ceiling on 20,000 nodes": f"{100 * first.ceiling:.4f} %",
               "a win tied to its leader's node": f"{first.win_linked:.3f}"}
        for s, col in ((0.01, "1 %"), (0.001, "0.1 %"), (0.0001, "0.01 %")):
            row[f"a {col} holder: identified / sized to ±10 %"] = (
                f"{duration(g.loc[s].identify_days)} / {duration(g.loc[s].size_days)}")
        rows.append(row)
    print(md(pd.DataFrame(rows)))


def m4cost() -> None:
    t = pd.read_csv(RUNS / "m4" / "cost.csv")
    print(md(pd.DataFrame({
        "public signers, rounds of 60 slots": t.signers.map(lambda v: f"{v:,}"),
        "votes a second": t.votes_per_s.map(lambda v: f"{v:,.2f}"),
        "one Pi 5 core, verifying": t.core_share.map(lambda v: f"{100 * v:.2f} %"),
        "received (KB/s)": t.kb_per_s.map(lambda v: f"{v:.1f}")})))


def m4blend() -> None:
    t = pd.read_csv(RUNS / "m4" / "blend.csv")
    print(md(pd.DataFrame({
        "votes through Blend": t["mode"],
        "votes a second, network-wide": t.votes_per_s.map(lambda v: f"{v:.3f}"),
        "Blend headers a node verifies a second, more / one Pi 5 core": [
            f"{h:.1f} / {100 * s:.2f} %" for h, s in zip(t.headers_per_s, t.headers_share)],
        "a leader's signature, one Pi 5 core": t.signature_share.map(lambda v: f"{100 * v:.4f} %"),
        "a core connection carries, today / with the votes (KB/s)": [
            f"{a:.0f} / {b:.0f}" for a, b in zip(t.kb_per_connection_today, t.kb_per_connection)],
        "transaction messages the votes take, the backlog's headroom kept": t.transactions_taken.map(
            lambda v: _pct(v, 1)),
        "Blend keys a leader's votes need a win / today's leadership quota a win": [
            f"{k:.0f} / {q:.0f}" for k, q in zip(t.leader_keys_per_win, t.leadership_quota)]})))


def m5quorum() -> None:
    t = pd.read_csv(RUNS / "m5" / "quorum.csv")
    rows = []
    for name, g in t.groupby("quorum", sort=False):
        g = g.set_index("uptime")
        rows.append({
            "quorum": name,
            "two conflicting certificates from": _pct(g.loc[1.0].conflicting),
            "certificates stall above, uptime 1 / 0.95 / 0.9": " / ".join(
                _pct(g.loc[u].stalls_above) for u in (1.0, 0.95, 0.9))})
    print(md(pd.DataFrame(rows)))


def m7supply() -> None:
    t = pd.read_csv(RUNS / "m7" / "supply.csv")
    print(md(pd.DataFrame({
        "coalition, share of the active stake": t.alpha.map(_share),
        "share of the supply, at most, with the active stake at 30 % of it": t.supply_share.map(
            lambda v: _pct(v, 1))})))


def m7seats() -> None:
    t = pd.read_csv(RUNS / "m7" / "seats.csv")

    def broken(active, supply):
        return "–" if not math.isfinite(active) else f"{_pct(active)} / {_pct(supply)}"

    print(md(pd.DataFrame({
        "coalition": t.alpha.map(_share),
        "anonymous seats a round, sized for the inference's error up to 1.05": t.sized_seats.map(
            _count),
        "the true over the inferred active stake once the coalition's stake enters": t.entering.map(
            lambda v: f"{v:.2f}"),
        "anonymous seats a round, sized for that": t.entered_seats.map(_count),
        "honest stake entering that breaks the seats sized for 1.05: share of the active stake / of the supply": [
            broken(a, s) for a, s in zip(t.break_active, t.break_supply)]})))


def m7wait() -> None:
    t = pd.read_csv(RUNS / "m7" / "wait.csv")
    named = {1.0: "the inference at the true stake", round(1 / 0.7, 6): "a coalition of 30 % entering",
             1.5: "a coalition of a third entering"}
    rows = []
    for x, g in t.groupby("x", sort=True):
        g = g.set_index(g.alpha.round(6))
        label = f"{x:.2f}"
        if round(x, 6) in named:
            label += f", {named[round(x, 6)]}"

        def h(a):
            v = g.loc[round(a, 6)].wait_h
            return f"{v:.2f}" if math.isfinite(v) else "more than 416"

        rows.append({
            "the true over the inferred active stake": label,
            "a block every": f"{g.interval_s.iloc[0]:.1f} s",
            "the wait against 30 % (h)": h(0.30),
            "the wait against a third (h)": h(1 / 3)})
    print(md(pd.DataFrame(rows)))


def m7edge() -> None:
    # the edge rounds down and the least inferred stake up, so neither reads past what holds
    t = pd.read_csv(RUNS / "m7" / "edge.csv")
    print(md(pd.DataFrame({
        "coalition": t.alpha.map(_share),
        "the true over the inferred active stake up to which the wait stays within 18 hours": t.edge.map(
            lambda v: f"{math.floor(1000 * v) / 1000:.3f}"),
        "the least inferred active stake that keeps the true within it, the active stake at most 30 % of the supply": t.least_inferred.map(
            lambda v: f"{math.ceil(1000 * v) / 10:.1f} %")})))


def m7declared() -> None:
    t = pd.read_csv(RUNS / "m7" / "declared.csv")
    print(md(pd.DataFrame({
        "active stake, share of the supply": t.active.map(lambda v: _pct(v, 0)),
        "the minimum stake, share of the supply": t.minimum.map(lambda v: _pct(v, 3)),
        "declarations, at most": t.declarations.map(lambda v: f"{v:,}"),
        "votes a second, rounds of 60 slots": t.votes_per_s.map(lambda v: f"{v:,.2f}"),
        "one Pi 5 core, verifying": t.core_share.map(lambda v: f"{100 * v:.2f} %"),
        "received (KB/s)": t.kb_per_s.map(lambda v: f"{v:.1f}")})))
