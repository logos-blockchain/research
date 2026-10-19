module

public import Cryptarchia.Prob.Certs.E20D11G.R32
meta import Cryptarchia.Prob.Certs.E20D11G.R32

/-! # E20D11G: (group, representative) entries 440 to 450, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r40_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 132 (0, 0))
def r40_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 133 (0, 0))
def r40_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 134 (0, 0))
def r40_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 135 (0, 0))
def r40_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 136 (0, 0))
def r40_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 137 (0, 0))
def r40_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 138 (0, 0))
def r40_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 139 (0, 0))
def r40_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 140 (0, 0))
def r40_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 141 (0, 0))
def r40_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 142 (0, 0))

theorem c40_0 : F.repChkAG (Q.tab r40_0.1) γ nG r40_0.1 Rd cst r40_0.2.1 r40_0.2.2 = true := by decide +kernel
theorem c40_1 : F.repChkAG (Q.tab r40_1.1) γ nG r40_1.1 Rd cst r40_1.2.1 r40_1.2.2 = true := by decide +kernel
theorem c40_2 : F.repChkAG (Q.tab r40_2.1) γ nG r40_2.1 Rd cst r40_2.2.1 r40_2.2.2 = true := by decide +kernel
theorem c40_3 : F.repChkAG (Q.tab r40_3.1) γ nG r40_3.1 Rd cst r40_3.2.1 r40_3.2.2 = true := by decide +kernel
theorem c40_4 : F.repChkAG (Q.tab r40_4.1) γ nG r40_4.1 Rd cst r40_4.2.1 r40_4.2.2 = true := by decide +kernel
theorem c40_5 : F.repChkAG (Q.tab r40_5.1) γ nG r40_5.1 Rd cst r40_5.2.1 r40_5.2.2 = true := by decide +kernel
theorem c40_6 : F.repChkAG (Q.tab r40_6.1) γ nG r40_6.1 Rd cst r40_6.2.1 r40_6.2.2 = true := by decide +kernel
theorem c40_7 : F.repChkAG (Q.tab r40_7.1) γ nG r40_7.1 Rd cst r40_7.2.1 r40_7.2.2 = true := by decide +kernel
theorem c40_8 : F.repChkAG (Q.tab r40_8.1) γ nG r40_8.1 Rd cst r40_8.2.1 r40_8.2.2 = true := by decide +kernel
theorem c40_9 : F.repChkAG (Q.tab r40_9.1) γ nG r40_9.1 Rd cst r40_9.2.1 r40_9.2.2 = true := by decide +kernel
theorem c40_10 : F.repChkAG (Q.tab r40_10.1) γ nG r40_10.1 Rd cst r40_10.2.1 r40_10.2.2 = true := by decide +kernel

def D40 : List (ℕ × (ℤ × ℤ) × RepData) := [r40_0, r40_1, r40_2, r40_3, r40_4, r40_5, r40_6, r40_7, r40_8, r40_9, r40_10]

theorem chkA40 : D40.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D40, List.all_cons, List.all_nil, c40_0, c40_1, c40_2, c40_3, c40_4, c40_5, c40_6, c40_7, c40_8, c40_9, c40_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
