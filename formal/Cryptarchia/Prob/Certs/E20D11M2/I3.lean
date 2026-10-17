module

public import Cryptarchia.Prob.Certs.E20D11M2.Fam
meta import Cryptarchia.Prob.Certs.E20D11M2.Fam

/-! # E20D11M2: phase index 3, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11M2

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post3 : List (List ℤ) := eval% F.postSeeds 3
def pre3 : List (List ℤ) := eval% F.preSeeds 3 post3

def dat3 : IdxData := ⟨post3, pre3, eval% F.eInList 3 post3, eval% F.eEOf 3 post3 pre3, [], 0⟩

theorem chk3 : F.idxChk 3 dat3 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11M2
