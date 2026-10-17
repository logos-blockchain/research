module

public import Cryptarchia.Prob.Certs.E20D11C.Fam
meta import Cryptarchia.Prob.Certs.E20D11C.Fam

/-! # E20D11C: phase index 16, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post16 : List (List ℤ) := eval% F.postSeeds 16
def pre16 : List (List ℤ) := eval% F.preSeeds 16 post16

def dat16 : IdxData := ⟨post16, pre16, eval% F.eInList 16 post16, eval% F.eEOf 16 post16 pre16, [], 0⟩

theorem chk16 : F.idxChk 16 dat16 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11C
