import MiningOnboarding.Explore

/-!
Starting points for exploring the onboarding design with the continuing-entry simulator
(§19 of the report: "Does the policy preserve onboarding opportunities for later cohorts?").

  lake env lean MiningOnboardingTest/Experiments.lean
-/

open Onboarding.Explore

namespace Onboarding.Explore.Experiments

/-- A year of arrivals (49 epochs) of `k` newcomers per epoch, no capitalised miners. -/
def run (net : Net) (policy : Policy) (k : Nat) : Outcome :=
  simulate { net, SC0 := 0, policy, arrivals := fun _ => k, epochs := 49 }

def summary (o : Outcome) : String :=
  s!"qualified {round o.qualifiedFraction}, first failing cohort {o.firstFailure}, pool exhausted at {fmtOpt o.exhaustedAt}"

-- Fixed total payout `M = 10⁶`, all to newcomers, versus entry rate.
#eval IO.println <| String.intercalate "\n" <| [1, 10, 100].map fun k =>
  s!"fixedTotal 1e6, {k}/epoch: " ++ summary (run reference (.fixedTotal 1e6 0 1) k)

-- Fixed individual income: the six-month rate of §12.3, versus entry rate.
#eval IO.println <| String.intercalate "\n" <| [1, 10, 100].map fun k =>
  s!"fixedIndividual 14256, {k}/epoch: " ++ summary (run reference (.fixedIndividual 14256 0) k)

-- The immediately unlocked fraction `β` removes the leadership-only ceiling.
#eval IO.println <| String.intercalate "\n" <| [0, 1e-5, 1e-4].map fun β =>
  s!"β = {β}, fixedTotal 1e6, 10/epoch: " ++ summary (run { reference with β } (.fixedTotal 1e6 0 1) 10)

-- Per-cohort table.
#eval IO.println (run reference (.fixedTotal 1e6 0 1) 10).table

end Onboarding.Explore.Experiments
