"""Which metrics carry over from the unrestricted model to the countable one? (§9)

Most of the report's studies predate the countable default. They reproduce exactly under `--old`,
so the question is not whether they are valid runs — it is whether their *numbers* still describe
the countable design. §9 used to answer that wholesale ("no difference is resolvable in the design
regime, so those findings carry over"), and that is how the §8.4 capstone went stale: its `p_ref`
was quoted at 1.000 for weeks after the redesign made the true value 0.944.

The wholesale answer is wrong because the carry-over is metric-specific. Accuracy barely moves
between the models at `rho < 1` — that is the §3.2a finding. But `p_ref` is not a small difference,
it is an artefact: under the unrestricted rule EVERY in-window orphan is referenceable, so
`p_ref ~ 1` is a restatement of the model rather than a measurement of the design.

This prints the per-metric verdict off the committed paired sweep, where both arms share the stake
draw, the peering graph and every lottery outcome, so the uncle rule is the only difference and the
comparison is a paired one. Any metric that fails here must be re-measured rather than carried over.

Run:  python scripts/model_carryover.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent.parent
RUNS = HERE / "runs"

# The design band: the operating regime the recommendation lives in. U = 0 is excluded because
# with no uncle slots the two models are identical by construction and would dilute the contrast.
METRICS = ["mean_ratio", "fork_rate", "mean_orphan_rate", "agreement_tip", "p_ref"]
CELL = ["blend_delay_max", "max_uncles", "replicate"]


def _load(label: str) -> pd.DataFrame:
    """Equilibrium tail of the newest paired run with this label."""
    src = sorted(RUNS.glob(f"*_{label}/results.parquet"))[-1]
    df = pd.read_parquet(src)
    return df[(df.epoch >= df.epochs.iloc[0] // 2) & (df.max_uncles > 0)]


def main() -> None:
    countable, unrestricted = _load("fine-paired-countable"), _load("fine-paired-old")
    print("=== countable vs unrestricted ceiling, PAIRED, design band (delta_max 1-5, U >= 1) ===")
    print(f"{'metric':>18} {'countable':>11} {'ceiling':>11} {'paired diff':>20} {'t':>7}  verdict")
    for m in METRICS:
        if m not in countable.columns:
            continue
        a = countable.groupby(CELL)[m].mean()
        b = unrestricted.groupby(CELL)[m].mean()
        i = a.index.intersection(b.index)
        d = b[i] - a[i]
        # Paired t over cells. A metric "carries over" if the gap is negligible against the
        # +-0.9% per-epoch noise floor of Appendix B, NOT if it merely fails to resolve --- with
        # 40 paired replicates even a 0.06% gap resolves, and that one is still immaterial.
        t = d.mean() / d.sem() if d.std(ddof=1) > 0 else float("nan")
        verdict = "carries over" if abs(d.mean()) < 0.009 else "RE-MEASURE"
        print(f"{m:>18} {a[i].mean():11.4f} {b[i].mean():11.4f} "
              f"{d.mean():+12.5f}+-{d.sem():.5f} {t:7.1f}  {verdict}")
    print("\np_ref is the one that fails: the unrestricted model makes every in-window orphan\n"
          "referenceable, so its ~1.0 is a property of the model, not of the design.")


if __name__ == "__main__":
    main()
