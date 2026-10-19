module

public import Cryptarchia.Prob.Certs.E20D11G.R73
meta import Cryptarchia.Prob.Certs.E20D11G.R73

/-! # E20D11G: (group, representative) entries 847 to 857, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r77_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 55 (0, 0))
def r77_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 56 (0, 0))
def r77_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 57 (0, 0))
def r77_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 58 (0, 0))
def r77_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 59 (0, 0))
def r77_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 60 (0, 0))
def r77_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 61 (0, 0))
def r77_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 62 (0, 0))
def r77_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 63 (0, 0))
def r77_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 64 (0, 0))
def r77_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 65 (0, 0))

theorem c77_0 : F.repChkAG (Q.tab r77_0.1) γ r77_0.2.1 r77_0.2.2 = true := by decide +kernel
theorem c77_1 : F.repChkAG (Q.tab r77_1.1) γ r77_1.2.1 r77_1.2.2 = true := by decide +kernel
theorem c77_2 : F.repChkAG (Q.tab r77_2.1) γ r77_2.2.1 r77_2.2.2 = true := by decide +kernel
theorem c77_3 : F.repChkAG (Q.tab r77_3.1) γ r77_3.2.1 r77_3.2.2 = true := by decide +kernel
theorem c77_4 : F.repChkAG (Q.tab r77_4.1) γ r77_4.2.1 r77_4.2.2 = true := by decide +kernel
theorem c77_5 : F.repChkAG (Q.tab r77_5.1) γ r77_5.2.1 r77_5.2.2 = true := by decide +kernel
theorem c77_6 : F.repChkAG (Q.tab r77_6.1) γ r77_6.2.1 r77_6.2.2 = true := by decide +kernel
theorem c77_7 : F.repChkAG (Q.tab r77_7.1) γ r77_7.2.1 r77_7.2.2 = true := by decide +kernel
theorem c77_8 : F.repChkAG (Q.tab r77_8.1) γ r77_8.2.1 r77_8.2.2 = true := by decide +kernel
theorem c77_9 : F.repChkAG (Q.tab r77_9.1) γ r77_9.2.1 r77_9.2.2 = true := by decide +kernel
theorem c77_10 : F.repChkAG (Q.tab r77_10.1) γ r77_10.2.1 r77_10.2.2 = true := by decide +kernel

def D77 : List (ℕ × (ℤ × ℤ) × RepData) := [r77_0, r77_1, r77_2, r77_3, r77_4, r77_5, r77_6, r77_7, r77_8, r77_9, r77_10]

theorem chkA77 : D77.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D77, List.all_cons, List.all_nil, c77_0, c77_1, c77_2, c77_3, c77_4, c77_5, c77_6, c77_7, c77_8, c77_9, c77_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
