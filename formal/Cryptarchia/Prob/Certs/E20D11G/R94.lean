module

public import Cryptarchia.Prob.Certs.E20D11G.R86
meta import Cryptarchia.Prob.Certs.E20D11G.R86

/-! # E20D11G: (group, representative) entries 1034 to 1044, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r94_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 242 (0, 0))
def r94_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 243 (0, 0))
def r94_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 244 (0, 0))
def r94_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 245 (0, 0))
def r94_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 246 (0, 0))
def r94_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 247 (0, 0))
def r94_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 248 (0, 0))
def r94_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 249 (0, 0))
def r94_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 250 (0, 0))
def r94_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 251 (0, 0))
def r94_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 252 (0, 0))

theorem c94_0 : F.repChkAG (Q.tab r94_0.1) γ nG r94_0.1 Rd r94_0.2.1 r94_0.2.2 = true := by decide +kernel
theorem c94_1 : F.repChkAG (Q.tab r94_1.1) γ nG r94_1.1 Rd r94_1.2.1 r94_1.2.2 = true := by decide +kernel
theorem c94_2 : F.repChkAG (Q.tab r94_2.1) γ nG r94_2.1 Rd r94_2.2.1 r94_2.2.2 = true := by decide +kernel
theorem c94_3 : F.repChkAG (Q.tab r94_3.1) γ nG r94_3.1 Rd r94_3.2.1 r94_3.2.2 = true := by decide +kernel
theorem c94_4 : F.repChkAG (Q.tab r94_4.1) γ nG r94_4.1 Rd r94_4.2.1 r94_4.2.2 = true := by decide +kernel
theorem c94_5 : F.repChkAG (Q.tab r94_5.1) γ nG r94_5.1 Rd r94_5.2.1 r94_5.2.2 = true := by decide +kernel
theorem c94_6 : F.repChkAG (Q.tab r94_6.1) γ nG r94_6.1 Rd r94_6.2.1 r94_6.2.2 = true := by decide +kernel
theorem c94_7 : F.repChkAG (Q.tab r94_7.1) γ nG r94_7.1 Rd r94_7.2.1 r94_7.2.2 = true := by decide +kernel
theorem c94_8 : F.repChkAG (Q.tab r94_8.1) γ nG r94_8.1 Rd r94_8.2.1 r94_8.2.2 = true := by decide +kernel
theorem c94_9 : F.repChkAG (Q.tab r94_9.1) γ nG r94_9.1 Rd r94_9.2.1 r94_9.2.2 = true := by decide +kernel
theorem c94_10 : F.repChkAG (Q.tab r94_10.1) γ nG r94_10.1 Rd r94_10.2.1 r94_10.2.2 = true := by decide +kernel

def D94 : List (ℕ × (ℤ × ℤ) × RepData) := [r94_0, r94_1, r94_2, r94_3, r94_4, r94_5, r94_6, r94_7, r94_8, r94_9, r94_10]

theorem chkA94 : D94.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D94, List.all_cons, List.all_nil, c94_0, c94_1, c94_2, c94_3, c94_4, c94_5, c94_6, c94_7, c94_8, c94_9, c94_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
