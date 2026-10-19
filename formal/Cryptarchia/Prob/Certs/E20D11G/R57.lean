module

public import Cryptarchia.Prob.Certs.E20D11G.R53
meta import Cryptarchia.Prob.Certs.E20D11G.R53

/-! # E20D11G: (group, representative) entries 627 to 637, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r57_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 99 (0, 0))
def r57_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 100 (0, 0))
def r57_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 101 (0, 0))
def r57_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 102 (0, 0))
def r57_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 103 (0, 0))
def r57_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 104 (0, 0))
def r57_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 105 (0, 0))
def r57_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 106 (0, 0))
def r57_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 107 (0, 0))
def r57_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 108 (0, 0))
def r57_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 109 (0, 0))

theorem c57_0 : F.repChkAG (Q.tab r57_0.1) γ r57_0.2.1 r57_0.2.2 = true := by decide +kernel
theorem c57_1 : F.repChkAG (Q.tab r57_1.1) γ r57_1.2.1 r57_1.2.2 = true := by decide +kernel
theorem c57_2 : F.repChkAG (Q.tab r57_2.1) γ r57_2.2.1 r57_2.2.2 = true := by decide +kernel
theorem c57_3 : F.repChkAG (Q.tab r57_3.1) γ r57_3.2.1 r57_3.2.2 = true := by decide +kernel
theorem c57_4 : F.repChkAG (Q.tab r57_4.1) γ r57_4.2.1 r57_4.2.2 = true := by decide +kernel
theorem c57_5 : F.repChkAG (Q.tab r57_5.1) γ r57_5.2.1 r57_5.2.2 = true := by decide +kernel
theorem c57_6 : F.repChkAG (Q.tab r57_6.1) γ r57_6.2.1 r57_6.2.2 = true := by decide +kernel
theorem c57_7 : F.repChkAG (Q.tab r57_7.1) γ r57_7.2.1 r57_7.2.2 = true := by decide +kernel
theorem c57_8 : F.repChkAG (Q.tab r57_8.1) γ r57_8.2.1 r57_8.2.2 = true := by decide +kernel
theorem c57_9 : F.repChkAG (Q.tab r57_9.1) γ r57_9.2.1 r57_9.2.2 = true := by decide +kernel
theorem c57_10 : F.repChkAG (Q.tab r57_10.1) γ r57_10.2.1 r57_10.2.2 = true := by decide +kernel

def D57 : List (ℕ × (ℤ × ℤ) × RepData) := [r57_0, r57_1, r57_2, r57_3, r57_4, r57_5, r57_6, r57_7, r57_8, r57_9, r57_10]

theorem chkA57 : D57.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D57, List.all_cons, List.all_nil, c57_0, c57_1, c57_2, c57_3, c57_4, c57_5, c57_6, c57_7, c57_8, c57_9, c57_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
