module

public import Cryptarchia.Prob.Certs.E20D11G.Tab
meta import Cryptarchia.Prob.Certs.E20D11G.Tab

/-! # E20D11G: (group, representative) entries 55 to 65, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r5_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 55 (0, 0))
def r5_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 56 (0, 0))
def r5_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 57 (0, 0))
def r5_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 58 (0, 0))
def r5_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 59 (0, 0))
def r5_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 60 (0, 0))
def r5_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 61 (0, 0))
def r5_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 62 (0, 0))
def r5_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 63 (0, 0))
def r5_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 64 (0, 0))
def r5_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 65 (0, 0))

theorem c5_0 : F.repChkAG (Q.tab r5_0.1) γ nG r5_0.1 Rd r5_0.2.1 r5_0.2.2 = true := by decide +kernel
theorem c5_1 : F.repChkAG (Q.tab r5_1.1) γ nG r5_1.1 Rd r5_1.2.1 r5_1.2.2 = true := by decide +kernel
theorem c5_2 : F.repChkAG (Q.tab r5_2.1) γ nG r5_2.1 Rd r5_2.2.1 r5_2.2.2 = true := by decide +kernel
theorem c5_3 : F.repChkAG (Q.tab r5_3.1) γ nG r5_3.1 Rd r5_3.2.1 r5_3.2.2 = true := by decide +kernel
theorem c5_4 : F.repChkAG (Q.tab r5_4.1) γ nG r5_4.1 Rd r5_4.2.1 r5_4.2.2 = true := by decide +kernel
theorem c5_5 : F.repChkAG (Q.tab r5_5.1) γ nG r5_5.1 Rd r5_5.2.1 r5_5.2.2 = true := by decide +kernel
theorem c5_6 : F.repChkAG (Q.tab r5_6.1) γ nG r5_6.1 Rd r5_6.2.1 r5_6.2.2 = true := by decide +kernel
theorem c5_7 : F.repChkAG (Q.tab r5_7.1) γ nG r5_7.1 Rd r5_7.2.1 r5_7.2.2 = true := by decide +kernel
theorem c5_8 : F.repChkAG (Q.tab r5_8.1) γ nG r5_8.1 Rd r5_8.2.1 r5_8.2.2 = true := by decide +kernel
theorem c5_9 : F.repChkAG (Q.tab r5_9.1) γ nG r5_9.1 Rd r5_9.2.1 r5_9.2.2 = true := by decide +kernel
theorem c5_10 : F.repChkAG (Q.tab r5_10.1) γ nG r5_10.1 Rd r5_10.2.1 r5_10.2.2 = true := by decide +kernel

def D5 : List (ℕ × (ℤ × ℤ) × RepData) := [r5_0, r5_1, r5_2, r5_3, r5_4, r5_5, r5_6, r5_7, r5_8, r5_9, r5_10]

theorem chkA5 : D5.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D5, List.all_cons, List.all_nil, c5_0, c5_1, c5_2, c5_3, c5_4, c5_5, c5_6, c5_7, c5_8, c5_9, c5_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
