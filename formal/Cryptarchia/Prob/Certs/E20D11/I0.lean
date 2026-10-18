module

public import Cryptarchia.Prob.Certs.E20D11.Data
meta import Cryptarchia.Prob.Certs.E20D11.Data

/-! # E20D11: phase indices 0 to 2, their tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post0 : List (List ℤ) := eval% F.postSeeds 0
def pre0 : List (List ℤ) := eval% F.preSeeds 0 post0
def vs0 : List ℤ := eval% F.swSeeds 0
def dat0 : IdxData := ⟨post0, pre0, eval% F.eInList 0 post0, eval% F.eEOf 0 post0 pre0, vs0, eval% F.eSOf 0 vs0⟩
theorem chk0 : F.idxChk 0 dat0 = true := by decide +kernel
def post1 : List (List ℤ) := eval% F.postSeeds 1
def pre1 : List (List ℤ) := eval% F.preSeeds 1 post1
def vs1 : List ℤ := eval% F.swSeeds 1
def dat1 : IdxData := ⟨post1, pre1, eval% F.eInList 1 post1, eval% F.eEOf 1 post1 pre1, vs1, eval% F.eSOf 1 vs1⟩
theorem chk1 : F.idxChk 1 dat1 = true := by decide +kernel
def vs2 : List ℤ := eval% F.swSeeds 2
def dat2 : IdxData := ⟨[], [], [], 0, vs2, eval% F.eSOf 2 vs2⟩
theorem chk2 : F.idxChk 2 dat2 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11
