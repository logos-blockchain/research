module

public import Cryptarchia.Prob.Certs.E20D11G.R56
meta import Cryptarchia.Prob.Certs.E20D11G.R56

/-! # E20D11G: (group, representative) entries 660 to 670, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r60_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 132 (0, 0))
def r60_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 133 (0, 0))
def r60_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 134 (0, 0))
def r60_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 135 (0, 0))
def r60_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 136 (0, 0))
def r60_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 137 (0, 0))
def r60_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 138 (0, 0))
def r60_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 139 (0, 0))
def r60_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 140 (0, 0))
def r60_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 141 (0, 0))
def r60_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 142 (0, 0))

theorem c60_0 : F.repChkAG (Q.tab r60_0.1) γ r60_0.2.1 r60_0.2.2 = true := by decide +kernel
theorem c60_1 : F.repChkAG (Q.tab r60_1.1) γ r60_1.2.1 r60_1.2.2 = true := by decide +kernel
theorem c60_2 : F.repChkAG (Q.tab r60_2.1) γ r60_2.2.1 r60_2.2.2 = true := by decide +kernel
theorem c60_3 : F.repChkAG (Q.tab r60_3.1) γ r60_3.2.1 r60_3.2.2 = true := by decide +kernel
theorem c60_4 : F.repChkAG (Q.tab r60_4.1) γ r60_4.2.1 r60_4.2.2 = true := by decide +kernel
theorem c60_5 : F.repChkAG (Q.tab r60_5.1) γ r60_5.2.1 r60_5.2.2 = true := by decide +kernel
theorem c60_6 : F.repChkAG (Q.tab r60_6.1) γ r60_6.2.1 r60_6.2.2 = true := by decide +kernel
theorem c60_7 : F.repChkAG (Q.tab r60_7.1) γ r60_7.2.1 r60_7.2.2 = true := by decide +kernel
theorem c60_8 : F.repChkAG (Q.tab r60_8.1) γ r60_8.2.1 r60_8.2.2 = true := by decide +kernel
theorem c60_9 : F.repChkAG (Q.tab r60_9.1) γ r60_9.2.1 r60_9.2.2 = true := by decide +kernel
theorem c60_10 : F.repChkAG (Q.tab r60_10.1) γ r60_10.2.1 r60_10.2.2 = true := by decide +kernel

def D60 : List (ℕ × (ℤ × ℤ) × RepData) := [r60_0, r60_1, r60_2, r60_3, r60_4, r60_5, r60_6, r60_7, r60_8, r60_9, r60_10]

theorem chkA60 : D60.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D60, List.all_cons, List.all_nil, c60_0, c60_1, c60_2, c60_3, c60_4, c60_5, c60_6, c60_7, c60_8, c60_9, c60_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
