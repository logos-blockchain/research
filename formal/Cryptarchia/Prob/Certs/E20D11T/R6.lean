module

public import Cryptarchia.Prob.Certs.E20D11T.R2
meta import Cryptarchia.Prob.Certs.E20D11T.R2

/-! # E20D11T: representatives 66 to 76, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r6_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 66 (0, 0))
def r6_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 67 (0, 0))
def r6_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 68 (0, 0))
def r6_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 69 (0, 0))
def r6_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 70 (0, 0))
def r6_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 71 (0, 0))
def r6_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 72 (0, 0))
def r6_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 73 (0, 0))
def r6_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 74 (0, 0))
def r6_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 75 (0, 0))
def r6_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 76 (0, 0))

theorem c6_0 : F.repChkA Q r6_0.1 r6_0.2 = true := by decide +kernel
theorem c6_1 : F.repChkA Q r6_1.1 r6_1.2 = true := by decide +kernel
theorem c6_2 : F.repChkA Q r6_2.1 r6_2.2 = true := by decide +kernel
theorem c6_3 : F.repChkA Q r6_3.1 r6_3.2 = true := by decide +kernel
theorem c6_4 : F.repChkA Q r6_4.1 r6_4.2 = true := by decide +kernel
theorem c6_5 : F.repChkA Q r6_5.1 r6_5.2 = true := by decide +kernel
theorem c6_6 : F.repChkA Q r6_6.1 r6_6.2 = true := by decide +kernel
theorem c6_7 : F.repChkA Q r6_7.1 r6_7.2 = true := by decide +kernel
theorem c6_8 : F.repChkA Q r6_8.1 r6_8.2 = true := by decide +kernel
theorem c6_9 : F.repChkA Q r6_9.1 r6_9.2 = true := by decide +kernel
theorem c6_10 : F.repChkA Q r6_10.1 r6_10.2 = true := by decide +kernel

def D6 : List ((ℤ × ℤ) × RepData) := [r6_0, r6_1, r6_2, r6_3, r6_4, r6_5, r6_6, r6_7, r6_8, r6_9, r6_10]

theorem chkA6 : D6.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D6, List.all_cons, List.all_nil, c6_0, c6_1, c6_2, c6_3, c6_4, c6_5, c6_6, c6_7, c6_8, c6_9, c6_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T
