module

public import Cryptarchia.Prob.Certs.E20D11.Fam
meta import Cryptarchia.Prob.Certs.E20D11.Fam

/-! # E20D11: phase index 0, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post0 : List (List ℤ) := eval% F.postSeeds 0
def pre0 : List (List ℤ) := eval% F.preSeeds 0 post0
def vs0 : List ℤ := eval% F.swSeeds 0

def dat0 : IdxData := ⟨post0, pre0, eval% F.eInList 0 post0, eval% F.eEOf 0 post0 pre0, vs0, eval% F.eSOf 0 vs0⟩

theorem chk0 : F.idxChk 0 dat0 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11
