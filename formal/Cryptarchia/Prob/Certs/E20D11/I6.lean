module

public import Cryptarchia.Prob.Certs.E20D11.Fam
meta import Cryptarchia.Prob.Certs.E20D11.Fam

/-! # E20D11: phase index 6, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post6 : List (List ℤ) := eval% F.postSeeds 6
def pre6 : List (List ℤ) := eval% F.preSeeds 6 post6

def dat6 : IdxData := ⟨post6, pre6, eval% F.eInList 6 post6, eval% F.eEOf 6 post6 pre6, [], 0⟩

theorem chk6 : F.idxChk 6 dat6 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11
