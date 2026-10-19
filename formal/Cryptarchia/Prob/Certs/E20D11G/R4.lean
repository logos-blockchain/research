module

public import Cryptarchia.Prob.Certs.E20D11G.R0
meta import Cryptarchia.Prob.Certs.E20D11G.R0

/-! # E20D11G: (group, representative) entries 44 to 54, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r4_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 44 (0, 0))
def r4_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 45 (0, 0))
def r4_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 46 (0, 0))
def r4_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 47 (0, 0))
def r4_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 48 (0, 0))
def r4_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 49 (0, 0))
def r4_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 50 (0, 0))
def r4_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 51 (0, 0))
def r4_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 52 (0, 0))
def r4_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 53 (0, 0))
def r4_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 54 (0, 0))

theorem c4_0 : F.repChkAG (Q.tab r4_0.1) γ r4_0.2.1 r4_0.2.2 = true := by decide +kernel
theorem c4_1 : F.repChkAG (Q.tab r4_1.1) γ r4_1.2.1 r4_1.2.2 = true := by decide +kernel
theorem c4_2 : F.repChkAG (Q.tab r4_2.1) γ r4_2.2.1 r4_2.2.2 = true := by decide +kernel
theorem c4_3 : F.repChkAG (Q.tab r4_3.1) γ r4_3.2.1 r4_3.2.2 = true := by decide +kernel
theorem c4_4 : F.repChkAG (Q.tab r4_4.1) γ r4_4.2.1 r4_4.2.2 = true := by decide +kernel
theorem c4_5 : F.repChkAG (Q.tab r4_5.1) γ r4_5.2.1 r4_5.2.2 = true := by decide +kernel
theorem c4_6 : F.repChkAG (Q.tab r4_6.1) γ r4_6.2.1 r4_6.2.2 = true := by decide +kernel
theorem c4_7 : F.repChkAG (Q.tab r4_7.1) γ r4_7.2.1 r4_7.2.2 = true := by decide +kernel
theorem c4_8 : F.repChkAG (Q.tab r4_8.1) γ r4_8.2.1 r4_8.2.2 = true := by decide +kernel
theorem c4_9 : F.repChkAG (Q.tab r4_9.1) γ r4_9.2.1 r4_9.2.2 = true := by decide +kernel
theorem c4_10 : F.repChkAG (Q.tab r4_10.1) γ r4_10.2.1 r4_10.2.2 = true := by decide +kernel

def D4 : List (ℕ × (ℤ × ℤ) × RepData) := [r4_0, r4_1, r4_2, r4_3, r4_4, r4_5, r4_6, r4_7, r4_8, r4_9, r4_10]

theorem chkA4 : D4.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D4, List.all_cons, List.all_nil, c4_0, c4_1, c4_2, c4_3, c4_4, c4_5, c4_6, c4_7, c4_8, c4_9, c4_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
