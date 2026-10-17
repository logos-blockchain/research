module

public import Cryptarchia.Prob.Certs.E20D11.Fam
meta import Cryptarchia.Prob.Certs.E20D11.Fam

/-! # E20D11: phase index 15, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post15 : List (List ℤ) := eval% F.postSeeds 15
def pre15 : List (List ℤ) := eval% F.preSeeds 15 post15

def dat15 : IdxData := ⟨post15, pre15, eval% F.eInList 15 post15, eval% F.eEOf 15 post15 pre15, [], 0⟩

theorem chk15 : F.idxChk 15 dat15 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11
