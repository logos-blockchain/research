module

public import Cryptarchia.Prob.Certs.E20D11G.R23
meta import Cryptarchia.Prob.Certs.E20D11G.R23

/-! # E20D11G: (group, representative) entries 297 to 307, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r27_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 33 (0, 0))
def r27_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 34 (0, 0))
def r27_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 35 (0, 0))
def r27_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 36 (0, 0))
def r27_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 37 (0, 0))
def r27_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 38 (0, 0))
def r27_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 39 (0, 0))
def r27_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 40 (0, 0))
def r27_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 41 (0, 0))
def r27_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 42 (0, 0))
def r27_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 43 (0, 0))

theorem c27_0 : F.repChkAG (Q.tab r27_0.1) γ r27_0.2.1 r27_0.2.2 = true := by decide +kernel
theorem c27_1 : F.repChkAG (Q.tab r27_1.1) γ r27_1.2.1 r27_1.2.2 = true := by decide +kernel
theorem c27_2 : F.repChkAG (Q.tab r27_2.1) γ r27_2.2.1 r27_2.2.2 = true := by decide +kernel
theorem c27_3 : F.repChkAG (Q.tab r27_3.1) γ r27_3.2.1 r27_3.2.2 = true := by decide +kernel
theorem c27_4 : F.repChkAG (Q.tab r27_4.1) γ r27_4.2.1 r27_4.2.2 = true := by decide +kernel
theorem c27_5 : F.repChkAG (Q.tab r27_5.1) γ r27_5.2.1 r27_5.2.2 = true := by decide +kernel
theorem c27_6 : F.repChkAG (Q.tab r27_6.1) γ r27_6.2.1 r27_6.2.2 = true := by decide +kernel
theorem c27_7 : F.repChkAG (Q.tab r27_7.1) γ r27_7.2.1 r27_7.2.2 = true := by decide +kernel
theorem c27_8 : F.repChkAG (Q.tab r27_8.1) γ r27_8.2.1 r27_8.2.2 = true := by decide +kernel
theorem c27_9 : F.repChkAG (Q.tab r27_9.1) γ r27_9.2.1 r27_9.2.2 = true := by decide +kernel
theorem c27_10 : F.repChkAG (Q.tab r27_10.1) γ r27_10.2.1 r27_10.2.2 = true := by decide +kernel

def D27 : List (ℕ × (ℤ × ℤ) × RepData) := [r27_0, r27_1, r27_2, r27_3, r27_4, r27_5, r27_6, r27_7, r27_8, r27_9, r27_10]

theorem chkA27 : D27.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D27, List.all_cons, List.all_nil, c27_0, c27_1, c27_2, c27_3, c27_4, c27_5, c27_6, c27_7, c27_8, c27_9, c27_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
