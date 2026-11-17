"""Independent recheck: how much a grindable epoch nonce weakens a finality window.

Everything here is computed from the study's source (finality_sim.waitbound, finality_sim.grinding)
with this script only. Caches and outputs stay inside this folder.
"""

from __future__ import annotations

import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
for _name, _sub in (("NUMBA_CACHE_DIR", ".cache/numba"), ("TMPDIR", ".cache/tmp"),
                    ("JOBLIB_TEMP_FOLDER", ".cache/joblib")):
    _p = HERE / _sub
    _p.mkdir(parents=True, exist_ok=True)
    os.environ[_name] = str(_p)
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True
os.environ.setdefault("NUMBA_NUM_THREADS", "1")       # joblib workers: one numba thread each
SRC = os.path.join(str(HERE), "..", "..", "..", "..", "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import json  # noqa: E402
import math  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402

CACHE = HERE / ".cache" / "data"
CACHE.mkdir(exist_ok=True)

F = 1 / 30
EPS = 1e-9
ONLINE = 0.9                    # the honest stake left online in an "offline" state
# name, delay (s), a tenth of the honest stake offline, inference deflated
STATES = (
    ("0 none, 10 s", 10, False, False),
    ("1 15 s", 15, False, False),
    ("2 offline, 10 s", 10, True, False),
    ("3 deflated, 10 s", 10, False, True),
    ("4 15 s + offline", 15, True, False),
    ("5 15 s + deflated", 15, False, True),
    ("6 offline + deflated, 10 s", 10, True, True),
)
GRIND = dict(budget_bits=64, depths=4000, floor=100, per_bit=4)


def active_share(s: float, offline: bool) -> float:
    """The coalition's share of the stake that is active (online and building)."""
    return s / (s + ONLINE * (1.0 - s)) if offline else s


def scale_of(a: float, deflated: bool) -> float:
    """What every lottery threshold is multiplied by: 1/(1 - a) once the inferred stake is only
    the honest stake online."""
    return 1.0 / (1.0 - a) if deflated else 1.0


def lottery_rate(scale: float) -> float:
    """The chance that a slot is occupied when all active stake builds: 1 - (1 - F)^scale."""
    return 1.0 - (1.0 - F) ** scale


def params(state: int, s: float) -> dict:
    _, delta, offline, deflated = STATES[state]
    a = active_share(s, offline)
    scale = scale_of(a, deflated)
    return dict(state=state, s=s, delta=delta, a=a, scale=scale, f_grind=lottery_rate(scale))


def _key(kind: str, **kw) -> pathlib.Path:
    parts = [kind] + [f"{k}={v!r}" for k, v in sorted(kw.items())]
    return CACHE / ("_".join(parts).replace("/", "-").replace(" ", "") + ".npz")


def curve(a: float, delta: int, scale: float, t_max: int, floor: float) -> np.ndarray:
    """wait_curve, cached on disk. Entry t - 1 bounds the chance after a wait of t slots."""
    path = _key("curve", a=round(a, 12), delta=delta, scale=round(scale, 12), t_max=t_max, floor=floor)
    if path.exists():
        return np.load(path)["c"]
    from finality_sim.waitbound import wait_curve
    t0 = time.time()
    c = wait_curve(t_max, a, delta, F, floor=floor, scale=scale)
    np.savez_compressed(path, c=c, seconds=time.time() - t0)
    return c


def grind(f: float, a: float, delta: int) -> dict:
    """pair_bounds and factors at 1e-9, cached on disk: one nonce and two, both ends."""
    path = _key("grind", f=round(f, 14), a=round(a, 12), delta=delta, **GRIND)
    if path.exists():
        z = np.load(path, allow_pickle=True)
        return json.loads(str(z["row"]))
    from finality_sim.grinding import factors, pair_bounds
    t0 = time.time()
    row = dict(f=f, a=a, delta=delta)
    try:
        ts, lo1, up1, lo2, up2 = pair_bounds(f, a, delta=delta, **GRIND)
        row["one_lo"], row["one_hi"] = (float(v) for v in factors(ts, lo1, up1, EPS))
        row["two_lo"], row["two_hi"] = (float(v) for v in factors(ts, lo2, up2, EPS))
        row["error"] = ""
        extra = dict(ts=ts, lo1=lo1, up1=up1, lo2=lo2, up2=up2)
    except ValueError as exc:                       # the walk outran the settings given
        row.update(one_lo=math.nan, one_hi=math.nan, two_lo=math.nan, two_hi=math.nan,
                   error=str(exc))
        extra = {}
    row["seconds"] = time.time() - t0
    np.savez_compressed(path, row=json.dumps(row), **extra)
    return row


def wait_needed(c: np.ndarray, eps: float) -> int:
    """The first wait t, in slots, with c[t - 1] <= eps; -1 if the curve never gets there."""
    hit = np.nonzero(c <= eps)[0]
    return int(hit[0]) + 1 if hit.size else -1
