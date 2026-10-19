module

public import Cryptarchia.Prob.Certs.E20D11G.R58
meta import Cryptarchia.Prob.Certs.E20D11G.R58

/-! # E20D11G: (group, representative) entries 682 to 692, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r62_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 154 (0, 0))
def r62_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 155 (0, 0))
def r62_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 156 (0, 0))
def r62_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 157 (0, 0))
def r62_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 158 (0, 0))
def r62_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 159 (0, 0))
def r62_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 160 (0, 0))
def r62_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 161 (0, 0))
def r62_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 162 (0, 0))
def r62_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 163 (0, 0))
def r62_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 164 (0, 0))

theorem c62_0 : F.repChkAG (Q.tab r62_0.1) γ r62_0.2.1 r62_0.2.2 = true := by decide +kernel
theorem c62_1 : F.repChkAG (Q.tab r62_1.1) γ r62_1.2.1 r62_1.2.2 = true := by decide +kernel
theorem c62_2 : F.repChkAG (Q.tab r62_2.1) γ r62_2.2.1 r62_2.2.2 = true := by decide +kernel
theorem c62_3 : F.repChkAG (Q.tab r62_3.1) γ r62_3.2.1 r62_3.2.2 = true := by decide +kernel
theorem c62_4 : F.repChkAG (Q.tab r62_4.1) γ r62_4.2.1 r62_4.2.2 = true := by decide +kernel
theorem c62_5 : F.repChkAG (Q.tab r62_5.1) γ r62_5.2.1 r62_5.2.2 = true := by decide +kernel
theorem c62_6 : F.repChkAG (Q.tab r62_6.1) γ r62_6.2.1 r62_6.2.2 = true := by decide +kernel
theorem c62_7 : F.repChkAG (Q.tab r62_7.1) γ r62_7.2.1 r62_7.2.2 = true := by decide +kernel
theorem c62_8 : F.repChkAG (Q.tab r62_8.1) γ r62_8.2.1 r62_8.2.2 = true := by decide +kernel
theorem c62_9 : F.repChkAG (Q.tab r62_9.1) γ r62_9.2.1 r62_9.2.2 = true := by decide +kernel
theorem c62_10 : F.repChkAG (Q.tab r62_10.1) γ r62_10.2.1 r62_10.2.2 = true := by decide +kernel

def D62 : List (ℕ × (ℤ × ℤ) × RepData) := [r62_0, r62_1, r62_2, r62_3, r62_4, r62_5, r62_6, r62_7, r62_8, r62_9, r62_10]

theorem chkA62 : D62.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D62, List.all_cons, List.all_nil, c62_0, c62_1, c62_2, c62_3, c62_4, c62_5, c62_6, c62_7, c62_8, c62_9, c62_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
