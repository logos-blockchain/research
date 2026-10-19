module

public import Cryptarchia.Prob.Certs.E20D11G.R27
meta import Cryptarchia.Prob.Certs.E20D11G.R27

/-! # E20D11G: (group, representative) entries 385 to 395, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r35_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 77 (0, 0))
def r35_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 78 (0, 0))
def r35_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 79 (0, 0))
def r35_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 80 (0, 0))
def r35_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 81 (0, 0))
def r35_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 82 (0, 0))
def r35_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 83 (0, 0))
def r35_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 84 (0, 0))
def r35_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 85 (0, 0))
def r35_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 86 (0, 0))
def r35_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 87 (0, 0))

theorem c35_0 : F.repChkAG (Q.tab r35_0.1) γ nG r35_0.1 Rd cst r35_0.2.1 r35_0.2.2 = true := by decide +kernel
theorem c35_1 : F.repChkAG (Q.tab r35_1.1) γ nG r35_1.1 Rd cst r35_1.2.1 r35_1.2.2 = true := by decide +kernel
theorem c35_2 : F.repChkAG (Q.tab r35_2.1) γ nG r35_2.1 Rd cst r35_2.2.1 r35_2.2.2 = true := by decide +kernel
theorem c35_3 : F.repChkAG (Q.tab r35_3.1) γ nG r35_3.1 Rd cst r35_3.2.1 r35_3.2.2 = true := by decide +kernel
theorem c35_4 : F.repChkAG (Q.tab r35_4.1) γ nG r35_4.1 Rd cst r35_4.2.1 r35_4.2.2 = true := by decide +kernel
theorem c35_5 : F.repChkAG (Q.tab r35_5.1) γ nG r35_5.1 Rd cst r35_5.2.1 r35_5.2.2 = true := by decide +kernel
theorem c35_6 : F.repChkAG (Q.tab r35_6.1) γ nG r35_6.1 Rd cst r35_6.2.1 r35_6.2.2 = true := by decide +kernel
theorem c35_7 : F.repChkAG (Q.tab r35_7.1) γ nG r35_7.1 Rd cst r35_7.2.1 r35_7.2.2 = true := by decide +kernel
theorem c35_8 : F.repChkAG (Q.tab r35_8.1) γ nG r35_8.1 Rd cst r35_8.2.1 r35_8.2.2 = true := by decide +kernel
theorem c35_9 : F.repChkAG (Q.tab r35_9.1) γ nG r35_9.1 Rd cst r35_9.2.1 r35_9.2.2 = true := by decide +kernel
theorem c35_10 : F.repChkAG (Q.tab r35_10.1) γ nG r35_10.1 Rd cst r35_10.2.1 r35_10.2.2 = true := by decide +kernel

def D35 : List (ℕ × (ℤ × ℤ) × RepData) := [r35_0, r35_1, r35_2, r35_3, r35_4, r35_5, r35_6, r35_7, r35_8, r35_9, r35_10]

theorem chkA35 : D35.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D35, List.all_cons, List.all_nil, c35_0, c35_1, c35_2, c35_3, c35_4, c35_5, c35_6, c35_7, c35_8, c35_9, c35_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
