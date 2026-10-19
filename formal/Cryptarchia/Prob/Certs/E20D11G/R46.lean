module

public import Cryptarchia.Prob.Certs.E20D11G.R38
meta import Cryptarchia.Prob.Certs.E20D11G.R38

/-! # E20D11G: (group, representative) entries 506 to 516, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r46_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 44 (0, 0))
def r46_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 45 (0, 0))
def r46_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 46 (0, 0))
def r46_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 47 (0, 0))
def r46_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 48 (0, 0))
def r46_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 49 (0, 0))
def r46_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 50 (0, 0))
def r46_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 51 (0, 0))
def r46_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 52 (0, 0))
def r46_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 53 (0, 0))
def r46_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 54 (0, 0))

theorem c46_0 : F.repChkAG (Q.tab r46_0.1) γ nG r46_0.1 Rd cst r46_0.2.1 r46_0.2.2 = true := by decide +kernel
theorem c46_1 : F.repChkAG (Q.tab r46_1.1) γ nG r46_1.1 Rd cst r46_1.2.1 r46_1.2.2 = true := by decide +kernel
theorem c46_2 : F.repChkAG (Q.tab r46_2.1) γ nG r46_2.1 Rd cst r46_2.2.1 r46_2.2.2 = true := by decide +kernel
theorem c46_3 : F.repChkAG (Q.tab r46_3.1) γ nG r46_3.1 Rd cst r46_3.2.1 r46_3.2.2 = true := by decide +kernel
theorem c46_4 : F.repChkAG (Q.tab r46_4.1) γ nG r46_4.1 Rd cst r46_4.2.1 r46_4.2.2 = true := by decide +kernel
theorem c46_5 : F.repChkAG (Q.tab r46_5.1) γ nG r46_5.1 Rd cst r46_5.2.1 r46_5.2.2 = true := by decide +kernel
theorem c46_6 : F.repChkAG (Q.tab r46_6.1) γ nG r46_6.1 Rd cst r46_6.2.1 r46_6.2.2 = true := by decide +kernel
theorem c46_7 : F.repChkAG (Q.tab r46_7.1) γ nG r46_7.1 Rd cst r46_7.2.1 r46_7.2.2 = true := by decide +kernel
theorem c46_8 : F.repChkAG (Q.tab r46_8.1) γ nG r46_8.1 Rd cst r46_8.2.1 r46_8.2.2 = true := by decide +kernel
theorem c46_9 : F.repChkAG (Q.tab r46_9.1) γ nG r46_9.1 Rd cst r46_9.2.1 r46_9.2.2 = true := by decide +kernel
theorem c46_10 : F.repChkAG (Q.tab r46_10.1) γ nG r46_10.1 Rd cst r46_10.2.1 r46_10.2.2 = true := by decide +kernel

def D46 : List (ℕ × (ℤ × ℤ) × RepData) := [r46_0, r46_1, r46_2, r46_3, r46_4, r46_5, r46_6, r46_7, r46_8, r46_9, r46_10]

theorem chkA46 : D46.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D46, List.all_cons, List.all_nil, c46_0, c46_1, c46_2, c46_3, c46_4, c46_5, c46_6, c46_7, c46_8, c46_9, c46_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
