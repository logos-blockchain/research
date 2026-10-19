module

public import Cryptarchia.Prob.Certs.E20D11G.R7
meta import Cryptarchia.Prob.Certs.E20D11G.R7

/-! # E20D11G: (group, representative) entries 121 to 131, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r11_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 121 (0, 0))
def r11_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 122 (0, 0))
def r11_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 123 (0, 0))
def r11_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 124 (0, 0))
def r11_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 125 (0, 0))
def r11_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 126 (0, 0))
def r11_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 127 (0, 0))
def r11_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 128 (0, 0))
def r11_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 129 (0, 0))
def r11_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 130 (0, 0))
def r11_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 131 (0, 0))

theorem c11_0 : F.repChkAG (Q.tab r11_0.1) γ r11_0.2.1 r11_0.2.2 = true := by decide +kernel
theorem c11_1 : F.repChkAG (Q.tab r11_1.1) γ r11_1.2.1 r11_1.2.2 = true := by decide +kernel
theorem c11_2 : F.repChkAG (Q.tab r11_2.1) γ r11_2.2.1 r11_2.2.2 = true := by decide +kernel
theorem c11_3 : F.repChkAG (Q.tab r11_3.1) γ r11_3.2.1 r11_3.2.2 = true := by decide +kernel
theorem c11_4 : F.repChkAG (Q.tab r11_4.1) γ r11_4.2.1 r11_4.2.2 = true := by decide +kernel
theorem c11_5 : F.repChkAG (Q.tab r11_5.1) γ r11_5.2.1 r11_5.2.2 = true := by decide +kernel
theorem c11_6 : F.repChkAG (Q.tab r11_6.1) γ r11_6.2.1 r11_6.2.2 = true := by decide +kernel
theorem c11_7 : F.repChkAG (Q.tab r11_7.1) γ r11_7.2.1 r11_7.2.2 = true := by decide +kernel
theorem c11_8 : F.repChkAG (Q.tab r11_8.1) γ r11_8.2.1 r11_8.2.2 = true := by decide +kernel
theorem c11_9 : F.repChkAG (Q.tab r11_9.1) γ r11_9.2.1 r11_9.2.2 = true := by decide +kernel
theorem c11_10 : F.repChkAG (Q.tab r11_10.1) γ r11_10.2.1 r11_10.2.2 = true := by decide +kernel

def D11 : List (ℕ × (ℤ × ℤ) × RepData) := [r11_0, r11_1, r11_2, r11_3, r11_4, r11_5, r11_6, r11_7, r11_8, r11_9, r11_10]

theorem chkA11 : D11.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D11, List.all_cons, List.all_nil, c11_0, c11_1, c11_2, c11_3, c11_4, c11_5, c11_6, c11_7, c11_8, c11_9, c11_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
