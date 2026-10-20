module

public import Cryptarchia.Prob.Certs.E20D11G.Data
public import Cryptarchia.Prob.TableSpec
meta import Cryptarchia.Prob.Certs.E20D11G.Data
meta import Cryptarchia.Prob.TableSpec

/-! # E20D11G: the switching tables of phase indices 0, 1, 2 and 17, their seeds and bounds computed at
elaboration time -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def vs0 : List ℤ := eval% F.swSeeds 0
def dat0 : IdxData := ⟨[], [], [], [], 0, vs0, eval% F.eSOf 0 vs0⟩
theorem sw0 : F.idxChkSw 0 dat0 = true := by decide +kernel
def vs1 : List ℤ := eval% F.swSeeds 1
def dat1 : IdxData := ⟨[], [], [], [], 0, vs1, eval% F.eSOf 1 vs1⟩
theorem sw1 : F.idxChkSw 1 dat1 = true := by decide +kernel
def vs2 : List ℤ := eval% F.swSeeds 2
def dat2 : IdxData := ⟨[], [], [], [], 0, vs2, eval% F.eSOf 2 vs2⟩
theorem sw2 : F.idxChkSw 2 dat2 = true := by decide +kernel
def vs17 : List ℤ := eval% F.swSeeds 17
def dat17 : IdxData := ⟨[], [], [], [], 0, vs17, eval% F.eSOf 17 vs17⟩
theorem sw17 : F.idxChkSw 17 dat17 = true := by decide +kernel

end Cryptarchia.Prob.Certs.E20D11G
