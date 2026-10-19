module

public import Cryptarchia.Prob.Certs.E20D11G.R21
meta import Cryptarchia.Prob.Certs.E20D11G.R21

/-! # E20D11G: (group, representative) entries 275 to 285, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r25_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 11 (0, 0))
def r25_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 12 (0, 0))
def r25_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 13 (0, 0))
def r25_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 14 (0, 0))
def r25_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 15 (0, 0))
def r25_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 16 (0, 0))
def r25_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 17 (0, 0))
def r25_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 18 (0, 0))
def r25_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 19 (0, 0))
def r25_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 20 (0, 0))
def r25_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 21 (0, 0))

theorem c25_0 : F.repChkAG (Q.tab r25_0.1) γ r25_0.2.1 r25_0.2.2 = true := by decide +kernel
theorem c25_1 : F.repChkAG (Q.tab r25_1.1) γ r25_1.2.1 r25_1.2.2 = true := by decide +kernel
theorem c25_2 : F.repChkAG (Q.tab r25_2.1) γ r25_2.2.1 r25_2.2.2 = true := by decide +kernel
theorem c25_3 : F.repChkAG (Q.tab r25_3.1) γ r25_3.2.1 r25_3.2.2 = true := by decide +kernel
theorem c25_4 : F.repChkAG (Q.tab r25_4.1) γ r25_4.2.1 r25_4.2.2 = true := by decide +kernel
theorem c25_5 : F.repChkAG (Q.tab r25_5.1) γ r25_5.2.1 r25_5.2.2 = true := by decide +kernel
theorem c25_6 : F.repChkAG (Q.tab r25_6.1) γ r25_6.2.1 r25_6.2.2 = true := by decide +kernel
theorem c25_7 : F.repChkAG (Q.tab r25_7.1) γ r25_7.2.1 r25_7.2.2 = true := by decide +kernel
theorem c25_8 : F.repChkAG (Q.tab r25_8.1) γ r25_8.2.1 r25_8.2.2 = true := by decide +kernel
theorem c25_9 : F.repChkAG (Q.tab r25_9.1) γ r25_9.2.1 r25_9.2.2 = true := by decide +kernel
theorem c25_10 : F.repChkAG (Q.tab r25_10.1) γ r25_10.2.1 r25_10.2.2 = true := by decide +kernel

def D25 : List (ℕ × (ℤ × ℤ) × RepData) := [r25_0, r25_1, r25_2, r25_3, r25_4, r25_5, r25_6, r25_7, r25_8, r25_9, r25_10]

theorem chkA25 : D25.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D25, List.all_cons, List.all_nil, c25_0, c25_1, c25_2, c25_3, c25_4, c25_5, c25_6, c25_7, c25_8, c25_9, c25_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
