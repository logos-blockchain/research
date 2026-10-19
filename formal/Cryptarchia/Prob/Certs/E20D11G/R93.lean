module

public import Cryptarchia.Prob.Certs.E20D11G.R89
meta import Cryptarchia.Prob.Certs.E20D11G.R89

/-! # E20D11G: (group, representative) entries 1023 to 1033, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r93_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 231 (0, 0))
def r93_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 232 (0, 0))
def r93_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 233 (0, 0))
def r93_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 234 (0, 0))
def r93_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 235 (0, 0))
def r93_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 236 (0, 0))
def r93_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 237 (0, 0))
def r93_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 238 (0, 0))
def r93_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 239 (0, 0))
def r93_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 240 (0, 0))
def r93_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 241 (0, 0))

theorem c93_0 : F.repChkAG (Q.tab r93_0.1) γ r93_0.2.1 r93_0.2.2 = true := by decide +kernel
theorem c93_1 : F.repChkAG (Q.tab r93_1.1) γ r93_1.2.1 r93_1.2.2 = true := by decide +kernel
theorem c93_2 : F.repChkAG (Q.tab r93_2.1) γ r93_2.2.1 r93_2.2.2 = true := by decide +kernel
theorem c93_3 : F.repChkAG (Q.tab r93_3.1) γ r93_3.2.1 r93_3.2.2 = true := by decide +kernel
theorem c93_4 : F.repChkAG (Q.tab r93_4.1) γ r93_4.2.1 r93_4.2.2 = true := by decide +kernel
theorem c93_5 : F.repChkAG (Q.tab r93_5.1) γ r93_5.2.1 r93_5.2.2 = true := by decide +kernel
theorem c93_6 : F.repChkAG (Q.tab r93_6.1) γ r93_6.2.1 r93_6.2.2 = true := by decide +kernel
theorem c93_7 : F.repChkAG (Q.tab r93_7.1) γ r93_7.2.1 r93_7.2.2 = true := by decide +kernel
theorem c93_8 : F.repChkAG (Q.tab r93_8.1) γ r93_8.2.1 r93_8.2.2 = true := by decide +kernel
theorem c93_9 : F.repChkAG (Q.tab r93_9.1) γ r93_9.2.1 r93_9.2.2 = true := by decide +kernel
theorem c93_10 : F.repChkAG (Q.tab r93_10.1) γ r93_10.2.1 r93_10.2.2 = true := by decide +kernel

def D93 : List (ℕ × (ℤ × ℤ) × RepData) := [r93_0, r93_1, r93_2, r93_3, r93_4, r93_5, r93_6, r93_7, r93_8, r93_9, r93_10]

theorem chkA93 : D93.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D93, List.all_cons, List.all_nil, c93_0, c93_1, c93_2, c93_3, c93_4, c93_5, c93_6, c93_7, c93_8, c93_9, c93_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
