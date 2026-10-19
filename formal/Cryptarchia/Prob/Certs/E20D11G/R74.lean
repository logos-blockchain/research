module

public import Cryptarchia.Prob.Certs.E20D11G.R70
meta import Cryptarchia.Prob.Certs.E20D11G.R70

/-! # E20D11G: (group, representative) entries 814 to 824, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r74_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 22 (0, 0))
def r74_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 23 (0, 0))
def r74_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 24 (0, 0))
def r74_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 25 (0, 0))
def r74_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 26 (0, 0))
def r74_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 27 (0, 0))
def r74_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 28 (0, 0))
def r74_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 29 (0, 0))
def r74_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 30 (0, 0))
def r74_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 31 (0, 0))
def r74_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 32 (0, 0))

theorem c74_0 : F.repChkAG (Q.tab r74_0.1) γ r74_0.2.1 r74_0.2.2 = true := by decide +kernel
theorem c74_1 : F.repChkAG (Q.tab r74_1.1) γ r74_1.2.1 r74_1.2.2 = true := by decide +kernel
theorem c74_2 : F.repChkAG (Q.tab r74_2.1) γ r74_2.2.1 r74_2.2.2 = true := by decide +kernel
theorem c74_3 : F.repChkAG (Q.tab r74_3.1) γ r74_3.2.1 r74_3.2.2 = true := by decide +kernel
theorem c74_4 : F.repChkAG (Q.tab r74_4.1) γ r74_4.2.1 r74_4.2.2 = true := by decide +kernel
theorem c74_5 : F.repChkAG (Q.tab r74_5.1) γ r74_5.2.1 r74_5.2.2 = true := by decide +kernel
theorem c74_6 : F.repChkAG (Q.tab r74_6.1) γ r74_6.2.1 r74_6.2.2 = true := by decide +kernel
theorem c74_7 : F.repChkAG (Q.tab r74_7.1) γ r74_7.2.1 r74_7.2.2 = true := by decide +kernel
theorem c74_8 : F.repChkAG (Q.tab r74_8.1) γ r74_8.2.1 r74_8.2.2 = true := by decide +kernel
theorem c74_9 : F.repChkAG (Q.tab r74_9.1) γ r74_9.2.1 r74_9.2.2 = true := by decide +kernel
theorem c74_10 : F.repChkAG (Q.tab r74_10.1) γ r74_10.2.1 r74_10.2.2 = true := by decide +kernel

def D74 : List (ℕ × (ℤ × ℤ) × RepData) := [r74_0, r74_1, r74_2, r74_3, r74_4, r74_5, r74_6, r74_7, r74_8, r74_9, r74_10]

theorem chkA74 : D74.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D74, List.all_cons, List.all_nil, c74_0, c74_1, c74_2, c74_3, c74_4, c74_5, c74_6, c74_7, c74_8, c74_9, c74_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
