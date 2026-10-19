module

public import Cryptarchia.Prob.Certs.E20D11G.R49
meta import Cryptarchia.Prob.Certs.E20D11G.R49

/-! # E20D11G: (group, representative) entries 583 to 593, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r53_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 55 (0, 0))
def r53_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 56 (0, 0))
def r53_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 57 (0, 0))
def r53_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 58 (0, 0))
def r53_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 59 (0, 0))
def r53_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 60 (0, 0))
def r53_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 61 (0, 0))
def r53_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 62 (0, 0))
def r53_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 63 (0, 0))
def r53_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 64 (0, 0))
def r53_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 65 (0, 0))

theorem c53_0 : F.repChkAG (Q.tab r53_0.1) γ r53_0.2.1 r53_0.2.2 = true := by decide +kernel
theorem c53_1 : F.repChkAG (Q.tab r53_1.1) γ r53_1.2.1 r53_1.2.2 = true := by decide +kernel
theorem c53_2 : F.repChkAG (Q.tab r53_2.1) γ r53_2.2.1 r53_2.2.2 = true := by decide +kernel
theorem c53_3 : F.repChkAG (Q.tab r53_3.1) γ r53_3.2.1 r53_3.2.2 = true := by decide +kernel
theorem c53_4 : F.repChkAG (Q.tab r53_4.1) γ r53_4.2.1 r53_4.2.2 = true := by decide +kernel
theorem c53_5 : F.repChkAG (Q.tab r53_5.1) γ r53_5.2.1 r53_5.2.2 = true := by decide +kernel
theorem c53_6 : F.repChkAG (Q.tab r53_6.1) γ r53_6.2.1 r53_6.2.2 = true := by decide +kernel
theorem c53_7 : F.repChkAG (Q.tab r53_7.1) γ r53_7.2.1 r53_7.2.2 = true := by decide +kernel
theorem c53_8 : F.repChkAG (Q.tab r53_8.1) γ r53_8.2.1 r53_8.2.2 = true := by decide +kernel
theorem c53_9 : F.repChkAG (Q.tab r53_9.1) γ r53_9.2.1 r53_9.2.2 = true := by decide +kernel
theorem c53_10 : F.repChkAG (Q.tab r53_10.1) γ r53_10.2.1 r53_10.2.2 = true := by decide +kernel

def D53 : List (ℕ × (ℤ × ℤ) × RepData) := [r53_0, r53_1, r53_2, r53_3, r53_4, r53_5, r53_6, r53_7, r53_8, r53_9, r53_10]

theorem chkA53 : D53.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D53, List.all_cons, List.all_nil, c53_0, c53_1, c53_2, c53_3, c53_4, c53_5, c53_6, c53_7, c53_8, c53_9, c53_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
