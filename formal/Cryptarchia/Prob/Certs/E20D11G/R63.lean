module

public import Cryptarchia.Prob.Certs.E20D11G.R55
meta import Cryptarchia.Prob.Certs.E20D11G.R55

/-! # E20D11G: (group, representative) entries 693 to 703, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r63_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 165 (0, 0))
def r63_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 166 (0, 0))
def r63_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 167 (0, 0))
def r63_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 168 (0, 0))
def r63_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 169 (0, 0))
def r63_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 170 (0, 0))
def r63_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 171 (0, 0))
def r63_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 172 (0, 0))
def r63_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 173 (0, 0))
def r63_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 174 (0, 0))
def r63_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 175 (0, 0))

theorem c63_0 : F.repChkAG (Q.tab r63_0.1) γ nG r63_0.1 Rd r63_0.2.1 r63_0.2.2 = true := by decide +kernel
theorem c63_1 : F.repChkAG (Q.tab r63_1.1) γ nG r63_1.1 Rd r63_1.2.1 r63_1.2.2 = true := by decide +kernel
theorem c63_2 : F.repChkAG (Q.tab r63_2.1) γ nG r63_2.1 Rd r63_2.2.1 r63_2.2.2 = true := by decide +kernel
theorem c63_3 : F.repChkAG (Q.tab r63_3.1) γ nG r63_3.1 Rd r63_3.2.1 r63_3.2.2 = true := by decide +kernel
theorem c63_4 : F.repChkAG (Q.tab r63_4.1) γ nG r63_4.1 Rd r63_4.2.1 r63_4.2.2 = true := by decide +kernel
theorem c63_5 : F.repChkAG (Q.tab r63_5.1) γ nG r63_5.1 Rd r63_5.2.1 r63_5.2.2 = true := by decide +kernel
theorem c63_6 : F.repChkAG (Q.tab r63_6.1) γ nG r63_6.1 Rd r63_6.2.1 r63_6.2.2 = true := by decide +kernel
theorem c63_7 : F.repChkAG (Q.tab r63_7.1) γ nG r63_7.1 Rd r63_7.2.1 r63_7.2.2 = true := by decide +kernel
theorem c63_8 : F.repChkAG (Q.tab r63_8.1) γ nG r63_8.1 Rd r63_8.2.1 r63_8.2.2 = true := by decide +kernel
theorem c63_9 : F.repChkAG (Q.tab r63_9.1) γ nG r63_9.1 Rd r63_9.2.1 r63_9.2.2 = true := by decide +kernel
theorem c63_10 : F.repChkAG (Q.tab r63_10.1) γ nG r63_10.1 Rd r63_10.2.1 r63_10.2.2 = true := by decide +kernel

def D63 : List (ℕ × (ℤ × ℤ) × RepData) := [r63_0, r63_1, r63_2, r63_3, r63_4, r63_5, r63_6, r63_7, r63_8, r63_9, r63_10]

theorem chkA63 : D63.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D63, List.all_cons, List.all_nil, c63_0, c63_1, c63_2, c63_3, c63_4, c63_5, c63_6, c63_7, c63_8, c63_9, c63_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
