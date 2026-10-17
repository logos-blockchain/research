module

public import Cryptarchia.Prob.Certs.E20D11.Fam
meta import Cryptarchia.Prob.Certs.E20D11.Fam

/-! # E20D11: phase index 14, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post14 : List (List ℤ) := eval% F.postSeeds 14
def pre14 : List (List ℤ) := eval% F.preSeeds 14 post14

def dat14 : IdxData := ⟨post14, pre14, eval% F.eInList 14 post14, eval% F.eEOf 14 post14 pre14, [], 0⟩

theorem chk14 : F.idxChk 14 dat14 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11
