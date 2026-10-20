module

public import Cryptarchia.Prob.Certs.E20D11C.Data
meta import Cryptarchia.Prob.Certs.E20D11C.Data

/-! # E20D11C: phase indices 17 to 18, their tables' seeds and bounds computed at elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11C

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def vs17 : List ℤ := eval% F.swSeeds 17
def dat17 : IdxData := ⟨[], [], [], [], 0, vs17, eval% F.eSOf 17 vs17⟩
theorem chk17 : F.idxChk 17 dat17 = true := by decide +kernel
def post18 : List (List ℤ) := eval% F.postSeeds 18
def pre18 : List (List ℤ) := eval% F.preSeeds 18 post18
def dat18 : IdxData := ⟨eval% F.postRows 18 post18, eval% F.preRows 18 post18 pre18, eval% F.vmaxRows 18 post18,
  eval% F.eInList 18 post18, eval% F.eEOf 18 post18 pre18, [], 0⟩
theorem chk18 : F.idxChk 18 dat18 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11C
