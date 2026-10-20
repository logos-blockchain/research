module

public import Cryptarchia.Prob.Certs.E20D11G.R11
meta import Cryptarchia.Prob.Certs.E20D11G.R11

/-! # E20D11G: (group, representative) entries 209 to 219, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r19_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 55 (0, 0))
def r19_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 56 (0, 0))
def r19_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 57 (0, 0))
def r19_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 58 (0, 0))
def r19_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 59 (0, 0))
def r19_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 60 (0, 0))
def r19_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 61 (0, 0))
def r19_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 62 (0, 0))
def r19_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 63 (0, 0))
def r19_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 64 (0, 0))
def r19_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 65 (0, 0))

theorem c19_0 : F.repChkAG (Q.tab r19_0.1) γ nG r19_0.1 Rd cst r19_0.2.1 r19_0.2.2 = true := by decide +kernel
theorem c19_1 : F.repChkAG (Q.tab r19_1.1) γ nG r19_1.1 Rd cst r19_1.2.1 r19_1.2.2 = true := by decide +kernel
theorem c19_2 : F.repChkAG (Q.tab r19_2.1) γ nG r19_2.1 Rd cst r19_2.2.1 r19_2.2.2 = true := by decide +kernel
theorem c19_3 : F.repChkAG (Q.tab r19_3.1) γ nG r19_3.1 Rd cst r19_3.2.1 r19_3.2.2 = true := by decide +kernel
theorem c19_4 : F.repChkAG (Q.tab r19_4.1) γ nG r19_4.1 Rd cst r19_4.2.1 r19_4.2.2 = true := by decide +kernel
theorem c19_5 : F.repChkAG (Q.tab r19_5.1) γ nG r19_5.1 Rd cst r19_5.2.1 r19_5.2.2 = true := by decide +kernel
theorem c19_6 : F.repChkAG (Q.tab r19_6.1) γ nG r19_6.1 Rd cst r19_6.2.1 r19_6.2.2 = true := by decide +kernel
theorem c19_7 : F.repChkAG (Q.tab r19_7.1) γ nG r19_7.1 Rd cst r19_7.2.1 r19_7.2.2 = true := by decide +kernel
theorem c19_8 : F.repChkAG (Q.tab r19_8.1) γ nG r19_8.1 Rd cst r19_8.2.1 r19_8.2.2 = true := by decide +kernel
theorem c19_9 : F.repChkAG (Q.tab r19_9.1) γ nG r19_9.1 Rd cst r19_9.2.1 r19_9.2.2 = true := by decide +kernel
theorem c19_10 : F.repChkAG (Q.tab r19_10.1) γ nG r19_10.1 Rd cst r19_10.2.1 r19_10.2.2 = true := by decide +kernel

def D19 : List (ℕ × (ℤ × ℤ) × RepData) := [r19_0, r19_1, r19_2, r19_3, r19_4, r19_5, r19_6, r19_7, r19_8, r19_9, r19_10]

theorem chkA19 : D19.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D19, List.all_cons, List.all_nil, c19_0, c19_1, c19_2, c19_3, c19_4, c19_5, c19_6, c19_7, c19_8, c19_9, c19_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
