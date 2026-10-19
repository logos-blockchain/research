module

public import Cryptarchia.Prob.Certs.E20D11G.Tab
meta import Cryptarchia.Prob.Certs.E20D11G.Tab

/-! # E20D11G: (group, representative) entries 0 to 10, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r0_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 0 (0, 0))
def r0_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 1 (0, 0))
def r0_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 2 (0, 0))
def r0_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 3 (0, 0))
def r0_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 4 (0, 0))
def r0_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 5 (0, 0))
def r0_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 6 (0, 0))
def r0_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 7 (0, 0))
def r0_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 8 (0, 0))
def r0_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 9 (0, 0))
def r0_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 10 (0, 0))

theorem c0_0 : F.repChkAG (Q.tab r0_0.1) γ nG r0_0.1 Rd r0_0.2.1 r0_0.2.2 = true := by decide +kernel
theorem c0_1 : F.repChkAG (Q.tab r0_1.1) γ nG r0_1.1 Rd r0_1.2.1 r0_1.2.2 = true := by decide +kernel
theorem c0_2 : F.repChkAG (Q.tab r0_2.1) γ nG r0_2.1 Rd r0_2.2.1 r0_2.2.2 = true := by decide +kernel
theorem c0_3 : F.repChkAG (Q.tab r0_3.1) γ nG r0_3.1 Rd r0_3.2.1 r0_3.2.2 = true := by decide +kernel
theorem c0_4 : F.repChkAG (Q.tab r0_4.1) γ nG r0_4.1 Rd r0_4.2.1 r0_4.2.2 = true := by decide +kernel
theorem c0_5 : F.repChkAG (Q.tab r0_5.1) γ nG r0_5.1 Rd r0_5.2.1 r0_5.2.2 = true := by decide +kernel
theorem c0_6 : F.repChkAG (Q.tab r0_6.1) γ nG r0_6.1 Rd r0_6.2.1 r0_6.2.2 = true := by decide +kernel
theorem c0_7 : F.repChkAG (Q.tab r0_7.1) γ nG r0_7.1 Rd r0_7.2.1 r0_7.2.2 = true := by decide +kernel
theorem c0_8 : F.repChkAG (Q.tab r0_8.1) γ nG r0_8.1 Rd r0_8.2.1 r0_8.2.2 = true := by decide +kernel
theorem c0_9 : F.repChkAG (Q.tab r0_9.1) γ nG r0_9.1 Rd r0_9.2.1 r0_9.2.2 = true := by decide +kernel
theorem c0_10 : F.repChkAG (Q.tab r0_10.1) γ nG r0_10.1 Rd r0_10.2.1 r0_10.2.2 = true := by decide +kernel

def D0 : List (ℕ × (ℤ × ℤ) × RepData) := [r0_0, r0_1, r0_2, r0_3, r0_4, r0_5, r0_6, r0_7, r0_8, r0_9, r0_10]

theorem chkA0 : D0.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D0, List.all_cons, List.all_nil, c0_0, c0_1, c0_2, c0_3, c0_4, c0_5, c0_6, c0_7, c0_8, c0_9, c0_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
