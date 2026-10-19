module

public import Cryptarchia.Prob.Certs.E20D11G.Tab
meta import Cryptarchia.Prob.Certs.E20D11G.Tab

/-! # E20D11G: (group, representative) entries 22 to 32, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r2_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 22 (0, 0))
def r2_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 23 (0, 0))
def r2_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 24 (0, 0))
def r2_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 25 (0, 0))
def r2_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 26 (0, 0))
def r2_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 27 (0, 0))
def r2_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 28 (0, 0))
def r2_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 29 (0, 0))
def r2_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 30 (0, 0))
def r2_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 31 (0, 0))
def r2_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 32 (0, 0))

theorem c2_0 : F.repChkAG (Q.tab r2_0.1) γ nG r2_0.1 Rd r2_0.2.1 r2_0.2.2 = true := by decide +kernel
theorem c2_1 : F.repChkAG (Q.tab r2_1.1) γ nG r2_1.1 Rd r2_1.2.1 r2_1.2.2 = true := by decide +kernel
theorem c2_2 : F.repChkAG (Q.tab r2_2.1) γ nG r2_2.1 Rd r2_2.2.1 r2_2.2.2 = true := by decide +kernel
theorem c2_3 : F.repChkAG (Q.tab r2_3.1) γ nG r2_3.1 Rd r2_3.2.1 r2_3.2.2 = true := by decide +kernel
theorem c2_4 : F.repChkAG (Q.tab r2_4.1) γ nG r2_4.1 Rd r2_4.2.1 r2_4.2.2 = true := by decide +kernel
theorem c2_5 : F.repChkAG (Q.tab r2_5.1) γ nG r2_5.1 Rd r2_5.2.1 r2_5.2.2 = true := by decide +kernel
theorem c2_6 : F.repChkAG (Q.tab r2_6.1) γ nG r2_6.1 Rd r2_6.2.1 r2_6.2.2 = true := by decide +kernel
theorem c2_7 : F.repChkAG (Q.tab r2_7.1) γ nG r2_7.1 Rd r2_7.2.1 r2_7.2.2 = true := by decide +kernel
theorem c2_8 : F.repChkAG (Q.tab r2_8.1) γ nG r2_8.1 Rd r2_8.2.1 r2_8.2.2 = true := by decide +kernel
theorem c2_9 : F.repChkAG (Q.tab r2_9.1) γ nG r2_9.1 Rd r2_9.2.1 r2_9.2.2 = true := by decide +kernel
theorem c2_10 : F.repChkAG (Q.tab r2_10.1) γ nG r2_10.1 Rd r2_10.2.1 r2_10.2.2 = true := by decide +kernel

def D2 : List (ℕ × (ℤ × ℤ) × RepData) := [r2_0, r2_1, r2_2, r2_3, r2_4, r2_5, r2_6, r2_7, r2_8, r2_9, r2_10]

theorem chkA2 : D2.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D2, List.all_cons, List.all_nil, c2_0, c2_1, c2_2, c2_3, c2_4, c2_5, c2_6, c2_7, c2_8, c2_9, c2_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
