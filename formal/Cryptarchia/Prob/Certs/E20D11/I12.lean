module

public import Cryptarchia.Prob.Certs.E20D11.Fam
meta import Cryptarchia.Prob.Certs.E20D11.Fam

/-! # E20D11: phase index 12, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post12 : List (List ℤ) := eval% F.postSeeds 12
def pre12 : List (List ℤ) := eval% F.preSeeds 12 post12

def dat12 : IdxData := ⟨post12, pre12, eval% F.eInList 12 post12, eval% F.eEOf 12 post12 pre12, [], 0⟩

theorem chk12 : F.idxChk 12 dat12 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11
