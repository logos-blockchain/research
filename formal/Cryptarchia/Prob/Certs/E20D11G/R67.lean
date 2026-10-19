module

public import Cryptarchia.Prob.Certs.E20D11G.R59
meta import Cryptarchia.Prob.Certs.E20D11G.R59

/-! # E20D11G: (group, representative) entries 737 to 747, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r67_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 209 (0, 0))
def r67_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 210 (0, 0))
def r67_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 211 (0, 0))
def r67_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 212 (0, 0))
def r67_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 213 (0, 0))
def r67_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 214 (0, 0))
def r67_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 215 (0, 0))
def r67_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 216 (0, 0))
def r67_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 217 (0, 0))
def r67_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 218 (0, 0))
def r67_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 219 (0, 0))

theorem c67_0 : F.repChkAG (Q.tab r67_0.1) γ nG r67_0.1 Rd cst r67_0.2.1 r67_0.2.2 = true := by decide +kernel
theorem c67_1 : F.repChkAG (Q.tab r67_1.1) γ nG r67_1.1 Rd cst r67_1.2.1 r67_1.2.2 = true := by decide +kernel
theorem c67_2 : F.repChkAG (Q.tab r67_2.1) γ nG r67_2.1 Rd cst r67_2.2.1 r67_2.2.2 = true := by decide +kernel
theorem c67_3 : F.repChkAG (Q.tab r67_3.1) γ nG r67_3.1 Rd cst r67_3.2.1 r67_3.2.2 = true := by decide +kernel
theorem c67_4 : F.repChkAG (Q.tab r67_4.1) γ nG r67_4.1 Rd cst r67_4.2.1 r67_4.2.2 = true := by decide +kernel
theorem c67_5 : F.repChkAG (Q.tab r67_5.1) γ nG r67_5.1 Rd cst r67_5.2.1 r67_5.2.2 = true := by decide +kernel
theorem c67_6 : F.repChkAG (Q.tab r67_6.1) γ nG r67_6.1 Rd cst r67_6.2.1 r67_6.2.2 = true := by decide +kernel
theorem c67_7 : F.repChkAG (Q.tab r67_7.1) γ nG r67_7.1 Rd cst r67_7.2.1 r67_7.2.2 = true := by decide +kernel
theorem c67_8 : F.repChkAG (Q.tab r67_8.1) γ nG r67_8.1 Rd cst r67_8.2.1 r67_8.2.2 = true := by decide +kernel
theorem c67_9 : F.repChkAG (Q.tab r67_9.1) γ nG r67_9.1 Rd cst r67_9.2.1 r67_9.2.2 = true := by decide +kernel
theorem c67_10 : F.repChkAG (Q.tab r67_10.1) γ nG r67_10.1 Rd cst r67_10.2.1 r67_10.2.2 = true := by decide +kernel

def D67 : List (ℕ × (ℤ × ℤ) × RepData) := [r67_0, r67_1, r67_2, r67_3, r67_4, r67_5, r67_6, r67_7, r67_8, r67_9, r67_10]

theorem chkA67 : D67.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D67, List.all_cons, List.all_nil, c67_0, c67_1, c67_2, c67_3, c67_4, c67_5, c67_6, c67_7, c67_8, c67_9, c67_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
