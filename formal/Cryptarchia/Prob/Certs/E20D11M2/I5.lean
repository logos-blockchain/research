module

public import Cryptarchia.Prob.Certs.E20D11M2.Data
meta import Cryptarchia.Prob.Certs.E20D11M2.Data

/-! # E20D11M2: phase indices 15 to 16, their tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11M2

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post15 : List (List ℤ) := eval% F.postSeeds 15
def pre15 : List (List ℤ) := eval% F.preSeeds 15 post15
def dat15 : IdxData := ⟨post15, pre15, eval% F.eInList 15 post15, eval% F.eEOf 15 post15 pre15, [], 0⟩
theorem chk15 : F.idxChk 15 dat15 = true := by decide +kernel
def post16 : List (List ℤ) := eval% F.postSeeds 16
def pre16 : List (List ℤ) := eval% F.preSeeds 16 post16
def dat16 : IdxData := ⟨post16, pre16, eval% F.eInList 16 post16, eval% F.eEOf 16 post16 pre16, [], 0⟩
theorem chk16 : F.idxChk 16 dat16 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11M2
