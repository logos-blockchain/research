module

public import Cryptarchia.Prob.Certs.E20D11C.Fam
meta import Cryptarchia.Prob.Certs.E20D11C.Fam

/-! # E20D11C: phase index 13, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post13 : List (List ℤ) := eval% F.postSeeds 13
def pre13 : List (List ℤ) := eval% F.preSeeds 13 post13

def dat13 : IdxData := ⟨post13, pre13, eval% F.eInList 13 post13, eval% F.eEOf 13 post13 pre13, [], 0⟩

theorem chk13 : F.idxChk 13 dat13 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11C
