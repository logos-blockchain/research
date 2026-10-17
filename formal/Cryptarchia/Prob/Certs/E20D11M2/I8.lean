module

public import Cryptarchia.Prob.Certs.E20D11M2.Fam
meta import Cryptarchia.Prob.Certs.E20D11M2.Fam

/-! # E20D11M2: phase index 8, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11M2

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post8 : List (List ℤ) := eval% F.postSeeds 8
def pre8 : List (List ℤ) := eval% F.preSeeds 8 post8

def dat8 : IdxData := ⟨post8, pre8, eval% F.eInList 8 post8, eval% F.eEOf 8 post8 pre8, [], 0⟩

theorem chk8 : F.idxChk 8 dat8 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11M2
