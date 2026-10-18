module

public import Cryptarchia.Prob.Certs.E20D11M2.Data
meta import Cryptarchia.Prob.Certs.E20D11M2.Data

/-! # E20D11M2: phase indices 3 to 5, their tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11M2

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post3 : List (List ℤ) := eval% F.postSeeds 3
def pre3 : List (List ℤ) := eval% F.preSeeds 3 post3
def dat3 : IdxData := ⟨post3, pre3, eval% F.eInList 3 post3, eval% F.eEOf 3 post3 pre3, [], 0⟩
theorem chk3 : F.idxChk 3 dat3 = true := by decide +kernel
def post4 : List (List ℤ) := eval% F.postSeeds 4
def pre4 : List (List ℤ) := eval% F.preSeeds 4 post4
def dat4 : IdxData := ⟨post4, pre4, eval% F.eInList 4 post4, eval% F.eEOf 4 post4 pre4, [], 0⟩
theorem chk4 : F.idxChk 4 dat4 = true := by decide +kernel
def post5 : List (List ℤ) := eval% F.postSeeds 5
def pre5 : List (List ℤ) := eval% F.preSeeds 5 post5
def dat5 : IdxData := ⟨post5, pre5, eval% F.eInList 5 post5, eval% F.eEOf 5 post5 pre5, [], 0⟩
theorem chk5 : F.idxChk 5 dat5 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11M2
