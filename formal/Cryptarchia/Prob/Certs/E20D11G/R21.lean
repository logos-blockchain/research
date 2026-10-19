module

public import Cryptarchia.Prob.Certs.E20D11G.R13
meta import Cryptarchia.Prob.Certs.E20D11G.R13

/-! # E20D11G: (group, representative) entries 231 to 241, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r21_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 231 (0, 0))
def r21_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 232 (0, 0))
def r21_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 233 (0, 0))
def r21_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 234 (0, 0))
def r21_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 235 (0, 0))
def r21_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 236 (0, 0))
def r21_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 237 (0, 0))
def r21_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 238 (0, 0))
def r21_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 239 (0, 0))
def r21_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 240 (0, 0))
def r21_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 241 (0, 0))

theorem c21_0 : F.repChkAG (Q.tab r21_0.1) γ nG r21_0.1 Rd cst r21_0.2.1 r21_0.2.2 = true := by decide +kernel
theorem c21_1 : F.repChkAG (Q.tab r21_1.1) γ nG r21_1.1 Rd cst r21_1.2.1 r21_1.2.2 = true := by decide +kernel
theorem c21_2 : F.repChkAG (Q.tab r21_2.1) γ nG r21_2.1 Rd cst r21_2.2.1 r21_2.2.2 = true := by decide +kernel
theorem c21_3 : F.repChkAG (Q.tab r21_3.1) γ nG r21_3.1 Rd cst r21_3.2.1 r21_3.2.2 = true := by decide +kernel
theorem c21_4 : F.repChkAG (Q.tab r21_4.1) γ nG r21_4.1 Rd cst r21_4.2.1 r21_4.2.2 = true := by decide +kernel
theorem c21_5 : F.repChkAG (Q.tab r21_5.1) γ nG r21_5.1 Rd cst r21_5.2.1 r21_5.2.2 = true := by decide +kernel
theorem c21_6 : F.repChkAG (Q.tab r21_6.1) γ nG r21_6.1 Rd cst r21_6.2.1 r21_6.2.2 = true := by decide +kernel
theorem c21_7 : F.repChkAG (Q.tab r21_7.1) γ nG r21_7.1 Rd cst r21_7.2.1 r21_7.2.2 = true := by decide +kernel
theorem c21_8 : F.repChkAG (Q.tab r21_8.1) γ nG r21_8.1 Rd cst r21_8.2.1 r21_8.2.2 = true := by decide +kernel
theorem c21_9 : F.repChkAG (Q.tab r21_9.1) γ nG r21_9.1 Rd cst r21_9.2.1 r21_9.2.2 = true := by decide +kernel
theorem c21_10 : F.repChkAG (Q.tab r21_10.1) γ nG r21_10.1 Rd cst r21_10.2.1 r21_10.2.2 = true := by decide +kernel

def D21 : List (ℕ × (ℤ × ℤ) × RepData) := [r21_0, r21_1, r21_2, r21_3, r21_4, r21_5, r21_6, r21_7, r21_8, r21_9, r21_10]

theorem chkA21 : D21.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D21, List.all_cons, List.all_nil, c21_0, c21_1, c21_2, c21_3, c21_4, c21_5, c21_6, c21_7, c21_8, c21_9, c21_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
