module

public import Cryptarchia.Prob.Certs.E20D11C.Fam
meta import Cryptarchia.Prob.Certs.E20D11C.Fam

/-! # E20D11C: phase index 1, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post1 : List (List ℤ) := eval% F.postSeeds 1
def pre1 : List (List ℤ) := eval% F.preSeeds 1 post1
def vs1 : List ℤ := eval% F.swSeeds 1

def dat1 : IdxData := ⟨post1, pre1, eval% F.eInList 1 post1, eval% F.eEOf 1 post1 pre1, vs1, eval% F.eSOf 1 vs1⟩

theorem chk1 : F.idxChk 1 dat1 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11C
