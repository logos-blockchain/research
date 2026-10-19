module

public import Cryptarchia.Prob.Certs.E20D11G.R16
meta import Cryptarchia.Prob.Certs.E20D11G.R16

/-! # E20D11G: (group, representative) entries 264 to 274, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r24_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 0 (0, 0))
def r24_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 1 (0, 0))
def r24_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 2 (0, 0))
def r24_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 3 (0, 0))
def r24_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 4 (0, 0))
def r24_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 5 (0, 0))
def r24_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 6 (0, 0))
def r24_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 7 (0, 0))
def r24_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 8 (0, 0))
def r24_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 9 (0, 0))
def r24_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 10 (0, 0))

theorem c24_0 : F.repChkAG (Q.tab r24_0.1) γ nG r24_0.1 Rd cst r24_0.2.1 r24_0.2.2 = true := by decide +kernel
theorem c24_1 : F.repChkAG (Q.tab r24_1.1) γ nG r24_1.1 Rd cst r24_1.2.1 r24_1.2.2 = true := by decide +kernel
theorem c24_2 : F.repChkAG (Q.tab r24_2.1) γ nG r24_2.1 Rd cst r24_2.2.1 r24_2.2.2 = true := by decide +kernel
theorem c24_3 : F.repChkAG (Q.tab r24_3.1) γ nG r24_3.1 Rd cst r24_3.2.1 r24_3.2.2 = true := by decide +kernel
theorem c24_4 : F.repChkAG (Q.tab r24_4.1) γ nG r24_4.1 Rd cst r24_4.2.1 r24_4.2.2 = true := by decide +kernel
theorem c24_5 : F.repChkAG (Q.tab r24_5.1) γ nG r24_5.1 Rd cst r24_5.2.1 r24_5.2.2 = true := by decide +kernel
theorem c24_6 : F.repChkAG (Q.tab r24_6.1) γ nG r24_6.1 Rd cst r24_6.2.1 r24_6.2.2 = true := by decide +kernel
theorem c24_7 : F.repChkAG (Q.tab r24_7.1) γ nG r24_7.1 Rd cst r24_7.2.1 r24_7.2.2 = true := by decide +kernel
theorem c24_8 : F.repChkAG (Q.tab r24_8.1) γ nG r24_8.1 Rd cst r24_8.2.1 r24_8.2.2 = true := by decide +kernel
theorem c24_9 : F.repChkAG (Q.tab r24_9.1) γ nG r24_9.1 Rd cst r24_9.2.1 r24_9.2.2 = true := by decide +kernel
theorem c24_10 : F.repChkAG (Q.tab r24_10.1) γ nG r24_10.1 Rd cst r24_10.2.1 r24_10.2.2 = true := by decide +kernel

def D24 : List (ℕ × (ℤ × ℤ) × RepData) := [r24_0, r24_1, r24_2, r24_3, r24_4, r24_5, r24_6, r24_7, r24_8, r24_9, r24_10]

theorem chkA24 : D24.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D24, List.all_cons, List.all_nil, c24_0, c24_1, c24_2, c24_3, c24_4, c24_5, c24_6, c24_7, c24_8, c24_9, c24_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
