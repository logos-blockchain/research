module

public import Cryptarchia.Prob.Certs.E20D11G.R6
meta import Cryptarchia.Prob.Certs.E20D11G.R6

/-! # E20D11G: (group, representative) entries 154 to 164, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r14_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 154 (0, 0))
def r14_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 155 (0, 0))
def r14_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 156 (0, 0))
def r14_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 157 (0, 0))
def r14_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 158 (0, 0))
def r14_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 159 (0, 0))
def r14_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 160 (0, 0))
def r14_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 161 (0, 0))
def r14_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 162 (0, 0))
def r14_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 163 (0, 0))
def r14_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 164 (0, 0))

theorem c14_0 : F.repChkAG (Q.tab r14_0.1) γ nG r14_0.1 Rd r14_0.2.1 r14_0.2.2 = true := by decide +kernel
theorem c14_1 : F.repChkAG (Q.tab r14_1.1) γ nG r14_1.1 Rd r14_1.2.1 r14_1.2.2 = true := by decide +kernel
theorem c14_2 : F.repChkAG (Q.tab r14_2.1) γ nG r14_2.1 Rd r14_2.2.1 r14_2.2.2 = true := by decide +kernel
theorem c14_3 : F.repChkAG (Q.tab r14_3.1) γ nG r14_3.1 Rd r14_3.2.1 r14_3.2.2 = true := by decide +kernel
theorem c14_4 : F.repChkAG (Q.tab r14_4.1) γ nG r14_4.1 Rd r14_4.2.1 r14_4.2.2 = true := by decide +kernel
theorem c14_5 : F.repChkAG (Q.tab r14_5.1) γ nG r14_5.1 Rd r14_5.2.1 r14_5.2.2 = true := by decide +kernel
theorem c14_6 : F.repChkAG (Q.tab r14_6.1) γ nG r14_6.1 Rd r14_6.2.1 r14_6.2.2 = true := by decide +kernel
theorem c14_7 : F.repChkAG (Q.tab r14_7.1) γ nG r14_7.1 Rd r14_7.2.1 r14_7.2.2 = true := by decide +kernel
theorem c14_8 : F.repChkAG (Q.tab r14_8.1) γ nG r14_8.1 Rd r14_8.2.1 r14_8.2.2 = true := by decide +kernel
theorem c14_9 : F.repChkAG (Q.tab r14_9.1) γ nG r14_9.1 Rd r14_9.2.1 r14_9.2.2 = true := by decide +kernel
theorem c14_10 : F.repChkAG (Q.tab r14_10.1) γ nG r14_10.1 Rd r14_10.2.1 r14_10.2.2 = true := by decide +kernel

def D14 : List (ℕ × (ℤ × ℤ) × RepData) := [r14_0, r14_1, r14_2, r14_3, r14_4, r14_5, r14_6, r14_7, r14_8, r14_9, r14_10]

theorem chkA14 : D14.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D14, List.all_cons, List.all_nil, c14_0, c14_1, c14_2, c14_3, c14_4, c14_5, c14_6, c14_7, c14_8, c14_9, c14_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
