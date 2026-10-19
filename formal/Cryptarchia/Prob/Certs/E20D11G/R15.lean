module

public import Cryptarchia.Prob.Certs.E20D11G.R7
meta import Cryptarchia.Prob.Certs.E20D11G.R7

/-! # E20D11G: (group, representative) entries 165 to 175, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r15_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 11 (0, 0))
def r15_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 12 (0, 0))
def r15_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 13 (0, 0))
def r15_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 14 (0, 0))
def r15_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 15 (0, 0))
def r15_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 16 (0, 0))
def r15_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 17 (0, 0))
def r15_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 18 (0, 0))
def r15_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 19 (0, 0))
def r15_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 20 (0, 0))
def r15_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 21 (0, 0))

theorem c15_0 : F.repChkAG (Q.tab r15_0.1) γ nG r15_0.1 Rd cst r15_0.2.1 r15_0.2.2 = true := by decide +kernel
theorem c15_1 : F.repChkAG (Q.tab r15_1.1) γ nG r15_1.1 Rd cst r15_1.2.1 r15_1.2.2 = true := by decide +kernel
theorem c15_2 : F.repChkAG (Q.tab r15_2.1) γ nG r15_2.1 Rd cst r15_2.2.1 r15_2.2.2 = true := by decide +kernel
theorem c15_3 : F.repChkAG (Q.tab r15_3.1) γ nG r15_3.1 Rd cst r15_3.2.1 r15_3.2.2 = true := by decide +kernel
theorem c15_4 : F.repChkAG (Q.tab r15_4.1) γ nG r15_4.1 Rd cst r15_4.2.1 r15_4.2.2 = true := by decide +kernel
theorem c15_5 : F.repChkAG (Q.tab r15_5.1) γ nG r15_5.1 Rd cst r15_5.2.1 r15_5.2.2 = true := by decide +kernel
theorem c15_6 : F.repChkAG (Q.tab r15_6.1) γ nG r15_6.1 Rd cst r15_6.2.1 r15_6.2.2 = true := by decide +kernel
theorem c15_7 : F.repChkAG (Q.tab r15_7.1) γ nG r15_7.1 Rd cst r15_7.2.1 r15_7.2.2 = true := by decide +kernel
theorem c15_8 : F.repChkAG (Q.tab r15_8.1) γ nG r15_8.1 Rd cst r15_8.2.1 r15_8.2.2 = true := by decide +kernel
theorem c15_9 : F.repChkAG (Q.tab r15_9.1) γ nG r15_9.1 Rd cst r15_9.2.1 r15_9.2.2 = true := by decide +kernel
theorem c15_10 : F.repChkAG (Q.tab r15_10.1) γ nG r15_10.1 Rd cst r15_10.2.1 r15_10.2.2 = true := by decide +kernel

def D15 : List (ℕ × (ℤ × ℤ) × RepData) := [r15_0, r15_1, r15_2, r15_3, r15_4, r15_5, r15_6, r15_7, r15_8, r15_9, r15_10]

theorem chkA15 : D15.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D15, List.all_cons, List.all_nil, c15_0, c15_1, c15_2, c15_3, c15_4, c15_5, c15_6, c15_7, c15_8, c15_9, c15_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
