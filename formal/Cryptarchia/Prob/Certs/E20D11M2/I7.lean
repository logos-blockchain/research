module

public import Cryptarchia.Prob.Certs.E20D11M2.Fam
meta import Cryptarchia.Prob.Certs.E20D11M2.Fam

/-! # E20D11M2: phase index 7, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11M2

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post7 : List (List ℤ) := eval% F.postSeeds 7
def pre7 : List (List ℤ) := eval% F.preSeeds 7 post7

def dat7 : IdxData := ⟨post7, pre7, eval% F.eInList 7 post7, eval% F.eEOf 7 post7 pre7, [], 0⟩

theorem chk7 : F.idxChk 7 dat7 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11M2
