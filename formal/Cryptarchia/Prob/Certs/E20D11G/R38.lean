module

public import Cryptarchia.Prob.Certs.E20D11G.R30
meta import Cryptarchia.Prob.Certs.E20D11G.R30

/-! # E20D11G: (group, representative) entries 418 to 428, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r38_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 154 (0, 0))
def r38_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 155 (0, 0))
def r38_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 156 (0, 0))
def r38_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 157 (0, 0))
def r38_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 158 (0, 0))
def r38_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 159 (0, 0))
def r38_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 160 (0, 0))
def r38_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 161 (0, 0))
def r38_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 162 (0, 0))
def r38_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 163 (0, 0))
def r38_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 164 (0, 0))

theorem c38_0 : F.repChkAG (Q.tab r38_0.1) γ nG r38_0.1 Rd r38_0.2.1 r38_0.2.2 = true := by decide +kernel
theorem c38_1 : F.repChkAG (Q.tab r38_1.1) γ nG r38_1.1 Rd r38_1.2.1 r38_1.2.2 = true := by decide +kernel
theorem c38_2 : F.repChkAG (Q.tab r38_2.1) γ nG r38_2.1 Rd r38_2.2.1 r38_2.2.2 = true := by decide +kernel
theorem c38_3 : F.repChkAG (Q.tab r38_3.1) γ nG r38_3.1 Rd r38_3.2.1 r38_3.2.2 = true := by decide +kernel
theorem c38_4 : F.repChkAG (Q.tab r38_4.1) γ nG r38_4.1 Rd r38_4.2.1 r38_4.2.2 = true := by decide +kernel
theorem c38_5 : F.repChkAG (Q.tab r38_5.1) γ nG r38_5.1 Rd r38_5.2.1 r38_5.2.2 = true := by decide +kernel
theorem c38_6 : F.repChkAG (Q.tab r38_6.1) γ nG r38_6.1 Rd r38_6.2.1 r38_6.2.2 = true := by decide +kernel
theorem c38_7 : F.repChkAG (Q.tab r38_7.1) γ nG r38_7.1 Rd r38_7.2.1 r38_7.2.2 = true := by decide +kernel
theorem c38_8 : F.repChkAG (Q.tab r38_8.1) γ nG r38_8.1 Rd r38_8.2.1 r38_8.2.2 = true := by decide +kernel
theorem c38_9 : F.repChkAG (Q.tab r38_9.1) γ nG r38_9.1 Rd r38_9.2.1 r38_9.2.2 = true := by decide +kernel
theorem c38_10 : F.repChkAG (Q.tab r38_10.1) γ nG r38_10.1 Rd r38_10.2.1 r38_10.2.2 = true := by decide +kernel

def D38 : List (ℕ × (ℤ × ℤ) × RepData) := [r38_0, r38_1, r38_2, r38_3, r38_4, r38_5, r38_6, r38_7, r38_8, r38_9, r38_10]

theorem chkA38 : D38.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D38, List.all_cons, List.all_nil, c38_0, c38_1, c38_2, c38_3, c38_4, c38_5, c38_6, c38_7, c38_8, c38_9, c38_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
