module

public import Cryptarchia.Prob.Certs.E20D11G.R15
meta import Cryptarchia.Prob.Certs.E20D11G.R15

/-! # E20D11G: (group, representative) entries 253 to 263, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r23_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 253 (0, 0))
def r23_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 254 (0, 0))
def r23_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 255 (0, 0))
def r23_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 256 (0, 0))
def r23_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 257 (0, 0))
def r23_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 258 (0, 0))
def r23_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 259 (0, 0))
def r23_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 260 (0, 0))
def r23_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 261 (0, 0))
def r23_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 262 (0, 0))
def r23_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 263 (0, 0))

theorem c23_0 : F.repChkAG (Q.tab r23_0.1) γ nG r23_0.1 Rd cst r23_0.2.1 r23_0.2.2 = true := by decide +kernel
theorem c23_1 : F.repChkAG (Q.tab r23_1.1) γ nG r23_1.1 Rd cst r23_1.2.1 r23_1.2.2 = true := by decide +kernel
theorem c23_2 : F.repChkAG (Q.tab r23_2.1) γ nG r23_2.1 Rd cst r23_2.2.1 r23_2.2.2 = true := by decide +kernel
theorem c23_3 : F.repChkAG (Q.tab r23_3.1) γ nG r23_3.1 Rd cst r23_3.2.1 r23_3.2.2 = true := by decide +kernel
theorem c23_4 : F.repChkAG (Q.tab r23_4.1) γ nG r23_4.1 Rd cst r23_4.2.1 r23_4.2.2 = true := by decide +kernel
theorem c23_5 : F.repChkAG (Q.tab r23_5.1) γ nG r23_5.1 Rd cst r23_5.2.1 r23_5.2.2 = true := by decide +kernel
theorem c23_6 : F.repChkAG (Q.tab r23_6.1) γ nG r23_6.1 Rd cst r23_6.2.1 r23_6.2.2 = true := by decide +kernel
theorem c23_7 : F.repChkAG (Q.tab r23_7.1) γ nG r23_7.1 Rd cst r23_7.2.1 r23_7.2.2 = true := by decide +kernel
theorem c23_8 : F.repChkAG (Q.tab r23_8.1) γ nG r23_8.1 Rd cst r23_8.2.1 r23_8.2.2 = true := by decide +kernel
theorem c23_9 : F.repChkAG (Q.tab r23_9.1) γ nG r23_9.1 Rd cst r23_9.2.1 r23_9.2.2 = true := by decide +kernel
theorem c23_10 : F.repChkAG (Q.tab r23_10.1) γ nG r23_10.1 Rd cst r23_10.2.1 r23_10.2.2 = true := by decide +kernel

def D23 : List (ℕ × (ℤ × ℤ) × RepData) := [r23_0, r23_1, r23_2, r23_3, r23_4, r23_5, r23_6, r23_7, r23_8, r23_9, r23_10]

theorem chkA23 : D23.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D23, List.all_cons, List.all_nil, c23_0, c23_1, c23_2, c23_3, c23_4, c23_5, c23_6, c23_7, c23_8, c23_9, c23_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
