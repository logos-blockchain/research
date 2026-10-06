import MiningOnboarding.Explore

/-!
Regression checks of `MiningOnboarding/Explore.lean` against the numbers in §12 of
`reports/mining_funded_onboarding.tex`. Every `#guard` fails the file if it does not hold:

  lake env lean MiningOnboardingTest/Report.lean
-/

open Onboarding.Explore

namespace Onboarding.Explore.Report

def n := reference
def year := epochsOfMonths 12
def close (x y tol : Float) : Bool := Float.abs (x - y) ≤ tol

-- §12.2, 100 identical newcomers, `M = 10⁶`: unlocked balance just before one year ...
#guard close (unlocked n 1e6 10000 year) 2.617 5e-4
#guard close (unlocked n 1e6 7500 year) 1.962 5e-4
#guard close (unlocked n 1e6 5000 year) 1.308 5e-4
#guard close (unlocked n 1e6 2500 year) 0.654 5e-4
#guard close (unlocked n 1e6 1000 year) 0.262 5e-4
-- ... and qualification time in months
#guard close ((qualTime n 1e6 10000).getD 0 |> monthsOfEpochs) 7.05 5e-3
#guard close ((qualTime n 1e6 7500).getD 0 |> monthsOfEpochs) 8.25 5e-3
#guard close ((qualTime n 1e6 5000).getD 0 |> monthsOfEpochs) 10.32 5e-3
#guard (qualTime n 1e6 2500).isNone
#guard (qualTime n 1e6 1000).isNone
-- about 1.333 million LOGOS remain at one year
#guard close (pool n 1e6 year) 1.333e6 1e3
-- newcomers need more than about 38.22% of payouts
#guard close ((gammaMin n 100 1e6 year).getD 0) 0.3822 5e-5

-- §12.3, six-month target, 100 equal newcomers, `γ = 1`
def six := epochsOfMonths 6
#guard close ((mMin n 100 1 six).getD 0) 14255.75 5e-3
#guard close (14256 * six) 346896 1e-6
#guard close (unlocked n (100 * 14256) 14256 six) 1.000014 5e-7
#guard close (stake n (100 * 14256) 14256 six) 346897.000014 1e-6
#guard close (pool n (100 * 14256) six) 15.3104e6 1
#guard close (m0 n six) 11621 1
#guard close (m1 n 100 1 six) 13823 1

-- The simulator, run as a single cohort, agrees with the closed form.
def single : Outcome :=
  simulate { net := n, SC0 := 0, policy := .fixedTotal 1e6 0 1,
             arrivals := fun e => if e == 0 then 100 else 0, epochs := 1 }
#guard close (single.cohorts[0]!.tau.getD 0 |> monthsOfEpochs) 7.05 1e-2
#guard close single.cohorts[0]!.bAtL 2.617 2e-3

end Onboarding.Explore.Report
