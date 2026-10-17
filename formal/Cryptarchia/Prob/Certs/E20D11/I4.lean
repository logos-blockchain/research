module

public import Cryptarchia.Prob.Certs.E20D11.Fam
meta import Cryptarchia.Prob.Certs.E20D11.Fam

/-! # E20D11: phase index 4, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post4 : List (List ℤ) := eval% F.postSeeds 4
def pre4 : List (List ℤ) := eval% F.preSeeds 4 post4

def dat4 : IdxData := ⟨post4, pre4, eval% F.eInList 4 post4, eval% F.eEOf 4 post4 pre4, [], 0⟩

theorem chk4 : F.idxChk 4 dat4 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11
