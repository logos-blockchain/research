"""Every number MAPPING.md quotes (PLAN.md A2, A3).

    python scripts/mapping_numbers.py

Formulas are the specification's (logos-lips 47a73cdc, docs/blockchain/raw/):
- cryptarchia-v1-protocol.md: f = 1/30, slot = 1 s; s = 3*floor(k/f); epoch = 10*floor(k/f);
  the nonce is fixed 6*floor(k/f) into the previous epoch, so it leads its use by
  4*floor(k/f); the stake inference counts the first 6*floor(k/f) slots; W = 12 must stay
  within floor(0.6 k).
- fork-choice.md: s_gen = floor(k / (4 f)).
- cryptarchia-v1-bootstr-sync.md: T_offline = 20 min.
- bedrock-service-declaration-protocol.md: services read the registry of current_epoch - 2.
The stake inference's per-epoch noise is reports/tsi/README.md Appendix B's measured +-0.9 %
at k = 2160, scaled as 1/sqrt(T) with T = 6*floor(k/f).
"""

from __future__ import annotations

import math

F = 1 / 30
SLOT_S = 1.0
W_UNCLE = 12
T_OFFLINE_S = 20 * 60
TSI_NOISE_2160 = 0.9          # percent, per epoch, at k = 2160
KS = (2160, 1080, 432, 216, 120)
SIDES = (0.5, 0.3, 0.2)


def hours(slots: float) -> float:
    return slots * SLOT_S / 3600


def base(k: int) -> int:
    return math.floor(k / F)


def row(k: int) -> dict[str, float]:
    b = base(k)
    return {
        "k": k,
        "k-deep, no forks (h)": hours(b),
        "s (h)": hours(3 * b),
        "epoch (h)": hours(10 * b),
        "nonce lead (h)": hours(4 * b),
        "s_gen (h)": hours(math.floor(k / (4 * F))),
        "blocks per epoch": 10 * k,
        "inference window, occupied slots": 6 * k,
        "inference noise per epoch (%)": TSI_NOISE_2160 * math.sqrt(base(2160) / b),
        "floor(0.6 k) (W = 12 needs >= 12)": math.floor(0.6 * k),
        "offline grace margin (k/f)/T_offline": b * SLOT_S / T_OFFLINE_S,
        "SDP lag, 2 epochs (h)": hours(20 * b),
    }


def horizon_hours(depth: int, share: float) -> float:
    """Hours for a side holding ``share`` of the stake to make ``depth`` blocks, same epoch."""
    return hours(depth / (1 - (1 - F) ** share))


def main() -> None:
    print("1. What k sets, per value of k")
    rows = [row(k) for k in KS]
    for key in rows[0]:
        if key == "k":
            print(f"  {'k':42s}" + "".join(f"{r['k']:>10d}" for r in rows))
            continue
        cells = []
        for r in rows:
            v = r[key]
            cells.append(f"{v:>10.0f}" if isinstance(v, int) or v >= 100 else f"{v:>10.2f}")
        print(f"  {key:42s}" + "".join(cells))

    print("\n2. Self-healing horizon: hours for the losing side to make k blocks")
    print(f"  {'side stake share':42s}" + "".join(f"{k:>10d}" for k in KS))
    for share in SIDES:
        print(f"  {share:<42.1f}" + "".join(f"{horizon_hours(k, share):>10.1f}" for k in KS))

    print("\n3. The smallest k that keeps W = 12 inside floor(0.6 k):",
          min(k for k in range(1, 100) if math.floor(0.6 * k) >= W_UNCLE))


if __name__ == "__main__":
    main()
