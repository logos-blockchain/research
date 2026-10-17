module

public import Cryptarchia.Prob.Certs.E20D11C.Fam
meta import Cryptarchia.Prob.Certs.E20D11C.Fam

/-! # E20D11C: phase index 2, its tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def vs2 : List ℤ := eval% F.swSeeds 2

def dat2 : IdxData := ⟨[], [], [], 0, vs2, eval% F.eSOf 2 vs2⟩

theorem chk2 : F.idxChk 2 dat2 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11C
