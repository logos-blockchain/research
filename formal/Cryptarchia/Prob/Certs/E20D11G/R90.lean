module

public import Cryptarchia.Prob.Certs.E20D11G.R82
meta import Cryptarchia.Prob.Certs.E20D11G.R82

/-! # E20D11G: (group, representative) entries 990 to 1000, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r90_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 198 (0, 0))
def r90_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 199 (0, 0))
def r90_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 200 (0, 0))
def r90_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 201 (0, 0))
def r90_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 202 (0, 0))
def r90_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 203 (0, 0))
def r90_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 204 (0, 0))
def r90_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 205 (0, 0))
def r90_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 206 (0, 0))
def r90_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 207 (0, 0))
def r90_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 208 (0, 0))

theorem c90_0 : F.repChkAG (Q.tab r90_0.1) γ nG r90_0.1 Rd r90_0.2.1 r90_0.2.2 = true := by decide +kernel
theorem c90_1 : F.repChkAG (Q.tab r90_1.1) γ nG r90_1.1 Rd r90_1.2.1 r90_1.2.2 = true := by decide +kernel
theorem c90_2 : F.repChkAG (Q.tab r90_2.1) γ nG r90_2.1 Rd r90_2.2.1 r90_2.2.2 = true := by decide +kernel
theorem c90_3 : F.repChkAG (Q.tab r90_3.1) γ nG r90_3.1 Rd r90_3.2.1 r90_3.2.2 = true := by decide +kernel
theorem c90_4 : F.repChkAG (Q.tab r90_4.1) γ nG r90_4.1 Rd r90_4.2.1 r90_4.2.2 = true := by decide +kernel
theorem c90_5 : F.repChkAG (Q.tab r90_5.1) γ nG r90_5.1 Rd r90_5.2.1 r90_5.2.2 = true := by decide +kernel
theorem c90_6 : F.repChkAG (Q.tab r90_6.1) γ nG r90_6.1 Rd r90_6.2.1 r90_6.2.2 = true := by decide +kernel
theorem c90_7 : F.repChkAG (Q.tab r90_7.1) γ nG r90_7.1 Rd r90_7.2.1 r90_7.2.2 = true := by decide +kernel
theorem c90_8 : F.repChkAG (Q.tab r90_8.1) γ nG r90_8.1 Rd r90_8.2.1 r90_8.2.2 = true := by decide +kernel
theorem c90_9 : F.repChkAG (Q.tab r90_9.1) γ nG r90_9.1 Rd r90_9.2.1 r90_9.2.2 = true := by decide +kernel
theorem c90_10 : F.repChkAG (Q.tab r90_10.1) γ nG r90_10.1 Rd r90_10.2.1 r90_10.2.2 = true := by decide +kernel

def D90 : List (ℕ × (ℤ × ℤ) × RepData) := [r90_0, r90_1, r90_2, r90_3, r90_4, r90_5, r90_6, r90_7, r90_8, r90_9, r90_10]

theorem chkA90 : D90.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D90, List.all_cons, List.all_nil, c90_0, c90_1, c90_2, c90_3, c90_4, c90_5, c90_6, c90_7, c90_8, c90_9, c90_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
