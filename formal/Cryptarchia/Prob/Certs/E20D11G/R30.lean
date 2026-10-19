module

public import Cryptarchia.Prob.Certs.E20D11G.R22
meta import Cryptarchia.Prob.Certs.E20D11G.R22

/-! # E20D11G: (group, representative) entries 330 to 340, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r30_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 66 (0, 0))
def r30_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 67 (0, 0))
def r30_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 68 (0, 0))
def r30_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 69 (0, 0))
def r30_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 70 (0, 0))
def r30_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 71 (0, 0))
def r30_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 72 (0, 0))
def r30_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 73 (0, 0))
def r30_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 74 (0, 0))
def r30_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 75 (0, 0))
def r30_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 76 (0, 0))

theorem c30_0 : F.repChkAG (Q.tab r30_0.1) γ nG r30_0.1 Rd cst r30_0.2.1 r30_0.2.2 = true := by decide +kernel
theorem c30_1 : F.repChkAG (Q.tab r30_1.1) γ nG r30_1.1 Rd cst r30_1.2.1 r30_1.2.2 = true := by decide +kernel
theorem c30_2 : F.repChkAG (Q.tab r30_2.1) γ nG r30_2.1 Rd cst r30_2.2.1 r30_2.2.2 = true := by decide +kernel
theorem c30_3 : F.repChkAG (Q.tab r30_3.1) γ nG r30_3.1 Rd cst r30_3.2.1 r30_3.2.2 = true := by decide +kernel
theorem c30_4 : F.repChkAG (Q.tab r30_4.1) γ nG r30_4.1 Rd cst r30_4.2.1 r30_4.2.2 = true := by decide +kernel
theorem c30_5 : F.repChkAG (Q.tab r30_5.1) γ nG r30_5.1 Rd cst r30_5.2.1 r30_5.2.2 = true := by decide +kernel
theorem c30_6 : F.repChkAG (Q.tab r30_6.1) γ nG r30_6.1 Rd cst r30_6.2.1 r30_6.2.2 = true := by decide +kernel
theorem c30_7 : F.repChkAG (Q.tab r30_7.1) γ nG r30_7.1 Rd cst r30_7.2.1 r30_7.2.2 = true := by decide +kernel
theorem c30_8 : F.repChkAG (Q.tab r30_8.1) γ nG r30_8.1 Rd cst r30_8.2.1 r30_8.2.2 = true := by decide +kernel
theorem c30_9 : F.repChkAG (Q.tab r30_9.1) γ nG r30_9.1 Rd cst r30_9.2.1 r30_9.2.2 = true := by decide +kernel
theorem c30_10 : F.repChkAG (Q.tab r30_10.1) γ nG r30_10.1 Rd cst r30_10.2.1 r30_10.2.2 = true := by decide +kernel

def D30 : List (ℕ × (ℤ × ℤ) × RepData) := [r30_0, r30_1, r30_2, r30_3, r30_4, r30_5, r30_6, r30_7, r30_8, r30_9, r30_10]

theorem chkA30 : D30.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D30, List.all_cons, List.all_nil, c30_0, c30_1, c30_2, c30_3, c30_4, c30_5, c30_6, c30_7, c30_8, c30_9, c30_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
