"""UNITS.md's tables, read from runs/n1 to runs/n6; tables.py dispatches n* here.

    python scripts/tables.py n1committee | n1units | n1rounding | n2registry | n2lottery |
                             n3budget | n3load | n3p2p | n4privacy | n4holders | n4ceilings |
                             n5bytes | n5verify | n5prove | n6time | n6layers | n6online
"""

from __future__ import annotations

import math
import pathlib

import pandas as pd

from tables import duration, md

RUNS = pathlib.Path(__file__).resolve().parent.parent / "runs"
FULL = "every honest unit online"


def _share(a: float) -> str:
    return "a third" if abs(a - 1 / 3) < 1e-9 else f"{100 * a:.0f} %"


def _online(u: float) -> str:
    return "all" if u == 1.0 else f"{100 * u:.0f} %"


def _count(v: float) -> str:
    return "none" if not math.isfinite(v) else f"{v:,.0f}"


def _pct(v: float, digits: int = 1) -> str:
    return "none" if not math.isfinite(v) else f"{100 * v:.{digits}f} %"


def _uptime(v: float) -> str:
    return "none" if not math.isfinite(v) else f"{100 * v:.1f} %"


def _minutes(s: float) -> str:
    if s < 3600:
        return f"{s / 60:.1f} min"
    return f"{s / 3600:.2f} h"


def _days(d: float) -> str:
    return duration(d)


def n1committee() -> None:
    t = pd.read_csv(RUNS / "n1" / "committee.csv")
    print(md(pd.DataFrame({
        "coalition": t.alpha.map(_share),
        "honest units online": t.uptime.map(_online),
        "anonymous seats a round: no margin / sized for the inference's error up to 1.05": [
            f"{_count(a)} / {_count(b)}" for a, b in zip(t.seats, t.sized)],
        "counted, drawn with replacement (M.1)": t["count"].map(_count),
        "a private draw over 30,000 units, seats expected": t.private.map(_count),
        "a public draw from 30,000 units": t.public.map(_count),
        "every unit voting, 30,000 a round": t.every_holds.map(
            lambda v: "holds" if v else "fails")})))


def n1units() -> None:
    t = pd.read_csv(RUNS / "n1" / "units.csv")
    rows = []
    for (size, units), g in t.groupby(["unit", "units"], sort=True):
        def public(a, u):
            return _count(g[(abs(g.alpha - a) < 1e-9) & (g.uptime == u)].public.iloc[0])

        def every(a):
            return _uptime(g[abs(g.alpha - a) < 1e-9].every_uptime.iloc[0])

        rows.append({
            "a unit, share of the supply": f"{100 * size:g} %",
            "registered units": f"{units:,}",
            "a public draw against 25 %: all online / 95 %": f"{public(0.25, 1.0)} / {public(0.25, 0.95)}",
            "against 30 %: all online / 95 %": f"{public(0.30, 1.0)} / {public(0.30, 0.95)}",
            "the least uptime at which every unit voting holds, against 25 % / 30 %":
                f"{every(0.25)} / {every(0.30)}"})
    print(md(pd.DataFrame(rows)))


def n1rounding() -> None:
    t = pd.read_csv(RUNS / "n1" / "rounding.csv")
    rows = []
    for loss, g in t.groupby("loss", sort=True):
        a25, a30 = g[abs(g.alpha - 0.25) < 1e-9], g[abs(g.alpha - 0.30) < 1e-9]
        rows.append({
            "the honest stake lost below whole units": f"{100 * loss:.0f} %",
            "the coalition's share of the units, holding 25 % / 30 % of the stake":
                f"{_pct(a25.unit_share.iloc[0])} / {_pct(a30.unit_share.iloc[0])}",
            "a public draw against 30 %: all online / 95 %":
                f"{_count(a30[a30.uptime == 1.0].public.iloc[0])} / "
                f"{_count(a30[a30.uptime == 0.95].public.iloc[0])}",
            "the least uptime at which every unit voting holds, against 30 %":
                _uptime(a30.every_uptime.iloc[0])})
    print(md(pd.DataFrame(rows)))


def n2registry() -> None:
    r = pd.read_csv(RUNS / "n2" / "registry.csv").iloc[0]
    print(md(pd.DataFrame([{
        "registered units": f"{int(r.units):,}",
        "the window": f"{int(r.window_slots):,} slots, {r.window_h:.0f} h",
        "registrations a second": f"{r.per_s:.3f}",
        "a registration (bytes)": f"{int(r.bytes)}",
        "the registry an epoch (MB)": f"{r.epoch_mb:.2f}",
        "registrations an epoch, holders of 1 % / 0.1 % / 0.01 %":
            f"{int(r['holder_0.01'])} / {int(r['holder_0.001'])} / {int(r['holder_0.0001'])}"}])))


def n2lottery() -> None:
    t = pd.read_csv(RUNS / "n2" / "lottery.csv")
    rows = []
    for (a, u), g in t.groupby(["alpha", "uptime"], sort=False):
        reg, inf = g[g["mode"] == "registered"].iloc[0], g[g["mode"] == "inferred"].iloc[0]

        def h(v):
            return f"{v:.2f}" if math.isfinite(v) else "more than 416"

        rows.append({
            "coalition": _share(a),
            "honest registered stake online": "all" if u == 1.0 else (
                "two thirds" if abs(u - 2 / 3) < 1e-9 else f"{100 * u:.0f} %"),
            "the coalition's share of the online stake": _pct(reg.alpha_online),
            "a block every (s): divided by the registered stake / by the inferred":
                f"{reg.interval_s:.1f} / {inf.interval_s:.1f}",
            "the wait (h): divided by the registered stake / by the inferred":
                f"{h(reg.wait_h)} / {h(inf.wait_h)}"})
    print(md(pd.DataFrame(rows)))


def n3budget() -> None:
    t = pd.read_csv(RUNS / "n3" / "budget.csv")
    rows = []
    for (c, n), g in t.groupby(["committee", "units"], sort=False):
        lo = g[g.budget == "no vote in a node's cover"].iloc[0]
        hi = g[g.budget == "equal stakes"].iloc[0]
        rows.append({"committee against 30 %": c, "units a round": f"{n:,}",
                     "the shortest round: no vote in a node's cover, 4/3 votes a second / equal stakes, 2.27":
                         f"{_minutes(lo.round_s)} / {_minutes(hi.round_s)}"})
    print(md(pd.DataFrame(rows)))


def n3load() -> None:
    t = pd.read_csv(RUNS / "n3" / "load.csv")
    t = t[(t.round_s == 600) & (t.committee == "public draw, every honest unit online")
          & (t.layers.isin([3, 8]))]
    rows = [{"core nodes": "any", "layers": "3", "transport": "today's traffic, no votes",
             "vote messages a second": "0", "verifications the votes add, share of one Pi 5 core": "0",
             "the read limit / the node budget, in Pi 5 cores": "20 / 0.96",
             "received (MB/s)": f"{4 * 16 * 19_318 / 1e6:.2f}"}]
    for _, r in t.iterrows():
        rows.append({"core nodes": f"{int(r.nodes):,}", "layers": str(int(r.layers)),
                     "transport": r.transport,
                     "vote messages a second": f"{r.vote_messages_per_s:.2f}",
                     "verifications the votes add, share of one Pi 5 core": _pct(r.added_cores),
                     "the read limit / the node budget, in Pi 5 cores":
                         f"{int(r.r1)} / {r.v_cores:.2f}",
                     "received (MB/s)": f"{r.received_mb:.2f}"})
    print(md(pd.DataFrame(rows)))


def n3p2p() -> None:
    t = pd.read_csv(RUNS / "n3" / "p2p.csv")
    t = t[t.round_s == 600]
    print(md(pd.DataFrame({
        "core nodes": t.nodes.map(lambda v: f"{v:,}"),
        "layers": t.layers.astype(str),
        "the schedule's messages a node carries a second: point to point / through Blend's flooding": [
            f"{m:.3f} / {h * n / 600:.1f}" for m, h, n in zip(t.messages_per_s, t.layers, t.nodes)]})))


def n4privacy() -> None:
    t = pd.read_csv(RUNS / "n4" / "privacy.csv")
    t = t[(t.share == 0.001) & (t.round_s == 600)
          & ((t.committee == FULL) | (t.committee == "every unit voting"))]
    first = t.iloc[0]
    rows = [{"layers": "3", "votes": "none: blocks only, today",
             "days to identify": _days(first.today_identify_days),
             "days to size to ±10 %": _days(first.today_size_days), "of today's time": "1"}]
    for _, r in t.sort_values(["layers"], kind="stable").iterrows():
        rows.append({"layers": str(int(r.layers)), "votes": r.transport,
                     "days to identify": _days(r.identify_days),
                     "days to size to ±10 %": _days(r.size_days),
                     "of today's time": f"{r.multiple:.3f}"})
    print(md(pd.DataFrame(rows)))


def n4holders() -> None:
    t = pd.read_csv(RUNS / "n4" / "privacy.csv")
    t = t[(t.layers == 8) & (t.round_s == 600) & (t.committee == FULL)]
    rows = []
    for s, g in t.groupby("share", sort=False):
        def size(tr):
            r = g[g.transport == tr].iloc[0]
            return f"{_days(r.size_days)} / {r.multiple:.2f}"

        rows.append({"holder": f"{100 * s:g} %",
                     "today: days to size": _days(g.today_size_days.iloc[0]),
                     "schedule, public draw, unlinkable: days / of today's":
                         size("schedule, public draw, unlinkable"),
                     "schedule, public draw, linkable keys": size("schedule, public draw, linkable keys"),
                     "one vote a message, unlinkable": size("one vote a message, unlinkable")})
    print(md(pd.DataFrame(rows)))


def n4ceilings() -> None:
    t = pd.read_csv(RUNS / "n4" / "ceilings.csv")
    rows = []
    today = t[t.design == "blocks only, today"].set_index("nodes").share
    rows.append({"what a node sends": "blocks only, today",
                 "on 1,000 core nodes": _pct(today[1000.0], 2),
                 "on 20,000 core nodes": _pct(today[20000.0], 3)})
    one = t[t.design == "one vote a message"]
    for c, g in one.groupby("committee", sort=False):
        g = g.set_index("nodes").share
        rows.append({"what a node sends": f"one vote a message, rounds of 600 s, {c}",
                     "on 1,000 core nodes": _pct(g[1000.0], 4),
                     "on 20,000 core nodes": _pct(g[20000.0], 4)})
    for _, r in t[t.design == "schedule"].iterrows():
        v = _pct(r.share, 2)
        rows.append({"what a node sends": f"the schedule, {r.committee}, {r.packaging}",
                     "on 1,000 core nodes": v, "on 20,000 core nodes": v})
    print(md(pd.DataFrame(rows)))


def n5bytes() -> None:
    t = pd.read_csv(RUNS / "n5" / "bytes.csv")
    t = t[t.committee == "public draw, every honest unit online"]
    print(md(pd.DataFrame({
        "packaging": t.packaging,
        "a unit's vote (bytes)": t.unit_vote_bytes.astype(str),
        "a message's own bytes": t.message_fixed_bytes.astype(str),
        "units' votes a message carries, at most": t.k_max.astype(str),
        "a certificate of the quorum against 30 %, every honest unit online (KB)": [
            f"{a:.0f} to {b:.0f}" for a, b in zip(t.certificate_kb_min, t.certificate_kb_max)]})))


def n5verify() -> None:
    t = pd.read_csv(RUNS / "n5" / "verify.csv")
    rows = []
    for (pk, c, units, nodes), g in t.groupby(["packaging", "committee", "units", "nodes"],
                                              sort=False, dropna=False):
        g = g.set_index("round_s").core_share
        what = (f"{c}, {int(units):,} proofs a round" if pk == "a proof a unit"
                else f"one from each of {int(nodes):,} core nodes")
        rows.append({"packaging": pk, "proofs": what,
                     "one Pi 5 core, rounds of 10 minutes / an hour":
                         f"{_pct(g[600])} / {_pct(g[3600])}"})
    print(md(pd.DataFrame(rows)))


def n5prove() -> None:
    t = pd.read_csv(RUNS / "n5" / "prove.csv")
    t = t[t.round_s == 600]
    print(md(pd.DataFrame({
        "committee against 30 %": t.committee,
        "holder": t.share.map(lambda s: f"{100 * s:g} %"),
        "registrations an epoch (s)": t.registration_s_per_epoch.map(lambda v: f"{v:.1f}"),
        "votes a round": t.votes_per_round.map(lambda v: f"{v:.1f}"),
        "proving a round (s)": t.vote_s_per_round.map(lambda v: f"{v:.2f}"),
        "the machine, rounds of 10 minutes": t.machine_share.map(lambda v: _pct(v, 2))})))


def _time_rows(t: pd.DataFrame) -> list[dict]:
    rows = []
    for _, r in t.iterrows():
        rows.append({
            "transport": r.transport + ("" if r.transport == "Blend as specified" else
                                        f", {int(r.layers)} layers"),
            "core nodes": "any" if not math.isfinite(r.nodes) or r.transport != "schedule"
            else f"{int(r.nodes):,}",
            "verifications the votes add, share of one Pi 5 core":
                "M.2's budget" if not math.isfinite(r.budget) else _pct(r.budget, 0),
            "round (s)": f"{int(r.round_s):,}",
            "final on average: the checkpoint gadget / one certificate":
                f"{_minutes(r.gadget_s)} / {_minutes(r.single_s)}",
            "the node budget, in Pi 5 cores / received (MB/s)":
                f"{r.v_cores:.2f} / {r.received_mb:.2f}",
            "a holder of 0.1 % sized (days) / of today's":
                f"{r.size_days:,.0f} / {r.multiple:.2f}"})
    return rows


def n6time() -> None:
    t = pd.read_csv(RUNS / "n6" / "time.csv")
    t = t[t.committee == FULL]
    spec = t[t.transport == "Blend as specified"]
    sched = t[(t.transport == "schedule") & (t.layers == 8)]
    one = t[(t.transport == "one vote a message") & (t.layers == 8) & (t.nodes == 1000)]
    print(md(pd.DataFrame(_time_rows(pd.concat([spec, sched, one])))))


def n6layers() -> None:
    t = pd.read_csv(RUNS / "n6" / "time.csv")
    t = t[(t.committee == FULL) & (t.transport == "schedule") & (t.budget == 0.2)]
    print(md(pd.DataFrame({
        "core nodes": t.nodes.map(lambda v: f"{int(v):,}"),
        "layers": t.layers.astype(int).astype(str),
        "round (s)": t.round_s.map(lambda v: f"{int(v):,}"),
        "final on average, the checkpoint gadget": t.gadget_s.map(_minutes),
        "a holder of 0.1 % sized (days) / of today's": [
            f"{d:,.1f} / {m:.3f}" if d < 100 else f"{d:,.0f} / {m:.2f}"
            for d, m in zip(t.size_days, t.multiple)]})))


def n6online() -> None:
    t = pd.read_csv(RUNS / "n6" / "time.csv")
    t = t[(t.committee != FULL) & (t.transport == "schedule") & (t.layers == 8)]
    print(md(pd.DataFrame({
        "committee against 30 %, 95 % of the honest units online": t.committee.map(
            lambda c: "every unit voting" if c.startswith("every unit") else "a public draw"),
        "units a round": t.units.map(lambda v: f"{int(v):,}"),
        "core nodes": t.nodes.map(lambda v: f"{int(v):,}"),
        "verifications the votes add, share of one Pi 5 core": t.budget.map(lambda v: _pct(v, 0)),
        "round (s)": t.round_s.map(lambda v: f"{int(v):,}"),
        "final on average, the checkpoint gadget": t.gadget_s.map(_minutes),
        "a holder of 0.1 % sized (days) / of today's": [
            f"{d:,.0f} / {m:.2f}" for d, m in zip(t.size_days, t.multiple)]})))
