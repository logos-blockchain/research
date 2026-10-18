module

public import Cryptarchia.Prob.Certs.E20D11T.Tab
meta import Cryptarchia.Prob.Certs.E20D11T.Tab

/-! # E20D11T: representatives 33 to 43, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r3_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 33 (0, 0))
def r3_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 34 (0, 0))
def r3_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 35 (0, 0))
def r3_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 36 (0, 0))
def r3_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 37 (0, 0))
def r3_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 38 (0, 0))
def r3_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 39 (0, 0))
def r3_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 40 (0, 0))
def r3_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 41 (0, 0))
def r3_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 42 (0, 0))
def r3_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 43 (0, 0))

theorem c3_0 : F.repChkA Q r3_0.1 r3_0.2 = true := by decide +kernel
theorem c3_1 : F.repChkA Q r3_1.1 r3_1.2 = true := by decide +kernel
theorem c3_2 : F.repChkA Q r3_2.1 r3_2.2 = true := by decide +kernel
theorem c3_3 : F.repChkA Q r3_3.1 r3_3.2 = true := by decide +kernel
theorem c3_4 : F.repChkA Q r3_4.1 r3_4.2 = true := by decide +kernel
theorem c3_5 : F.repChkA Q r3_5.1 r3_5.2 = true := by decide +kernel
theorem c3_6 : F.repChkA Q r3_6.1 r3_6.2 = true := by decide +kernel
theorem c3_7 : F.repChkA Q r3_7.1 r3_7.2 = true := by decide +kernel
theorem c3_8 : F.repChkA Q r3_8.1 r3_8.2 = true := by decide +kernel
theorem c3_9 : F.repChkA Q r3_9.1 r3_9.2 = true := by decide +kernel
theorem c3_10 : F.repChkA Q r3_10.1 r3_10.2 = true := by decide +kernel

def D3 : List ((ℤ × ℤ) × RepData) := [r3_0, r3_1, r3_2, r3_3, r3_4, r3_5, r3_6, r3_7, r3_8, r3_9, r3_10]

theorem chkA3 : D3.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D3, List.all_cons, List.all_nil, c3_0, c3_1, c3_2, c3_3, c3_4, c3_5, c3_6, c3_7, c3_8, c3_9, c3_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T
