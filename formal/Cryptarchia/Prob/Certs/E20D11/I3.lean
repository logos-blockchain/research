module

public import Cryptarchia.Prob.Certs.E20D11.Data
meta import Cryptarchia.Prob.Certs.E20D11.Data

/-! # E20D11: phase indices 9 to 11, their tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post9 : List (List ℤ) := eval% F.postSeeds 9
def pre9 : List (List ℤ) := eval% F.preSeeds 9 post9
def dat9 : IdxData := ⟨post9, pre9, eval% F.eInList 9 post9, eval% F.eEOf 9 post9 pre9, [], 0⟩
theorem chk9 : F.idxChk 9 dat9 = true := by decide +kernel
def post10 : List (List ℤ) := eval% F.postSeeds 10
def pre10 : List (List ℤ) := eval% F.preSeeds 10 post10
def dat10 : IdxData := ⟨post10, pre10, eval% F.eInList 10 post10, eval% F.eEOf 10 post10 pre10, [], 0⟩
theorem chk10 : F.idxChk 10 dat10 = true := by decide +kernel
def post11 : List (List ℤ) := eval% F.postSeeds 11
def pre11 : List (List ℤ) := eval% F.preSeeds 11 post11
def dat11 : IdxData := ⟨post11, pre11, eval% F.eInList 11 post11, eval% F.eEOf 11 post11 pre11, [], 0⟩
theorem chk11 : F.idxChk 11 dat11 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11
