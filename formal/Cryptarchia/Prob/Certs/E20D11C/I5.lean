module

public import Cryptarchia.Prob.Certs.E20D11C.Fam
meta import Cryptarchia.Prob.Certs.E20D11C.Fam

/-! # E20D11C: phase index 5, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post5 : List (List ℤ) := eval% F.postSeeds 5
def pre5 : List (List ℤ) := eval% F.preSeeds 5 post5

def dat5 : IdxData := ⟨post5, pre5, eval% F.eInList 5 post5, eval% F.eEOf 5 post5 pre5, [], 0⟩

theorem chk5 : F.idxChk 5 dat5 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11C
