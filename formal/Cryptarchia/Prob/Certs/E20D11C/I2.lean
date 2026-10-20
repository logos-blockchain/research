module

public import Cryptarchia.Prob.Certs.E20D11C.Data
meta import Cryptarchia.Prob.Certs.E20D11C.Data

/-! # E20D11C: phase indices 6 to 8, their tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def post6 : List (List ℤ) := eval% F.postSeeds 6
def pre6 : List (List ℤ) := eval% F.preSeeds 6 post6
def dat6 : IdxData := ⟨eval% F.postRows 6 post6, eval% F.preRows 6 post6 pre6, eval% F.vmaxRows 6 post6,
  eval% F.eInList 6 post6, eval% F.eEOf 6 post6 pre6, [], 0⟩
theorem chk6 : F.idxChk 6 dat6 = true := by decide +kernel
def post7 : List (List ℤ) := eval% F.postSeeds 7
def pre7 : List (List ℤ) := eval% F.preSeeds 7 post7
def dat7 : IdxData := ⟨eval% F.postRows 7 post7, eval% F.preRows 7 post7 pre7, eval% F.vmaxRows 7 post7,
  eval% F.eInList 7 post7, eval% F.eEOf 7 post7 pre7, [], 0⟩
theorem chk7 : F.idxChk 7 dat7 = true := by decide +kernel
def post8 : List (List ℤ) := eval% F.postSeeds 8
def pre8 : List (List ℤ) := eval% F.preSeeds 8 post8
def dat8 : IdxData := ⟨eval% F.postRows 8 post8, eval% F.preRows 8 post8 pre8, eval% F.vmaxRows 8 post8,
  eval% F.eInList 8 post8, eval% F.eEOf 8 post8 pre8, [], 0⟩
theorem chk8 : F.idxChk 8 dat8 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11C
