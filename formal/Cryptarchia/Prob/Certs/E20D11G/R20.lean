module

public import Cryptarchia.Prob.Certs.E20D11G.R12
meta import Cryptarchia.Prob.Certs.E20D11G.R12

/-! # E20D11G: (group, representative) entries 220 to 230, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r20_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 220 (0, 0))
def r20_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 221 (0, 0))
def r20_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 222 (0, 0))
def r20_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 223 (0, 0))
def r20_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 224 (0, 0))
def r20_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 225 (0, 0))
def r20_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 226 (0, 0))
def r20_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 227 (0, 0))
def r20_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 228 (0, 0))
def r20_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 229 (0, 0))
def r20_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 230 (0, 0))

theorem c20_0 : F.repChkAG (Q.tab r20_0.1) γ nG r20_0.1 Rd r20_0.2.1 r20_0.2.2 = true := by decide +kernel
theorem c20_1 : F.repChkAG (Q.tab r20_1.1) γ nG r20_1.1 Rd r20_1.2.1 r20_1.2.2 = true := by decide +kernel
theorem c20_2 : F.repChkAG (Q.tab r20_2.1) γ nG r20_2.1 Rd r20_2.2.1 r20_2.2.2 = true := by decide +kernel
theorem c20_3 : F.repChkAG (Q.tab r20_3.1) γ nG r20_3.1 Rd r20_3.2.1 r20_3.2.2 = true := by decide +kernel
theorem c20_4 : F.repChkAG (Q.tab r20_4.1) γ nG r20_4.1 Rd r20_4.2.1 r20_4.2.2 = true := by decide +kernel
theorem c20_5 : F.repChkAG (Q.tab r20_5.1) γ nG r20_5.1 Rd r20_5.2.1 r20_5.2.2 = true := by decide +kernel
theorem c20_6 : F.repChkAG (Q.tab r20_6.1) γ nG r20_6.1 Rd r20_6.2.1 r20_6.2.2 = true := by decide +kernel
theorem c20_7 : F.repChkAG (Q.tab r20_7.1) γ nG r20_7.1 Rd r20_7.2.1 r20_7.2.2 = true := by decide +kernel
theorem c20_8 : F.repChkAG (Q.tab r20_8.1) γ nG r20_8.1 Rd r20_8.2.1 r20_8.2.2 = true := by decide +kernel
theorem c20_9 : F.repChkAG (Q.tab r20_9.1) γ nG r20_9.1 Rd r20_9.2.1 r20_9.2.2 = true := by decide +kernel
theorem c20_10 : F.repChkAG (Q.tab r20_10.1) γ nG r20_10.1 Rd r20_10.2.1 r20_10.2.2 = true := by decide +kernel

def D20 : List (ℕ × (ℤ × ℤ) × RepData) := [r20_0, r20_1, r20_2, r20_3, r20_4, r20_5, r20_6, r20_7, r20_8, r20_9, r20_10]

theorem chkA20 : D20.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D20, List.all_cons, List.all_nil, c20_0, c20_1, c20_2, c20_3, c20_4, c20_5, c20_6, c20_7, c20_8, c20_9, c20_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
