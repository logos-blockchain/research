module

public import Cryptarchia.Prob.Certs.E20D11G.R46
meta import Cryptarchia.Prob.Certs.E20D11G.R46

/-! # E20D11G: (group, representative) entries 594 to 604, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r54_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 132 (0, 0))
def r54_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 133 (0, 0))
def r54_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 134 (0, 0))
def r54_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 135 (0, 0))
def r54_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 136 (0, 0))
def r54_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 137 (0, 0))
def r54_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 138 (0, 0))
def r54_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 139 (0, 0))
def r54_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 140 (0, 0))
def r54_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 141 (0, 0))
def r54_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 142 (0, 0))

theorem c54_0 : F.repChkAG (Q.tab r54_0.1) γ nG r54_0.1 Rd cst r54_0.2.1 r54_0.2.2 = true := by decide +kernel
theorem c54_1 : F.repChkAG (Q.tab r54_1.1) γ nG r54_1.1 Rd cst r54_1.2.1 r54_1.2.2 = true := by decide +kernel
theorem c54_2 : F.repChkAG (Q.tab r54_2.1) γ nG r54_2.1 Rd cst r54_2.2.1 r54_2.2.2 = true := by decide +kernel
theorem c54_3 : F.repChkAG (Q.tab r54_3.1) γ nG r54_3.1 Rd cst r54_3.2.1 r54_3.2.2 = true := by decide +kernel
theorem c54_4 : F.repChkAG (Q.tab r54_4.1) γ nG r54_4.1 Rd cst r54_4.2.1 r54_4.2.2 = true := by decide +kernel
theorem c54_5 : F.repChkAG (Q.tab r54_5.1) γ nG r54_5.1 Rd cst r54_5.2.1 r54_5.2.2 = true := by decide +kernel
theorem c54_6 : F.repChkAG (Q.tab r54_6.1) γ nG r54_6.1 Rd cst r54_6.2.1 r54_6.2.2 = true := by decide +kernel
theorem c54_7 : F.repChkAG (Q.tab r54_7.1) γ nG r54_7.1 Rd cst r54_7.2.1 r54_7.2.2 = true := by decide +kernel
theorem c54_8 : F.repChkAG (Q.tab r54_8.1) γ nG r54_8.1 Rd cst r54_8.2.1 r54_8.2.2 = true := by decide +kernel
theorem c54_9 : F.repChkAG (Q.tab r54_9.1) γ nG r54_9.1 Rd cst r54_9.2.1 r54_9.2.2 = true := by decide +kernel
theorem c54_10 : F.repChkAG (Q.tab r54_10.1) γ nG r54_10.1 Rd cst r54_10.2.1 r54_10.2.2 = true := by decide +kernel

def D54 : List (ℕ × (ℤ × ℤ) × RepData) := [r54_0, r54_1, r54_2, r54_3, r54_4, r54_5, r54_6, r54_7, r54_8, r54_9, r54_10]

theorem chkA54 : D54.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D54, List.all_cons, List.all_nil, c54_0, c54_1, c54_2, c54_3, c54_4, c54_5, c54_6, c54_7, c54_8, c54_9, c54_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
