module

public import Cryptarchia.Prob.Certs.E20D11G.Tab
meta import Cryptarchia.Prob.Certs.E20D11G.Tab

/-! # E20D11G: (group, representative) entries 33 to 43, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r3_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 33 (0, 0))
def r3_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 34 (0, 0))
def r3_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 35 (0, 0))
def r3_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 36 (0, 0))
def r3_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 37 (0, 0))
def r3_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 38 (0, 0))
def r3_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 39 (0, 0))
def r3_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 40 (0, 0))
def r3_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 41 (0, 0))
def r3_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 42 (0, 0))
def r3_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 43 (0, 0))

theorem c3_0 : F.repChkAG (Q.tab r3_0.1) γ r3_0.2.1 r3_0.2.2 = true := by decide +kernel
theorem c3_1 : F.repChkAG (Q.tab r3_1.1) γ r3_1.2.1 r3_1.2.2 = true := by decide +kernel
theorem c3_2 : F.repChkAG (Q.tab r3_2.1) γ r3_2.2.1 r3_2.2.2 = true := by decide +kernel
theorem c3_3 : F.repChkAG (Q.tab r3_3.1) γ r3_3.2.1 r3_3.2.2 = true := by decide +kernel
theorem c3_4 : F.repChkAG (Q.tab r3_4.1) γ r3_4.2.1 r3_4.2.2 = true := by decide +kernel
theorem c3_5 : F.repChkAG (Q.tab r3_5.1) γ r3_5.2.1 r3_5.2.2 = true := by decide +kernel
theorem c3_6 : F.repChkAG (Q.tab r3_6.1) γ r3_6.2.1 r3_6.2.2 = true := by decide +kernel
theorem c3_7 : F.repChkAG (Q.tab r3_7.1) γ r3_7.2.1 r3_7.2.2 = true := by decide +kernel
theorem c3_8 : F.repChkAG (Q.tab r3_8.1) γ r3_8.2.1 r3_8.2.2 = true := by decide +kernel
theorem c3_9 : F.repChkAG (Q.tab r3_9.1) γ r3_9.2.1 r3_9.2.2 = true := by decide +kernel
theorem c3_10 : F.repChkAG (Q.tab r3_10.1) γ r3_10.2.1 r3_10.2.2 = true := by decide +kernel

def D3 : List (ℕ × (ℤ × ℤ) × RepData) := [r3_0, r3_1, r3_2, r3_3, r3_4, r3_5, r3_6, r3_7, r3_8, r3_9, r3_10]

theorem chkA3 : D3.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D3, List.all_cons, List.all_nil, c3_0, c3_1, c3_2, c3_3, c3_4, c3_5, c3_6, c3_7, c3_8, c3_9, c3_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
