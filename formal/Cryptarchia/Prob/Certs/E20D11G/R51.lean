module

public import Cryptarchia.Prob.Certs.E20D11G.R47
meta import Cryptarchia.Prob.Certs.E20D11G.R47

/-! # E20D11G: (group, representative) entries 561 to 571, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r51_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 33 (0, 0))
def r51_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 34 (0, 0))
def r51_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 35 (0, 0))
def r51_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 36 (0, 0))
def r51_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 37 (0, 0))
def r51_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 38 (0, 0))
def r51_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 39 (0, 0))
def r51_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 40 (0, 0))
def r51_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 41 (0, 0))
def r51_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 42 (0, 0))
def r51_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 43 (0, 0))

theorem c51_0 : F.repChkAG (Q.tab r51_0.1) γ r51_0.2.1 r51_0.2.2 = true := by decide +kernel
theorem c51_1 : F.repChkAG (Q.tab r51_1.1) γ r51_1.2.1 r51_1.2.2 = true := by decide +kernel
theorem c51_2 : F.repChkAG (Q.tab r51_2.1) γ r51_2.2.1 r51_2.2.2 = true := by decide +kernel
theorem c51_3 : F.repChkAG (Q.tab r51_3.1) γ r51_3.2.1 r51_3.2.2 = true := by decide +kernel
theorem c51_4 : F.repChkAG (Q.tab r51_4.1) γ r51_4.2.1 r51_4.2.2 = true := by decide +kernel
theorem c51_5 : F.repChkAG (Q.tab r51_5.1) γ r51_5.2.1 r51_5.2.2 = true := by decide +kernel
theorem c51_6 : F.repChkAG (Q.tab r51_6.1) γ r51_6.2.1 r51_6.2.2 = true := by decide +kernel
theorem c51_7 : F.repChkAG (Q.tab r51_7.1) γ r51_7.2.1 r51_7.2.2 = true := by decide +kernel
theorem c51_8 : F.repChkAG (Q.tab r51_8.1) γ r51_8.2.1 r51_8.2.2 = true := by decide +kernel
theorem c51_9 : F.repChkAG (Q.tab r51_9.1) γ r51_9.2.1 r51_9.2.2 = true := by decide +kernel
theorem c51_10 : F.repChkAG (Q.tab r51_10.1) γ r51_10.2.1 r51_10.2.2 = true := by decide +kernel

def D51 : List (ℕ × (ℤ × ℤ) × RepData) := [r51_0, r51_1, r51_2, r51_3, r51_4, r51_5, r51_6, r51_7, r51_8, r51_9, r51_10]

theorem chkA51 : D51.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D51, List.all_cons, List.all_nil, c51_0, c51_1, c51_2, c51_3, c51_4, c51_5, c51_6, c51_7, c51_8, c51_9, c51_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
