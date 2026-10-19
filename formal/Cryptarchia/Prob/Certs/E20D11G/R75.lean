module

public import Cryptarchia.Prob.Certs.E20D11G.R71
meta import Cryptarchia.Prob.Certs.E20D11G.R71

/-! # E20D11G: (group, representative) entries 825 to 835, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r75_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 33 (0, 0))
def r75_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 34 (0, 0))
def r75_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 35 (0, 0))
def r75_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 36 (0, 0))
def r75_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 37 (0, 0))
def r75_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 38 (0, 0))
def r75_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 39 (0, 0))
def r75_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 40 (0, 0))
def r75_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 41 (0, 0))
def r75_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 42 (0, 0))
def r75_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 43 (0, 0))

theorem c75_0 : F.repChkAG (Q.tab r75_0.1) γ r75_0.2.1 r75_0.2.2 = true := by decide +kernel
theorem c75_1 : F.repChkAG (Q.tab r75_1.1) γ r75_1.2.1 r75_1.2.2 = true := by decide +kernel
theorem c75_2 : F.repChkAG (Q.tab r75_2.1) γ r75_2.2.1 r75_2.2.2 = true := by decide +kernel
theorem c75_3 : F.repChkAG (Q.tab r75_3.1) γ r75_3.2.1 r75_3.2.2 = true := by decide +kernel
theorem c75_4 : F.repChkAG (Q.tab r75_4.1) γ r75_4.2.1 r75_4.2.2 = true := by decide +kernel
theorem c75_5 : F.repChkAG (Q.tab r75_5.1) γ r75_5.2.1 r75_5.2.2 = true := by decide +kernel
theorem c75_6 : F.repChkAG (Q.tab r75_6.1) γ r75_6.2.1 r75_6.2.2 = true := by decide +kernel
theorem c75_7 : F.repChkAG (Q.tab r75_7.1) γ r75_7.2.1 r75_7.2.2 = true := by decide +kernel
theorem c75_8 : F.repChkAG (Q.tab r75_8.1) γ r75_8.2.1 r75_8.2.2 = true := by decide +kernel
theorem c75_9 : F.repChkAG (Q.tab r75_9.1) γ r75_9.2.1 r75_9.2.2 = true := by decide +kernel
theorem c75_10 : F.repChkAG (Q.tab r75_10.1) γ r75_10.2.1 r75_10.2.2 = true := by decide +kernel

def D75 : List (ℕ × (ℤ × ℤ) × RepData) := [r75_0, r75_1, r75_2, r75_3, r75_4, r75_5, r75_6, r75_7, r75_8, r75_9, r75_10]

theorem chkA75 : D75.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D75, List.all_cons, List.all_nil, c75_0, c75_1, c75_2, c75_3, c75_4, c75_5, c75_6, c75_7, c75_8, c75_9, c75_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
