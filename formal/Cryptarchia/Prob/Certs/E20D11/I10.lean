module

public import Cryptarchia.Prob.Certs.E20D11.Fam
meta import Cryptarchia.Prob.Certs.E20D11.Fam

/-! # E20D11: phase index 10, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post10 : List (List ℤ) := eval% F.postSeeds 10
def pre10 : List (List ℤ) := eval% F.preSeeds 10 post10

def dat10 : IdxData := ⟨post10, pre10, eval% F.eInList 10 post10, eval% F.eEOf 10 post10 pre10, [], 0⟩

theorem chk10 : F.idxChk 10 dat10 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11
