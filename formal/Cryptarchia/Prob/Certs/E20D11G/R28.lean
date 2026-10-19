module

public import Cryptarchia.Prob.Certs.E20D11G.R20
meta import Cryptarchia.Prob.Certs.E20D11G.R20

/-! # E20D11G: (group, representative) entries 308 to 318, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r28_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 0 (0, 0))
def r28_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 1 (0, 0))
def r28_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 2 (0, 0))
def r28_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 3 (0, 0))
def r28_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 4 (0, 0))
def r28_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 5 (0, 0))
def r28_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 6 (0, 0))
def r28_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 7 (0, 0))
def r28_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 8 (0, 0))
def r28_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 9 (0, 0))
def r28_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 10 (0, 0))

theorem c28_0 : F.repChkAG (Q.tab r28_0.1) γ nG r28_0.1 Rd cst r28_0.2.1 r28_0.2.2 = true := by decide +kernel
theorem c28_1 : F.repChkAG (Q.tab r28_1.1) γ nG r28_1.1 Rd cst r28_1.2.1 r28_1.2.2 = true := by decide +kernel
theorem c28_2 : F.repChkAG (Q.tab r28_2.1) γ nG r28_2.1 Rd cst r28_2.2.1 r28_2.2.2 = true := by decide +kernel
theorem c28_3 : F.repChkAG (Q.tab r28_3.1) γ nG r28_3.1 Rd cst r28_3.2.1 r28_3.2.2 = true := by decide +kernel
theorem c28_4 : F.repChkAG (Q.tab r28_4.1) γ nG r28_4.1 Rd cst r28_4.2.1 r28_4.2.2 = true := by decide +kernel
theorem c28_5 : F.repChkAG (Q.tab r28_5.1) γ nG r28_5.1 Rd cst r28_5.2.1 r28_5.2.2 = true := by decide +kernel
theorem c28_6 : F.repChkAG (Q.tab r28_6.1) γ nG r28_6.1 Rd cst r28_6.2.1 r28_6.2.2 = true := by decide +kernel
theorem c28_7 : F.repChkAG (Q.tab r28_7.1) γ nG r28_7.1 Rd cst r28_7.2.1 r28_7.2.2 = true := by decide +kernel
theorem c28_8 : F.repChkAG (Q.tab r28_8.1) γ nG r28_8.1 Rd cst r28_8.2.1 r28_8.2.2 = true := by decide +kernel
theorem c28_9 : F.repChkAG (Q.tab r28_9.1) γ nG r28_9.1 Rd cst r28_9.2.1 r28_9.2.2 = true := by decide +kernel
theorem c28_10 : F.repChkAG (Q.tab r28_10.1) γ nG r28_10.1 Rd cst r28_10.2.1 r28_10.2.2 = true := by decide +kernel

def D28 : List (ℕ × (ℤ × ℤ) × RepData) := [r28_0, r28_1, r28_2, r28_3, r28_4, r28_5, r28_6, r28_7, r28_8, r28_9, r28_10]

theorem chkA28 : D28.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D28, List.all_cons, List.all_nil, c28_0, c28_1, c28_2, c28_3, c28_4, c28_5, c28_6, c28_7, c28_8, c28_9, c28_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
