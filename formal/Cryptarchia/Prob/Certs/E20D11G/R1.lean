module

public import Cryptarchia.Prob.Certs.E20D11G.Tab
meta import Cryptarchia.Prob.Certs.E20D11G.Tab

/-! # E20D11G: (group, representative) entries 11 to 21, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r1_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 11 (0, 0))
def r1_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 12 (0, 0))
def r1_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 13 (0, 0))
def r1_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 14 (0, 0))
def r1_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 15 (0, 0))
def r1_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 16 (0, 0))
def r1_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 17 (0, 0))
def r1_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 18 (0, 0))
def r1_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 19 (0, 0))
def r1_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 20 (0, 0))
def r1_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 21 (0, 0))

theorem c1_0 : F.repChkAG (Q.tab r1_0.1) γ nG r1_0.1 Rd r1_0.2.1 r1_0.2.2 = true := by decide +kernel
theorem c1_1 : F.repChkAG (Q.tab r1_1.1) γ nG r1_1.1 Rd r1_1.2.1 r1_1.2.2 = true := by decide +kernel
theorem c1_2 : F.repChkAG (Q.tab r1_2.1) γ nG r1_2.1 Rd r1_2.2.1 r1_2.2.2 = true := by decide +kernel
theorem c1_3 : F.repChkAG (Q.tab r1_3.1) γ nG r1_3.1 Rd r1_3.2.1 r1_3.2.2 = true := by decide +kernel
theorem c1_4 : F.repChkAG (Q.tab r1_4.1) γ nG r1_4.1 Rd r1_4.2.1 r1_4.2.2 = true := by decide +kernel
theorem c1_5 : F.repChkAG (Q.tab r1_5.1) γ nG r1_5.1 Rd r1_5.2.1 r1_5.2.2 = true := by decide +kernel
theorem c1_6 : F.repChkAG (Q.tab r1_6.1) γ nG r1_6.1 Rd r1_6.2.1 r1_6.2.2 = true := by decide +kernel
theorem c1_7 : F.repChkAG (Q.tab r1_7.1) γ nG r1_7.1 Rd r1_7.2.1 r1_7.2.2 = true := by decide +kernel
theorem c1_8 : F.repChkAG (Q.tab r1_8.1) γ nG r1_8.1 Rd r1_8.2.1 r1_8.2.2 = true := by decide +kernel
theorem c1_9 : F.repChkAG (Q.tab r1_9.1) γ nG r1_9.1 Rd r1_9.2.1 r1_9.2.2 = true := by decide +kernel
theorem c1_10 : F.repChkAG (Q.tab r1_10.1) γ nG r1_10.1 Rd r1_10.2.1 r1_10.2.2 = true := by decide +kernel

def D1 : List (ℕ × (ℤ × ℤ) × RepData) := [r1_0, r1_1, r1_2, r1_3, r1_4, r1_5, r1_6, r1_7, r1_8, r1_9, r1_10]

theorem chkA1 : D1.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D1, List.all_cons, List.all_nil, c1_0, c1_1, c1_2, c1_3, c1_4, c1_5, c1_6, c1_7, c1_8, c1_9, c1_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
