module

public import Cryptarchia.Prob.Certs.E20D11M2.Fam
meta import Cryptarchia.Prob.Certs.E20D11M2.Fam

/-! # E20D11M2: phase index 18, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11M2

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post18 : List (List ℤ) := eval% F.postSeeds 18
def pre18 : List (List ℤ) := eval% F.preSeeds 18 post18

def dat18 : IdxData := ⟨post18, pre18, eval% F.eInList 18 post18, eval% F.eEOf 18 post18 pre18, [], 0⟩

theorem chk18 : F.idxChk 18 dat18 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11M2
