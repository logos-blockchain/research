module

public import Cryptarchia.Prob.Certs.E20D11C.Fam
meta import Cryptarchia.Prob.Certs.E20D11C.Fam

/-! # E20D11C: phase index 9, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post9 : List (List ℤ) := eval% F.postSeeds 9
def pre9 : List (List ℤ) := eval% F.preSeeds 9 post9

def dat9 : IdxData := ⟨post9, pre9, eval% F.eInList 9 post9, eval% F.eEOf 9 post9 pre9, [], 0⟩

theorem chk9 : F.idxChk 9 dat9 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11C
