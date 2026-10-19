module

public import Cryptarchia.Prob.Certs.E20D11G.R64
meta import Cryptarchia.Prob.Certs.E20D11G.R64

/-! # E20D11G: (group, representative) entries 748 to 758, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r68_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 220 (0, 0))
def r68_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 221 (0, 0))
def r68_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 222 (0, 0))
def r68_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 223 (0, 0))
def r68_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 224 (0, 0))
def r68_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 225 (0, 0))
def r68_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 226 (0, 0))
def r68_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 227 (0, 0))
def r68_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 228 (0, 0))
def r68_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 229 (0, 0))
def r68_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 230 (0, 0))

theorem c68_0 : F.repChkAG (Q.tab r68_0.1) γ r68_0.2.1 r68_0.2.2 = true := by decide +kernel
theorem c68_1 : F.repChkAG (Q.tab r68_1.1) γ r68_1.2.1 r68_1.2.2 = true := by decide +kernel
theorem c68_2 : F.repChkAG (Q.tab r68_2.1) γ r68_2.2.1 r68_2.2.2 = true := by decide +kernel
theorem c68_3 : F.repChkAG (Q.tab r68_3.1) γ r68_3.2.1 r68_3.2.2 = true := by decide +kernel
theorem c68_4 : F.repChkAG (Q.tab r68_4.1) γ r68_4.2.1 r68_4.2.2 = true := by decide +kernel
theorem c68_5 : F.repChkAG (Q.tab r68_5.1) γ r68_5.2.1 r68_5.2.2 = true := by decide +kernel
theorem c68_6 : F.repChkAG (Q.tab r68_6.1) γ r68_6.2.1 r68_6.2.2 = true := by decide +kernel
theorem c68_7 : F.repChkAG (Q.tab r68_7.1) γ r68_7.2.1 r68_7.2.2 = true := by decide +kernel
theorem c68_8 : F.repChkAG (Q.tab r68_8.1) γ r68_8.2.1 r68_8.2.2 = true := by decide +kernel
theorem c68_9 : F.repChkAG (Q.tab r68_9.1) γ r68_9.2.1 r68_9.2.2 = true := by decide +kernel
theorem c68_10 : F.repChkAG (Q.tab r68_10.1) γ r68_10.2.1 r68_10.2.2 = true := by decide +kernel

def D68 : List (ℕ × (ℤ × ℤ) × RepData) := [r68_0, r68_1, r68_2, r68_3, r68_4, r68_5, r68_6, r68_7, r68_8, r68_9, r68_10]

theorem chkA68 : D68.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D68, List.all_cons, List.all_nil, c68_0, c68_1, c68_2, c68_3, c68_4, c68_5, c68_6, c68_7, c68_8, c68_9, c68_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G
