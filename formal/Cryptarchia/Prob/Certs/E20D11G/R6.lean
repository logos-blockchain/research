module

public import Cryptarchia.Prob.Certs.E20D11G.R2
meta import Cryptarchia.Prob.Certs.E20D11G.R2

/-! # E20D11G: (group, representative) entries 66 to 76, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r6_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 66 (0, 0))
def r6_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 67 (0, 0))
def r6_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 68 (0, 0))
def r6_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 69 (0, 0))
def r6_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 70 (0, 0))
def r6_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 71 (0, 0))
def r6_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 72 (0, 0))
def r6_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 73 (0, 0))
def r6_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 74 (0, 0))
def r6_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 75 (0, 0))
def r6_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 76 (0, 0))

theorem c6_0 : F.repChkAG (Q.tab r6_0.1) γ r6_0.2.1 r6_0.2.2 = true := by decide +kernel
theorem c6_1 : F.repChkAG (Q.tab r6_1.1) γ r6_1.2.1 r6_1.2.2 = true := by decide +kernel
theorem c6_2 : F.repChkAG (Q.tab r6_2.1) γ r6_2.2.1 r6_2.2.2 = true := by decide +kernel
theorem c6_3 : F.repChkAG (Q.tab r6_3.1) γ r6_3.2.1 r6_3.2.2 = true := by decide +kernel
theorem c6_4 : F.repChkAG (Q.tab r6_4.1) γ r6_4.2.1 r6_4.2.2 = true := by decide +kernel
theorem c6_5 : F.repChkAG (Q.tab r6_5.1) γ r6_5.2.1 r6_5.2.2 = true := by decide +kernel
theorem c6_6 : F.repChkAG (Q.tab r6_6.1) γ r6_6.2.1 r6_6.2.2 = true := by decide +kernel
theorem c6_7 : F.repChkAG (Q.tab r6_7.1) γ r6_7.2.1 r6_7.2.2 = true := by decide +kernel
theorem c6_8 : F.repChkAG (Q.tab r6_8.1) γ r6_8.2.1 r6_8.2.2 = true := by decide +kernel
theorem c6_9 : F.repChkAG (Q.tab r6_9.1) γ r6_9.2.1 r6_9.2.2 = true := by decide +kernel
theorem c6_10 : F.repChkAG (Q.tab r6_10.1) γ r6_10.2.1 r6_10.2.2 = true := by decide +kernel

def D6 : List (ℕ × (ℤ × ℤ) × RepData) := [r6_0, r6_1, r6_2, r6_3, r6_4, r6_5, r6_6, r6_7, r6_8, r6_9, r6_10]

theorem chkA6 : D6.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D6, List.all_cons, List.all_nil, c6_0, c6_1, c6_2, c6_3, c6_4, c6_5, c6_6, c6_7, c6_8, c6_9, c6_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
