module

public import Cryptarchia.Prob.Certs.E20D11G.R68
meta import Cryptarchia.Prob.Certs.E20D11G.R68

/-! # E20D11G: (group, representative) entries 792 to 802, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r72_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 0 (0, 0))
def r72_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 1 (0, 0))
def r72_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 2 (0, 0))
def r72_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 3 (0, 0))
def r72_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 4 (0, 0))
def r72_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 5 (0, 0))
def r72_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 6 (0, 0))
def r72_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 7 (0, 0))
def r72_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 8 (0, 0))
def r72_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 9 (0, 0))
def r72_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 10 (0, 0))

theorem c72_0 : F.repChkAG (Q.tab r72_0.1) γ r72_0.2.1 r72_0.2.2 = true := by decide +kernel
theorem c72_1 : F.repChkAG (Q.tab r72_1.1) γ r72_1.2.1 r72_1.2.2 = true := by decide +kernel
theorem c72_2 : F.repChkAG (Q.tab r72_2.1) γ r72_2.2.1 r72_2.2.2 = true := by decide +kernel
theorem c72_3 : F.repChkAG (Q.tab r72_3.1) γ r72_3.2.1 r72_3.2.2 = true := by decide +kernel
theorem c72_4 : F.repChkAG (Q.tab r72_4.1) γ r72_4.2.1 r72_4.2.2 = true := by decide +kernel
theorem c72_5 : F.repChkAG (Q.tab r72_5.1) γ r72_5.2.1 r72_5.2.2 = true := by decide +kernel
theorem c72_6 : F.repChkAG (Q.tab r72_6.1) γ r72_6.2.1 r72_6.2.2 = true := by decide +kernel
theorem c72_7 : F.repChkAG (Q.tab r72_7.1) γ r72_7.2.1 r72_7.2.2 = true := by decide +kernel
theorem c72_8 : F.repChkAG (Q.tab r72_8.1) γ r72_8.2.1 r72_8.2.2 = true := by decide +kernel
theorem c72_9 : F.repChkAG (Q.tab r72_9.1) γ r72_9.2.1 r72_9.2.2 = true := by decide +kernel
theorem c72_10 : F.repChkAG (Q.tab r72_10.1) γ r72_10.2.1 r72_10.2.2 = true := by decide +kernel

def D72 : List (ℕ × (ℤ × ℤ) × RepData) := [r72_0, r72_1, r72_2, r72_3, r72_4, r72_5, r72_6, r72_7, r72_8, r72_9, r72_10]

theorem chkA72 : D72.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D72, List.all_cons, List.all_nil, c72_0, c72_1, c72_2, c72_3, c72_4, c72_5, c72_6, c72_7, c72_8, c72_9, c72_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
