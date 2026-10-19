module

public import Cryptarchia.Prob.Certs.E20D11G.R45
meta import Cryptarchia.Prob.Certs.E20D11G.R45

/-! # E20D11G: (group, representative) entries 539 to 549, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r49_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 11 (0, 0))
def r49_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 12 (0, 0))
def r49_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 13 (0, 0))
def r49_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 14 (0, 0))
def r49_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 15 (0, 0))
def r49_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 16 (0, 0))
def r49_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 17 (0, 0))
def r49_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 18 (0, 0))
def r49_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 19 (0, 0))
def r49_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 20 (0, 0))
def r49_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 21 (0, 0))

theorem c49_0 : F.repChkAG (Q.tab r49_0.1) γ r49_0.2.1 r49_0.2.2 = true := by decide +kernel
theorem c49_1 : F.repChkAG (Q.tab r49_1.1) γ r49_1.2.1 r49_1.2.2 = true := by decide +kernel
theorem c49_2 : F.repChkAG (Q.tab r49_2.1) γ r49_2.2.1 r49_2.2.2 = true := by decide +kernel
theorem c49_3 : F.repChkAG (Q.tab r49_3.1) γ r49_3.2.1 r49_3.2.2 = true := by decide +kernel
theorem c49_4 : F.repChkAG (Q.tab r49_4.1) γ r49_4.2.1 r49_4.2.2 = true := by decide +kernel
theorem c49_5 : F.repChkAG (Q.tab r49_5.1) γ r49_5.2.1 r49_5.2.2 = true := by decide +kernel
theorem c49_6 : F.repChkAG (Q.tab r49_6.1) γ r49_6.2.1 r49_6.2.2 = true := by decide +kernel
theorem c49_7 : F.repChkAG (Q.tab r49_7.1) γ r49_7.2.1 r49_7.2.2 = true := by decide +kernel
theorem c49_8 : F.repChkAG (Q.tab r49_8.1) γ r49_8.2.1 r49_8.2.2 = true := by decide +kernel
theorem c49_9 : F.repChkAG (Q.tab r49_9.1) γ r49_9.2.1 r49_9.2.2 = true := by decide +kernel
theorem c49_10 : F.repChkAG (Q.tab r49_10.1) γ r49_10.2.1 r49_10.2.2 = true := by decide +kernel

def D49 : List (ℕ × (ℤ × ℤ) × RepData) := [r49_0, r49_1, r49_2, r49_3, r49_4, r49_5, r49_6, r49_7, r49_8, r49_9, r49_10]

theorem chkA49 : D49.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D49, List.all_cons, List.all_nil, c49_0, c49_1, c49_2, c49_3, c49_4, c49_5, c49_6, c49_7, c49_8, c49_9, c49_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
