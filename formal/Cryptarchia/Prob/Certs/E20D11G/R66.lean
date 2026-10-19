module

public import Cryptarchia.Prob.Certs.E20D11G.R62
meta import Cryptarchia.Prob.Certs.E20D11G.R62

/-! # E20D11G: (group, representative) entries 726 to 736, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r66_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 198 (0, 0))
def r66_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 199 (0, 0))
def r66_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 200 (0, 0))
def r66_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 201 (0, 0))
def r66_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 202 (0, 0))
def r66_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 203 (0, 0))
def r66_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 204 (0, 0))
def r66_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 205 (0, 0))
def r66_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 206 (0, 0))
def r66_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 207 (0, 0))
def r66_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 208 (0, 0))

theorem c66_0 : F.repChkAG (Q.tab r66_0.1) γ r66_0.2.1 r66_0.2.2 = true := by decide +kernel
theorem c66_1 : F.repChkAG (Q.tab r66_1.1) γ r66_1.2.1 r66_1.2.2 = true := by decide +kernel
theorem c66_2 : F.repChkAG (Q.tab r66_2.1) γ r66_2.2.1 r66_2.2.2 = true := by decide +kernel
theorem c66_3 : F.repChkAG (Q.tab r66_3.1) γ r66_3.2.1 r66_3.2.2 = true := by decide +kernel
theorem c66_4 : F.repChkAG (Q.tab r66_4.1) γ r66_4.2.1 r66_4.2.2 = true := by decide +kernel
theorem c66_5 : F.repChkAG (Q.tab r66_5.1) γ r66_5.2.1 r66_5.2.2 = true := by decide +kernel
theorem c66_6 : F.repChkAG (Q.tab r66_6.1) γ r66_6.2.1 r66_6.2.2 = true := by decide +kernel
theorem c66_7 : F.repChkAG (Q.tab r66_7.1) γ r66_7.2.1 r66_7.2.2 = true := by decide +kernel
theorem c66_8 : F.repChkAG (Q.tab r66_8.1) γ r66_8.2.1 r66_8.2.2 = true := by decide +kernel
theorem c66_9 : F.repChkAG (Q.tab r66_9.1) γ r66_9.2.1 r66_9.2.2 = true := by decide +kernel
theorem c66_10 : F.repChkAG (Q.tab r66_10.1) γ r66_10.2.1 r66_10.2.2 = true := by decide +kernel

def D66 : List (ℕ × (ℤ × ℤ) × RepData) := [r66_0, r66_1, r66_2, r66_3, r66_4, r66_5, r66_6, r66_7, r66_8, r66_9, r66_10]

theorem chkA66 : D66.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D66, List.all_cons, List.all_nil, c66_0, c66_1, c66_2, c66_3, c66_4, c66_5, c66_6, c66_7, c66_8, c66_9, c66_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
