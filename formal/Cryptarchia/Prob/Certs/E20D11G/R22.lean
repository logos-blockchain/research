module

public import Cryptarchia.Prob.Certs.E20D11G.R14
meta import Cryptarchia.Prob.Certs.E20D11G.R14

/-! # E20D11G: (group, representative) entries 242 to 252, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r22_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 242 (0, 0))
def r22_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 243 (0, 0))
def r22_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 244 (0, 0))
def r22_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 245 (0, 0))
def r22_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 246 (0, 0))
def r22_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 247 (0, 0))
def r22_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 248 (0, 0))
def r22_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 249 (0, 0))
def r22_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 250 (0, 0))
def r22_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 251 (0, 0))
def r22_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 252 (0, 0))

theorem c22_0 : F.repChkAG (Q.tab r22_0.1) γ nG r22_0.1 Rd cst r22_0.2.1 r22_0.2.2 = true := by decide +kernel
theorem c22_1 : F.repChkAG (Q.tab r22_1.1) γ nG r22_1.1 Rd cst r22_1.2.1 r22_1.2.2 = true := by decide +kernel
theorem c22_2 : F.repChkAG (Q.tab r22_2.1) γ nG r22_2.1 Rd cst r22_2.2.1 r22_2.2.2 = true := by decide +kernel
theorem c22_3 : F.repChkAG (Q.tab r22_3.1) γ nG r22_3.1 Rd cst r22_3.2.1 r22_3.2.2 = true := by decide +kernel
theorem c22_4 : F.repChkAG (Q.tab r22_4.1) γ nG r22_4.1 Rd cst r22_4.2.1 r22_4.2.2 = true := by decide +kernel
theorem c22_5 : F.repChkAG (Q.tab r22_5.1) γ nG r22_5.1 Rd cst r22_5.2.1 r22_5.2.2 = true := by decide +kernel
theorem c22_6 : F.repChkAG (Q.tab r22_6.1) γ nG r22_6.1 Rd cst r22_6.2.1 r22_6.2.2 = true := by decide +kernel
theorem c22_7 : F.repChkAG (Q.tab r22_7.1) γ nG r22_7.1 Rd cst r22_7.2.1 r22_7.2.2 = true := by decide +kernel
theorem c22_8 : F.repChkAG (Q.tab r22_8.1) γ nG r22_8.1 Rd cst r22_8.2.1 r22_8.2.2 = true := by decide +kernel
theorem c22_9 : F.repChkAG (Q.tab r22_9.1) γ nG r22_9.1 Rd cst r22_9.2.1 r22_9.2.2 = true := by decide +kernel
theorem c22_10 : F.repChkAG (Q.tab r22_10.1) γ nG r22_10.1 Rd cst r22_10.2.1 r22_10.2.2 = true := by decide +kernel

def D22 : List (ℕ × (ℤ × ℤ) × RepData) := [r22_0, r22_1, r22_2, r22_3, r22_4, r22_5, r22_6, r22_7, r22_8, r22_9, r22_10]

theorem chkA22 : D22.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D22, List.all_cons, List.all_nil, c22_0, c22_1, c22_2, c22_3, c22_4, c22_5, c22_6, c22_7, c22_8, c22_9, c22_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
