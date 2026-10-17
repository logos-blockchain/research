module

public import Cryptarchia.Prob.Certs.E20D11.Fam
meta import Cryptarchia.Prob.Certs.E20D11.Fam

/-! # E20D11: phase index 17, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def vs17 : List ℤ := eval% F.swSeeds 17

def dat17 : IdxData := ⟨[], [], [], 0, vs17, eval% F.eSOf 17 vs17⟩

theorem chk17 : F.idxChk 17 dat17 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11
