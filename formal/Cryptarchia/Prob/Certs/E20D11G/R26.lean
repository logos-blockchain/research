module

public import Cryptarchia.Prob.Certs.E20D11G.R22
meta import Cryptarchia.Prob.Certs.E20D11G.R22

/-! # E20D11G: (group, representative) entries 286 to 296, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r26_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 22 (0, 0))
def r26_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 23 (0, 0))
def r26_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 24 (0, 0))
def r26_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 25 (0, 0))
def r26_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 26 (0, 0))
def r26_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 27 (0, 0))
def r26_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 28 (0, 0))
def r26_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 29 (0, 0))
def r26_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 30 (0, 0))
def r26_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 31 (0, 0))
def r26_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 32 (0, 0))

theorem c26_0 : F.repChkAG (Q.tab r26_0.1) γ r26_0.2.1 r26_0.2.2 = true := by decide +kernel
theorem c26_1 : F.repChkAG (Q.tab r26_1.1) γ r26_1.2.1 r26_1.2.2 = true := by decide +kernel
theorem c26_2 : F.repChkAG (Q.tab r26_2.1) γ r26_2.2.1 r26_2.2.2 = true := by decide +kernel
theorem c26_3 : F.repChkAG (Q.tab r26_3.1) γ r26_3.2.1 r26_3.2.2 = true := by decide +kernel
theorem c26_4 : F.repChkAG (Q.tab r26_4.1) γ r26_4.2.1 r26_4.2.2 = true := by decide +kernel
theorem c26_5 : F.repChkAG (Q.tab r26_5.1) γ r26_5.2.1 r26_5.2.2 = true := by decide +kernel
theorem c26_6 : F.repChkAG (Q.tab r26_6.1) γ r26_6.2.1 r26_6.2.2 = true := by decide +kernel
theorem c26_7 : F.repChkAG (Q.tab r26_7.1) γ r26_7.2.1 r26_7.2.2 = true := by decide +kernel
theorem c26_8 : F.repChkAG (Q.tab r26_8.1) γ r26_8.2.1 r26_8.2.2 = true := by decide +kernel
theorem c26_9 : F.repChkAG (Q.tab r26_9.1) γ r26_9.2.1 r26_9.2.2 = true := by decide +kernel
theorem c26_10 : F.repChkAG (Q.tab r26_10.1) γ r26_10.2.1 r26_10.2.2 = true := by decide +kernel

def D26 : List (ℕ × (ℤ × ℤ) × RepData) := [r26_0, r26_1, r26_2, r26_3, r26_4, r26_5, r26_6, r26_7, r26_8, r26_9, r26_10]

theorem chkA26 : D26.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D26, List.all_cons, List.all_nil, c26_0, c26_1, c26_2, c26_3, c26_4, c26_5, c26_6, c26_7, c26_8, c26_9, c26_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
