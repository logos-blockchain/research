module

public import Cryptarchia.Prob.Certs.E20D11G.R36
meta import Cryptarchia.Prob.Certs.E20D11G.R36

/-! # E20D11G: (group, representative) entries 484 to 494, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r44_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 220 (0, 0))
def r44_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 221 (0, 0))
def r44_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 222 (0, 0))
def r44_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 223 (0, 0))
def r44_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 224 (0, 0))
def r44_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 225 (0, 0))
def r44_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 226 (0, 0))
def r44_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 227 (0, 0))
def r44_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 228 (0, 0))
def r44_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 229 (0, 0))
def r44_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 230 (0, 0))

theorem c44_0 : F.repChkAG (Q.tab r44_0.1) γ nG r44_0.1 Rd r44_0.2.1 r44_0.2.2 = true := by decide +kernel
theorem c44_1 : F.repChkAG (Q.tab r44_1.1) γ nG r44_1.1 Rd r44_1.2.1 r44_1.2.2 = true := by decide +kernel
theorem c44_2 : F.repChkAG (Q.tab r44_2.1) γ nG r44_2.1 Rd r44_2.2.1 r44_2.2.2 = true := by decide +kernel
theorem c44_3 : F.repChkAG (Q.tab r44_3.1) γ nG r44_3.1 Rd r44_3.2.1 r44_3.2.2 = true := by decide +kernel
theorem c44_4 : F.repChkAG (Q.tab r44_4.1) γ nG r44_4.1 Rd r44_4.2.1 r44_4.2.2 = true := by decide +kernel
theorem c44_5 : F.repChkAG (Q.tab r44_5.1) γ nG r44_5.1 Rd r44_5.2.1 r44_5.2.2 = true := by decide +kernel
theorem c44_6 : F.repChkAG (Q.tab r44_6.1) γ nG r44_6.1 Rd r44_6.2.1 r44_6.2.2 = true := by decide +kernel
theorem c44_7 : F.repChkAG (Q.tab r44_7.1) γ nG r44_7.1 Rd r44_7.2.1 r44_7.2.2 = true := by decide +kernel
theorem c44_8 : F.repChkAG (Q.tab r44_8.1) γ nG r44_8.1 Rd r44_8.2.1 r44_8.2.2 = true := by decide +kernel
theorem c44_9 : F.repChkAG (Q.tab r44_9.1) γ nG r44_9.1 Rd r44_9.2.1 r44_9.2.2 = true := by decide +kernel
theorem c44_10 : F.repChkAG (Q.tab r44_10.1) γ nG r44_10.1 Rd r44_10.2.1 r44_10.2.2 = true := by decide +kernel

def D44 : List (ℕ × (ℤ × ℤ) × RepData) := [r44_0, r44_1, r44_2, r44_3, r44_4, r44_5, r44_6, r44_7, r44_8, r44_9, r44_10]

theorem chkA44 : D44.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D44, List.all_cons, List.all_nil, c44_0, c44_1, c44_2, c44_3, c44_4, c44_5, c44_6, c44_7, c44_8, c44_9, c44_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
