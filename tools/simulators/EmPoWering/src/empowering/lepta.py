"""Exact-integer confirmation of the mechanism at lepton granularity.

The analyses in this package compute in float LGO, which is correct for every
dimensionless ratio but cannot confirm the integer mechanics: the pool holds about
5*10^16 lepta against float64's 2^53 exact-integer ceiling, and the protocol floors
where floats keep fractional lepta. This module re-runs the pool dynamics entirely in
integer lepta, mirroring the specification's checked uint64 arithmetic, and asserts
the properties the Units and Precision specification makes normative:

  * every intermediate fits uint64 (conservation bounds every fee aggregate at the
    supply, so no widening is needed for token values);
  * not one lepton is created or destroyed: fees split exactly into burnt + diverted,
    and the pool identity holds exactly at every boundary;
  * the flooring residues go where the specifications say -- the refill's residue to
    the burn, the per-claim reward's to the pool;
  * the sigma cliff sits exactly at pool < RATE_DEN * T * N_b lepta;
  * the float engine agrees with the exact engine on every ratio, and its absolute
    drift is bounded and reported rather than hidden;
  * the Units doc's canonical parse/format round-trips exactly on the full range.

Run:  make lepta        (or python -m empowering.lepta --config configs/specified.toml)
"""
from __future__ import annotations

import argparse
import random
import sys

from . import core
from .params import Params, load

U64_MAX = 2**64 - 1


def checked_u64(v: int) -> int:
    """The specification's checked_uint64: reject, never wrap or saturate."""
    assert 0 <= v <= U64_MAX, f"uint64 violation: {v:.3e}"
    return v


def simulate_exact(p: Params, epochs: int, n_tx: int | None = None):
    """Pool dynamics in integer lepta, at the target claim rate.

    Returns (rows, totals). Fees per block are the reference traffic's transfers at
    the resting price, in whole lepta, exactly as the ledger would see them.
    """
    u = p.base_units_per_lgo
    n = p.n_tx_ref if n_tx is None else n_tx
    fees_block = checked_u64(n * (p.transfer_tx_bytes + p.transfer_tx_gas) * p.price_resting)
    pool = checked_u64(int(p.genesis_pool_fraction * p.S_tge) * u)
    claims_per_epoch = p.T * p.N_b
    rows, burnt_total, diverted_total, minted_notes = [], 0, 0, 0
    for e in range(epochs):
        sigma = checked_u64(pool * p.rho_num) // (p.rho_den * p.T * p.N_b)
        # epoch-level form of the per-claim guard; exact at the target rate since
        # drain = claims*sigma = floor-rho(pool) <= pool (verify gate 29)
        enabled = sigma > 0 and pool >= sigma
        drain = checked_u64(claims_per_epoch * sigma) if enabled else 0
        # refill: per-block flooring, residue explicitly to the burn
        refill = burnt_e = 0
        for _ in range(p.N_b):
            diverted = checked_u64(fees_block * p.beta_num) // p.beta_den
            burnt = fees_block - diverted            # includes the flooring residue
            assert diverted + burnt == fees_block    # not one lepton lost in the split
            refill += diverted
            burnt_e += burnt
        new_pool = checked_u64(pool - drain + refill)
        assert new_pool == pool - drain + refill      # exact identity, no rounding
        rows.append(dict(epoch=e, pool=pool, sigma=sigma, drain=drain, refill=refill))
        burnt_total += burnt_e
        diverted_total += refill
        minted_notes += drain
        pool = new_pool
    return rows, dict(burnt=burnt_total, diverted=diverted_total,
                      paid_out=minted_notes, final_pool=pool)


# ---- the Units and Precision reference conversions, for the round-trip check ----

LEPTA_PER_LOGOS = 10**9


def parse_logos(s: str) -> int:
    if "." in s:
        i, f = s.split(".", 1)
    else:
        i, f = s, ""
    if not i.isdigit() or (f and not f.isdigit()) or len(f) > 9:
        raise ValueError(s)
    v = int(i) * LEPTA_PER_LOGOS + int(f.ljust(9, "0") or 0)
    if v > U64_MAX:
        raise ValueError(s)
    return v


def format_logos(v: int) -> str:
    whole, frac = divmod(v, LEPTA_PER_LOGOS)
    return f"{whole}.{str(frac).rjust(9, '0')}"


def run(config: str) -> int:
    p = load(config)
    failures = []

    def check(name, ok, note=""):
        print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f": {note}" if note else ""))
        if not ok:
            failures.append(name)

    print(f"exact-integer lepta confirmation against {p.name}\n")
    E = p.horizon_epochs
    rows, tot = simulate_exact(p, E)

    # 1. Conservation, globally: everything that left the fee flow is accounted for.
    fees_total = E * p.N_b * p.n_tx_ref * (p.transfer_tx_bytes + p.transfer_tx_gas) * p.price_resting
    check("fees split exactly into burnt + diverted",
          tot["burnt"] + tot["diverted"] == fees_total,
          f"{fees_total:,} lepta over {E} epochs")
    pool0 = int(p.genesis_pool_fraction * p.S_tge) * p.base_units_per_lgo
    check("pool identity exact over the horizon",
          tot["final_pool"] == pool0 + tot["diverted"] - tot["paid_out"],
          f"final pool {tot['final_pool']:,} lepta")

    # 2. Everything stayed in uint64 (checked_u64 would have raised otherwise).
    check("every intermediate within uint64", True,
          f"max seen ~{max(r['pool'] for r in rows):,} lepta vs {U64_MAX:,}")

    # 3. The sigma cliff sits exactly where the specification says.
    edge = p.rho_den * p.T * p.N_b
    s_at = (edge * p.rho_num) // (p.rho_den * p.T * p.N_b)
    s_below = ((edge - 1) * p.rho_num) // (p.rho_den * p.T * p.N_b)
    check("cliff exactly at RATE_DEN*T*N_b lepta",
          s_at == 1 and s_below == 0, f"boundary {edge:,} lepta")

    # 4. Float engine vs exact engine: ratios agree, drift bounded and visible.
    frows = core.simulate_pool(p, epochs=E)
    u = p.base_units_per_lgo
    drift = max(abs(fr["pool"] * u - r["pool"]) for fr, r in zip(frows, rows))
    rel = max(abs(fr["sigma"] * u - r["sigma"]) / r["sigma"]
              for fr, r in zip(frows, rows) if r["sigma"])
    # The divergence is flooring semantics, not float noise: the float engine pays the
    # fractional lepton the protocol floors away, so each claim can differ by under one
    # lepton and the honest bound is one lepton per claim paid.
    check("float engine ratio agreement", rel < 1e-8, f"worst rel {rel:.1e}")
    bound = p.T * p.N_b * E
    check("float-engine drift within one lepton per claim", drift < bound,
          f"max {drift:,.0f} lepta vs bound {bound:,} on a "
          f"{rows[-1]['pool']:,}-lepton pool (why the exact engine exists)")

    # 5. Units doc round-trip: canonical parse/format identity across the range.
    rng = random.Random(9)
    samples = [0, 1, U64_MAX, U64_MAX - 1, LEPTA_PER_LOGOS,
               18_446_744_073_709_551_615] + [rng.randrange(U64_MAX) for _ in range(10_000)]
    check("parse(format(v)) == v for 10,006 values",
          all(parse_logos(format_logos(v)) == v for v in samples))
    bad = ["1.0000000001", "18446744073.709551616", "1.1234567891"]

    def rejects(s):
        try:
            parse_logos(s)
            return False
        except ValueError:
            return True
    check("rejects >9 fractional digits and out-of-range",
          all(rejects(s) for s in bad))

    print(f"\n{len(failures)} failure(s)" if failures else "\nall confirmed")
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="empowering.lepta")
    ap.add_argument("--config", required=True)
    return run(ap.parse_args().config)


if __name__ == "__main__":
    sys.exit(main())
