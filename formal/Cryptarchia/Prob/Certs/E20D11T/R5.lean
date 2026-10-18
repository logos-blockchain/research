module

public import Cryptarchia.Prob.Certs.E20D11T.R1
meta import Cryptarchia.Prob.Certs.E20D11T.R1

/-! # E20D11T: representatives 55 to 65, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r5_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 55 (0, 0))
def r5_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 56 (0, 0))
def r5_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 57 (0, 0))
def r5_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 58 (0, 0))
def r5_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 59 (0, 0))
def r5_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 60 (0, 0))
def r5_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 61 (0, 0))
def r5_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 62 (0, 0))
def r5_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 63 (0, 0))
def r5_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 64 (0, 0))
def r5_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 65 (0, 0))

theorem c5_0 : F.repChkA Q r5_0.1 r5_0.2 = true := by decide +kernel
theorem c5_1 : F.repChkA Q r5_1.1 r5_1.2 = true := by decide +kernel
theorem c5_2 : F.repChkA Q r5_2.1 r5_2.2 = true := by decide +kernel
theorem c5_3 : F.repChkA Q r5_3.1 r5_3.2 = true := by decide +kernel
theorem c5_4 : F.repChkA Q r5_4.1 r5_4.2 = true := by decide +kernel
theorem c5_5 : F.repChkA Q r5_5.1 r5_5.2 = true := by decide +kernel
theorem c5_6 : F.repChkA Q r5_6.1 r5_6.2 = true := by decide +kernel
theorem c5_7 : F.repChkA Q r5_7.1 r5_7.2 = true := by decide +kernel
theorem c5_8 : F.repChkA Q r5_8.1 r5_8.2 = true := by decide +kernel
theorem c5_9 : F.repChkA Q r5_9.1 r5_9.2 = true := by decide +kernel
theorem c5_10 : F.repChkA Q r5_10.1 r5_10.2 = true := by decide +kernel

def D5 : List ((ℤ × ℤ) × RepData) := [r5_0, r5_1, r5_2, r5_3, r5_4, r5_5, r5_6, r5_7, r5_8, r5_9, r5_10]

theorem chkA5 : D5.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D5, List.all_cons, List.all_nil, c5_0, c5_1, c5_2, c5_3, c5_4, c5_5, c5_6, c5_7, c5_8, c5_9, c5_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T
