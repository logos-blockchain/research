module

public import Cryptarchia.Prob.Certs.E20D11G.R74
meta import Cryptarchia.Prob.Certs.E20D11G.R74

/-! # E20D11G: (group, representative) entries 858 to 868, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r78_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 66 (0, 0))
def r78_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 67 (0, 0))
def r78_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 68 (0, 0))
def r78_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 69 (0, 0))
def r78_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 70 (0, 0))
def r78_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 71 (0, 0))
def r78_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 72 (0, 0))
def r78_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 73 (0, 0))
def r78_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 74 (0, 0))
def r78_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 75 (0, 0))
def r78_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 76 (0, 0))

theorem c78_0 : F.repChkAG (Q.tab r78_0.1) γ r78_0.2.1 r78_0.2.2 = true := by decide +kernel
theorem c78_1 : F.repChkAG (Q.tab r78_1.1) γ r78_1.2.1 r78_1.2.2 = true := by decide +kernel
theorem c78_2 : F.repChkAG (Q.tab r78_2.1) γ r78_2.2.1 r78_2.2.2 = true := by decide +kernel
theorem c78_3 : F.repChkAG (Q.tab r78_3.1) γ r78_3.2.1 r78_3.2.2 = true := by decide +kernel
theorem c78_4 : F.repChkAG (Q.tab r78_4.1) γ r78_4.2.1 r78_4.2.2 = true := by decide +kernel
theorem c78_5 : F.repChkAG (Q.tab r78_5.1) γ r78_5.2.1 r78_5.2.2 = true := by decide +kernel
theorem c78_6 : F.repChkAG (Q.tab r78_6.1) γ r78_6.2.1 r78_6.2.2 = true := by decide +kernel
theorem c78_7 : F.repChkAG (Q.tab r78_7.1) γ r78_7.2.1 r78_7.2.2 = true := by decide +kernel
theorem c78_8 : F.repChkAG (Q.tab r78_8.1) γ r78_8.2.1 r78_8.2.2 = true := by decide +kernel
theorem c78_9 : F.repChkAG (Q.tab r78_9.1) γ r78_9.2.1 r78_9.2.2 = true := by decide +kernel
theorem c78_10 : F.repChkAG (Q.tab r78_10.1) γ r78_10.2.1 r78_10.2.2 = true := by decide +kernel

def D78 : List (ℕ × (ℤ × ℤ) × RepData) := [r78_0, r78_1, r78_2, r78_3, r78_4, r78_5, r78_6, r78_7, r78_8, r78_9, r78_10]

theorem chkA78 : D78.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D78, List.all_cons, List.all_nil, c78_0, c78_1, c78_2, c78_3, c78_4, c78_5, c78_6, c78_7, c78_8, c78_9, c78_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
