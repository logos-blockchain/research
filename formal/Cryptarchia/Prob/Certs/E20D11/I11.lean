module

public import Cryptarchia.Prob.Certs.E20D11.Fam
meta import Cryptarchia.Prob.Certs.E20D11.Fam

/-! # E20D11: phase index 11, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post11 : List (List ℤ) := eval% F.postSeeds 11
def pre11 : List (List ℤ) := eval% F.preSeeds 11 post11

def dat11 : IdxData := ⟨post11, pre11, eval% F.eInList 11 post11, eval% F.eEOf 11 post11 pre11, [], 0⟩

theorem chk11 : F.idxChk 11 dat11 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11
