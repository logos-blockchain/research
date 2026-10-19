module

public import Cryptarchia.Prob.Certs.E20D11G.R12
meta import Cryptarchia.Prob.Certs.E20D11G.R12

/-! # E20D11G: (group, representative) entries 176 to 186, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r16_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 176 (0, 0))
def r16_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 177 (0, 0))
def r16_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 178 (0, 0))
def r16_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 179 (0, 0))
def r16_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 180 (0, 0))
def r16_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 181 (0, 0))
def r16_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 182 (0, 0))
def r16_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 183 (0, 0))
def r16_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 184 (0, 0))
def r16_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 185 (0, 0))
def r16_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 186 (0, 0))

theorem c16_0 : F.repChkAG (Q.tab r16_0.1) γ r16_0.2.1 r16_0.2.2 = true := by decide +kernel
theorem c16_1 : F.repChkAG (Q.tab r16_1.1) γ r16_1.2.1 r16_1.2.2 = true := by decide +kernel
theorem c16_2 : F.repChkAG (Q.tab r16_2.1) γ r16_2.2.1 r16_2.2.2 = true := by decide +kernel
theorem c16_3 : F.repChkAG (Q.tab r16_3.1) γ r16_3.2.1 r16_3.2.2 = true := by decide +kernel
theorem c16_4 : F.repChkAG (Q.tab r16_4.1) γ r16_4.2.1 r16_4.2.2 = true := by decide +kernel
theorem c16_5 : F.repChkAG (Q.tab r16_5.1) γ r16_5.2.1 r16_5.2.2 = true := by decide +kernel
theorem c16_6 : F.repChkAG (Q.tab r16_6.1) γ r16_6.2.1 r16_6.2.2 = true := by decide +kernel
theorem c16_7 : F.repChkAG (Q.tab r16_7.1) γ r16_7.2.1 r16_7.2.2 = true := by decide +kernel
theorem c16_8 : F.repChkAG (Q.tab r16_8.1) γ r16_8.2.1 r16_8.2.2 = true := by decide +kernel
theorem c16_9 : F.repChkAG (Q.tab r16_9.1) γ r16_9.2.1 r16_9.2.2 = true := by decide +kernel
theorem c16_10 : F.repChkAG (Q.tab r16_10.1) γ r16_10.2.1 r16_10.2.2 = true := by decide +kernel

def D16 : List (ℕ × (ℤ × ℤ) × RepData) := [r16_0, r16_1, r16_2, r16_3, r16_4, r16_5, r16_6, r16_7, r16_8, r16_9, r16_10]

theorem chkA16 : D16.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D16, List.all_cons, List.all_nil, c16_0, c16_1, c16_2, c16_3, c16_4, c16_5, c16_6, c16_7, c16_8, c16_9, c16_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
