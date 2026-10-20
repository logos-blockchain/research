module

public import Cryptarchia.Prob.Certs.E20D11G.R34
meta import Cryptarchia.Prob.Certs.E20D11G.R34

/-! # E20D11G: (group, representative) entries 462 to 472, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r42_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 0 (0, 0))
def r42_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 1 (0, 0))
def r42_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 2 (0, 0))
def r42_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 3 (0, 0))
def r42_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 4 (0, 0))
def r42_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 5 (0, 0))
def r42_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 6 (0, 0))
def r42_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 7 (0, 0))
def r42_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 8 (0, 0))
def r42_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 9 (0, 0))
def r42_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 10 (0, 0))

theorem c42_0 : F.repChkAG (Q.tab r42_0.1) γ nG r42_0.1 Rd cst r42_0.2.1 r42_0.2.2 = true := by decide +kernel
theorem c42_1 : F.repChkAG (Q.tab r42_1.1) γ nG r42_1.1 Rd cst r42_1.2.1 r42_1.2.2 = true := by decide +kernel
theorem c42_2 : F.repChkAG (Q.tab r42_2.1) γ nG r42_2.1 Rd cst r42_2.2.1 r42_2.2.2 = true := by decide +kernel
theorem c42_3 : F.repChkAG (Q.tab r42_3.1) γ nG r42_3.1 Rd cst r42_3.2.1 r42_3.2.2 = true := by decide +kernel
theorem c42_4 : F.repChkAG (Q.tab r42_4.1) γ nG r42_4.1 Rd cst r42_4.2.1 r42_4.2.2 = true := by decide +kernel
theorem c42_5 : F.repChkAG (Q.tab r42_5.1) γ nG r42_5.1 Rd cst r42_5.2.1 r42_5.2.2 = true := by decide +kernel
theorem c42_6 : F.repChkAG (Q.tab r42_6.1) γ nG r42_6.1 Rd cst r42_6.2.1 r42_6.2.2 = true := by decide +kernel
theorem c42_7 : F.repChkAG (Q.tab r42_7.1) γ nG r42_7.1 Rd cst r42_7.2.1 r42_7.2.2 = true := by decide +kernel
theorem c42_8 : F.repChkAG (Q.tab r42_8.1) γ nG r42_8.1 Rd cst r42_8.2.1 r42_8.2.2 = true := by decide +kernel
theorem c42_9 : F.repChkAG (Q.tab r42_9.1) γ nG r42_9.1 Rd cst r42_9.2.1 r42_9.2.2 = true := by decide +kernel
theorem c42_10 : F.repChkAG (Q.tab r42_10.1) γ nG r42_10.1 Rd cst r42_10.2.1 r42_10.2.2 = true := by decide +kernel

def D42 : List (ℕ × (ℤ × ℤ) × RepData) := [r42_0, r42_1, r42_2, r42_3, r42_4, r42_5, r42_6, r42_7, r42_8, r42_9, r42_10]

theorem chkA42 : D42.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D42, List.all_cons, List.all_nil, c42_0, c42_1, c42_2, c42_3, c42_4, c42_5, c42_6, c42_7, c42_8, c42_9, c42_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
