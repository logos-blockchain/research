"""Independent recheck: an 18-hour finality window against a coalition of 30 % of the stake.

Run with the finality simulator's interpreter, for example from tools/simulators/finality:

    PYTHONDONTWRITEBYTECODE=1 \
    .venv/bin/python slot-finality/floor/recheck/delay-limits/recheck.py

Uses only ``finality_sim.waitbound.wait_curve``. Reads nothing else from the parent folder.
Writes ``results.json`` and ``results.txt`` beside this file. Caches go to ``./.cache``.

The curve ``c = wait_curve(t_max, alpha, delta_s, f, floor=1e-13, scale=scale)`` holds at
``c[t - 1]`` the bound on the chance that the coalition displaces a block after a wait of ``t``
slots (1 slot = 1 second). With ``floor > 0`` the array ends at the first wait whose bound is at
most ``floor``, so it can be shorter than ``t_max``.

- The wait at 1e-9: the first ``t`` with ``c[t - 1] <= 1e-9``, in hours ``t / 3600``.
- A window of 18 hours holds a state when ``c[64800 - 1] <= 1e-9``. A curve that ended at the
  floor before 64800 holds it and is marked.

States (the coalition holds ``s = 0.30`` of the total stake):

- no disturbance: ``alpha = s``, ``scale = 1``;
- a fraction ``o`` of the honest stake online, inference corrected: ``alpha = s / (s + o (1 - s))``,
  ``scale = 1``;
- deflated inference: ``scale = 1 / (1 - alpha)`` with the state's ``alpha``.
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "..", "..", "..", "src")
for _var, _sub in (("NUMBA_CACHE_DIR", "numba"), ("TMPDIR", "tmp"), ("JOBLIB_TEMP_FOLDER", "joblib")):
    _path = os.path.join(HERE, ".cache", _sub)
    os.makedirs(_path, exist_ok=True)
    os.environ[_var] = _path
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True
os.environ["PYTHONPATH"] = SRC + (os.pathsep + os.environ["PYTHONPATH"] if os.environ.get("PYTHONPATH") else "")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import json
import time
from fractions import Fraction

from joblib import Parallel, delayed

S = 0.30                    # the coalition's share of the total stake
F = 1 / 30                  # the lottery's chance that a slot is won
EPS = 1e-9                  # the target chance
FLOOR = 1e-13               # the curve is not resolved below this
WINDOW = 18 * 3600          # 64800 slots
T_MAX = 400_000             # for the waits
DELAYS = list(range(10, 26))
JOBS = 8


def alpha_online(o: float) -> float:
    """The coalition's share of the stake that builds when a fraction ``o`` of the honest stake
    is online."""
    return S / (S + o * (1 - S))


def deflated(alpha: float) -> float:
    return 1 / (1 - alpha)


def run(alpha: float, delta_s: int, scale: float, t_max: int) -> dict:
    """One curve, reduced to what the recheck reads."""
    import numpy as np

    import finality_sim
    from finality_sim.waitbound import wait_curve

    t0 = time.time()
    c = wait_curve(t_max, alpha, delta_s, F, floor=FLOOR, scale=scale)
    n = int(c.size)
    hit = np.nonzero(c <= EPS)[0]
    wait = int(hit[0]) + 1 if hit.size else -1
    p_window = float(c[WINDOW - 1]) if n >= WINDOW else None
    ended_at_floor = bool(n < t_max or c[-1] <= FLOOR)
    if p_window is not None:
        holds = bool(p_window <= EPS)
    else:
        holds = bool(c[-1] <= FLOOR)        # fell to the floor before the window
    rises = recross = None
    if wait > 0:
        tail = c[wait - 1:]
        rises = int((np.diff(tail) > 0).sum())          # increases after the first crossing
        recross = bool((tail > EPS).any())              # above 1e-9 again after it
    return dict(alpha=alpha, delta_s=delta_s, scale=scale, t_max=t_max, n=n, wait=wait,
                wait_h=wait / 3600 if wait > 0 else None, p_window=p_window, holds=holds,
                ended_at_floor=ended_at_floor, p_end=float(c[-1]), p_max=float(c.max()),
                rises_after_crossing=rises, recross=recross, seconds=time.time() - t0,
                module=finality_sim.__file__)


def key(alpha: float, delta_s: int, scale: float, t_max: int) -> str:
    return f"{alpha!r}|{delta_s}|{scale!r}|{t_max}"


class Store:
    """Results by state, saved after every batch."""

    def __init__(self, path: str):
        self.path = path
        self.data: dict[str, dict] = {}
        if os.path.exists(path):
            with open(path) as fh:
                self.data = json.load(fh).get("runs", {})

    def get(self, par: Parallel, jobs: list[tuple]) -> list[dict]:
        todo = [j for j in dict.fromkeys(jobs) if key(*j) not in self.data]
        if todo:
            for j, r in zip(todo, par(delayed(run)(*j) for j in todo)):
                self.data[key(*j)] = r
            self.save()
        return [self.data[key(*j)] for j in jobs]

    def save(self, extra: dict | None = None) -> None:
        with open(self.path, "w") as fh:
            json.dump(dict(runs=self.data, **(extra or {})), fh, indent=1)


def largest_delay(store: Store, par: Parallel, alpha: float, scale: float, log) -> tuple[int, dict]:
    """The largest whole delay at which the window holds, with every delay scanned."""
    scan = {d: r for d, r in zip(DELAYS, store.get(par, [(alpha, d, scale, WINDOW) for d in DELAYS]))}
    d = max(DELAYS)
    while scan[d]["holds"]:                 # holds at the top of the range: go on above it
        d += 1
        scan[d] = store.get(par, [(alpha, d, scale, WINDOW)])[0]
    d = min(DELAYS)
    while not scan[d]["holds"] and d > 0:   # fails at the bottom of the range: go on below it
        d -= 1
        scan[d] = store.get(par, [(alpha, d, scale, WINDOW)])[0]
    held = [d for d in sorted(scan) if scan[d]["holds"]]
    limit = max(held) if held else None
    if limit is not None:
        ok = all(scan[d]["holds"] == (d <= limit) for d in scan)
        log(f"  holds up to {limit} s; one boundary in the scan: {ok}")
        if not ok:
            log("  WARNING: the window does not hold on one interval of delays")
    return limit, scan


def smallest_online(store: Store, par: Parallel, delta_s: int, log) -> tuple[int, dict]:
    """The smallest whole percent of the honest stake online at which the window holds."""
    scan: dict[int, dict] = {}
    top = 100
    while top > 0:
        batch = list(range(top, max(top - JOBS, 0), -1))
        for p, r in zip(batch, store.get(par, [(alpha_online(p / 100), delta_s, 1.0, WINDOW) for p in batch])):
            scan[p] = r
        if not all(scan[p]["holds"] for p in batch):
            break
        top -= JOBS
    held = [p for p in sorted(scan) if scan[p]["holds"]]
    limit = min(held) if held else None
    if limit is not None:
        ok = all(scan[p]["holds"] == (p >= limit) for p in scan)
        log(f"  holds from {limit} % up; one boundary in the scan: {ok}")
        if not ok:
            log("  WARNING: the window does not hold on one interval of shares online")
    return limit, scan


def fmt_p(p) -> str:
    return "below floor" if p is None else f"{p:.3e}"


def fmt_h(r: dict) -> str:
    return "none" if r["wait"] < 0 else f"{r['wait_h']:.2f}"


def main() -> None:
    lines: list[str] = []

    def log(text: str = "") -> None:
        print(text, flush=True)
        lines.append(text)

    store = Store(os.path.join(HERE, "results.json"))
    t_start = time.time()

    # Compile once here, so that the workers load the compiled code from the cache.
    warm = run(S, 10, 1.0, 2_000)
    log(f"module: {warm['module']}")
    log(f"warm-up: {warm['seconds']:.1f} s")

    a0 = S
    a90 = alpha_online(0.90)
    states = [
        ("1", "no stake offline, not deflated", a0, 1.0),
        ("2", "no stake offline, deflated", a0, deflated(a0)),
        ("3", "o = 0.90, not deflated", a90, 1.0),
        ("4", "o = 0.90, deflated", a90, deflated(a90)),
    ]
    log(f"alpha(o = 0.90) = {a90!r}; exact 10/31 = {float(Fraction(10, 31))!r}")
    log(f"scale deflated at alpha = 0.30: {deflated(a0)!r}; exact 10/7 = {float(Fraction(10, 7))!r}")
    log(f"scale deflated at alpha(o = 0.90): {deflated(a90)!r}; exact 31/21 = {float(Fraction(31, 21))!r}")
    log()

    with Parallel(n_jobs=JOBS) as par:
        # Everything in the delay scans at once, then the scans read from the store.
        store.get(par, [(a, d, sc, WINDOW) for _, _, a, sc in states for d in DELAYS])
        limits = {}
        for item, name, a, sc in states:
            log(f"item {item}: {name}; alpha = {a!r}, scale = {sc!r}")
            limit, scan = largest_delay(store, par, a, sc, log)
            limits[item] = (limit, scan)
            for d in sorted(scan):
                r = scan[d]
                log(f"    delay {d:2d} s  holds {str(r['holds']):5s}  chance after 18 h {fmt_p(r['p_window']):>11s}"
                    f"  curve length {r['n']:6d}  ({r['seconds']:.0f} s)")
            log()

        log("item 5: delay 10 s, not deflated, a fraction o of the honest stake online")
        o_limit, o_scan = smallest_online(store, par, 10, log)
        for p in sorted(o_scan, reverse=True):
            r = o_scan[p]
            log(f"    o = {p:3d} %  alpha = {r['alpha']!r:20s}  holds {str(r['holds']):5s}"
                f"  chance after 18 h {fmt_p(r['p_window']):>11s}  curve length {r['n']:6d}  ({r['seconds']:.0f} s)")
        log()

        # The waits: full curves at each limit, its neighbour, and one point further each way.
        full = []
        for item, name, a, sc in states:
            limit = limits[item][0]
            if limit is not None:
                full += [(a, d, sc, T_MAX) for d in (limit - 1, limit, limit + 1, limit + 2) if d >= 1]
        if o_limit is not None:
            full += [(alpha_online(p / 100), 10, 1.0, T_MAX)
                     for p in (o_limit + 1, o_limit, o_limit - 1, o_limit - 2) if 0 < p <= 100]
        store.get(par, full)

        summary = []
        log("RESULT (window 18 h = 64800 s, target 1e-9, f = 1/30, floor 1e-13, t_max 400000)")
        for item, name, a, sc in states:
            limit, scan = limits[item]
            if limit is None:
                log(f"item {item}: {name}: the window holds at no delay scanned")
                continue
            for d, role in ((limit - 1, "context"), (limit, "limit d"), (limit + 1, "d + 1"), (limit + 2, "context")):
                if d < 1:
                    continue
                r = store.get(par, [(a, d, sc, T_MAX)])[0]
                same = r["p_window"] == scan[d]["p_window"] if d in scan else None
                log(f"item {item}: {name:32s} {role:8s} delta_s = {d:2d}  alpha = {a!r}  scale = {sc!r}"
                    f"  wait {fmt_h(r):>6s} h ({r['wait']} s)  chance after 18 h {fmt_p(r['p_window'])}"
                    f"  holds {r['holds']}  rises after crossing {r['rises_after_crossing']}"
                    f"  recross {r['recross']}  equals scan {same}")
                summary.append(dict(item=item, state=name, role=role, limit=limit, delta_s=d, alpha=a,
                                    scale=sc, wait_s=r["wait"], wait_h=r["wait_h"],
                                    p_window=r["p_window"], holds=r["holds"]))
            log()
        if o_limit is None:
            log("item 5: the window holds at no share online scanned")
        else:
            for p, role in ((o_limit + 1, "context"), (o_limit, "limit o"), (o_limit - 1, "o - 1 %"), (o_limit - 2, "context")):
                if not 0 < p <= 100:
                    continue
                a = alpha_online(p / 100)
                r = store.get(par, [(a, 10, 1.0, T_MAX)])[0]
                same = r["p_window"] == o_scan[p]["p_window"] if p in o_scan else None
                log(f"item 5: delay 10 s, o = {p:3d} %              {role:8s} delta_s = 10  alpha = {a!r}  scale = 1.0"
                    f"  wait {fmt_h(r):>6s} h ({r['wait']} s)  chance after 18 h {fmt_p(r['p_window'])}"
                    f"  holds {r['holds']}  rises after crossing {r['rises_after_crossing']}"
                    f"  recross {r['recross']}  equals scan {same}")
                summary.append(dict(item="5", state="delay 10 s, not deflated", role=role, limit=o_limit,
                                    online_pct=p, delta_s=10, alpha=a, scale=1.0, wait_s=r["wait"],
                                    wait_h=r["wait_h"], p_window=r["p_window"], holds=r["holds"]))
    log()
    log(f"total {time.time() - t_start:.0f} s")
    store.save(dict(summary=summary))
    with open(os.path.join(HERE, "results.txt"), "w") as fh:
        fh.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
