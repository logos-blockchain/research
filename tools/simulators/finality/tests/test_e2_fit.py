"""Gate for the §5.6 fit of E2 (scripts/e2_fit.py) against the chain's race in closed form."""

import math
import pathlib
import sys

import numpy as np

from test_race import closed

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
from e2_fit import fit  # noqa: E402


def test_the_fit_lands_short_of_the_closed_form():
    """The premined strict chain race at B3's measured q, over E2's 60 depths: the depth the fit
    extrapolates to 1e-9 falls 3–5 % short of the exact one."""
    for q in (0.255, 0.28, 0.307, 0.334):
        p = np.array([closed(q, k, True, 1) for k in range(1, 61)])
        a, rho, _ = fit(p * 1e12, 10 ** 12)
        fitted = math.log(a / 1e-9) / rho
        k = 1
        while closed(q, k, True, 1) > 1e-9:
            k += 1
        assert 0.95 * k <= fitted <= 0.97 * k, (q, fitted, k)
