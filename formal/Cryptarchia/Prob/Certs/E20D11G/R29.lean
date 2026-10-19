module

public import Cryptarchia.Prob.Certs.E20D11G.R21
meta import Cryptarchia.Prob.Certs.E20D11G.R21

/-! # E20D11G: (group, representative) entries 319 to 329, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r29_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 11 (0, 0))
def r29_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 12 (0, 0))
def r29_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 13 (0, 0))
def r29_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 14 (0, 0))
def r29_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 15 (0, 0))
def r29_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 16 (0, 0))
def r29_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 17 (0, 0))
def r29_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 18 (0, 0))
def r29_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 19 (0, 0))
def r29_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 20 (0, 0))
def r29_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 21 (0, 0))

theorem c29_0 : F.repChkAG (Q.tab r29_0.1) γ nG r29_0.1 Rd cst r29_0.2.1 r29_0.2.2 = true := by decide +kernel
theorem c29_1 : F.repChkAG (Q.tab r29_1.1) γ nG r29_1.1 Rd cst r29_1.2.1 r29_1.2.2 = true := by decide +kernel
theorem c29_2 : F.repChkAG (Q.tab r29_2.1) γ nG r29_2.1 Rd cst r29_2.2.1 r29_2.2.2 = true := by decide +kernel
theorem c29_3 : F.repChkAG (Q.tab r29_3.1) γ nG r29_3.1 Rd cst r29_3.2.1 r29_3.2.2 = true := by decide +kernel
theorem c29_4 : F.repChkAG (Q.tab r29_4.1) γ nG r29_4.1 Rd cst r29_4.2.1 r29_4.2.2 = true := by decide +kernel
theorem c29_5 : F.repChkAG (Q.tab r29_5.1) γ nG r29_5.1 Rd cst r29_5.2.1 r29_5.2.2 = true := by decide +kernel
theorem c29_6 : F.repChkAG (Q.tab r29_6.1) γ nG r29_6.1 Rd cst r29_6.2.1 r29_6.2.2 = true := by decide +kernel
theorem c29_7 : F.repChkAG (Q.tab r29_7.1) γ nG r29_7.1 Rd cst r29_7.2.1 r29_7.2.2 = true := by decide +kernel
theorem c29_8 : F.repChkAG (Q.tab r29_8.1) γ nG r29_8.1 Rd cst r29_8.2.1 r29_8.2.2 = true := by decide +kernel
theorem c29_9 : F.repChkAG (Q.tab r29_9.1) γ nG r29_9.1 Rd cst r29_9.2.1 r29_9.2.2 = true := by decide +kernel
theorem c29_10 : F.repChkAG (Q.tab r29_10.1) γ nG r29_10.1 Rd cst r29_10.2.1 r29_10.2.2 = true := by decide +kernel

def D29 : List (ℕ × (ℤ × ℤ) × RepData) := [r29_0, r29_1, r29_2, r29_3, r29_4, r29_5, r29_6, r29_7, r29_8, r29_9, r29_10]

theorem chkA29 : D29.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D29, List.all_cons, List.all_nil, c29_0, c29_1, c29_2, c29_3, c29_4, c29_5, c29_6, c29_7, c29_8, c29_9, c29_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
