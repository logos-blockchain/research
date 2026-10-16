import TokenEconomics.Simulation

/-!
Reproduction of the supply projection of Block Rewards (*Annex*) with the simulator of
`TokenEconomics/Simulation.lean`. Every `#guard` fails the file if it does not hold:

  lake env lean TokenEconomicsTest/Projection.lean
-/

open TokenEconomics.Simulation

namespace TokenEconomics.ProjectionTest

def close (x y tol : Float) : Bool := Float.abs (x - y) ≤ tol

-- Without noise, 3.250% after 10 years, the proven continuous value being 3.247%
-- (`noiseFree_growth`): the steps of half a day and of an epoch add 0.003 points.
#guard close (run 0.0 0.0 1) 0.03250 0.00005
#guard close (run 0.0 0.0 1) 0.03247 0.0005

-- With the annex's noise (0.1 on the stake deviation per epoch, 10% daily on the fees),
-- 20 runs average 3.02% (the annex: 3.00%), from 2.78% to 3.31% (the annex: 2.81% to 3.18%).
#guard close (runs 0.1 0.1 20).1 0.0300 0.0005
#guard close (runs 0.1 0.1 20).2.1 0.0278 0.0001
#guard close (runs 0.1 0.1 20).2.2 0.0331 0.0001

-- The noise of the inferred stake drives the result: half or twice the annex's level moves the
-- mean by about 0.08 and 0.06 points.
#guard close (runs 0.05 0.1 20).1 0.0310 0.0001
#guard close (runs 0.2 0.1 20).1 0.0294 0.0001

end TokenEconomics.ProjectionTest
