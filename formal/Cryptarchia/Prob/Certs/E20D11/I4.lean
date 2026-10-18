module

public import Cryptarchia.Prob.Certs.E20D11.Data
meta import Cryptarchia.Prob.Certs.E20D11.Data

/-! # E20D11: phase indices 12 to 14, their tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post12 : List (List ℤ) := eval% F.postSeeds 12
def pre12 : List (List ℤ) := eval% F.preSeeds 12 post12
def dat12 : IdxData := ⟨post12, pre12, eval% F.eInList 12 post12, eval% F.eEOf 12 post12 pre12, [], 0⟩
theorem chk12 : F.idxChk 12 dat12 = true := by decide +kernel
def post13 : List (List ℤ) := eval% F.postSeeds 13
def pre13 : List (List ℤ) := eval% F.preSeeds 13 post13
def dat13 : IdxData := ⟨post13, pre13, eval% F.eInList 13 post13, eval% F.eEOf 13 post13 pre13, [], 0⟩
theorem chk13 : F.idxChk 13 dat13 = true := by decide +kernel
def post14 : List (List ℤ) := eval% F.postSeeds 14
def pre14 : List (List ℤ) := eval% F.preSeeds 14 post14
def dat14 : IdxData := ⟨post14, pre14, eval% F.eInList 14 post14, eval% F.eEOf 14 post14 pre14, [], 0⟩
theorem chk14 : F.idxChk 14 dat14 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11
