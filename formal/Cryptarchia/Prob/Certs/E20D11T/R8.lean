module

public import Cryptarchia.Prob.Certs.E20D11T.R4
meta import Cryptarchia.Prob.Certs.E20D11T.R4

/-! # E20D11T: representatives 88 to 98, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r8_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 88 (0, 0))
def r8_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 89 (0, 0))
def r8_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 90 (0, 0))
def r8_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 91 (0, 0))
def r8_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 92 (0, 0))
def r8_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 93 (0, 0))
def r8_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 94 (0, 0))
def r8_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 95 (0, 0))
def r8_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 96 (0, 0))
def r8_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 97 (0, 0))
def r8_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 98 (0, 0))

theorem c8_0 : F.repChkA Q r8_0.1 r8_0.2 = true := by decide +kernel
theorem c8_1 : F.repChkA Q r8_1.1 r8_1.2 = true := by decide +kernel
theorem c8_2 : F.repChkA Q r8_2.1 r8_2.2 = true := by decide +kernel
theorem c8_3 : F.repChkA Q r8_3.1 r8_3.2 = true := by decide +kernel
theorem c8_4 : F.repChkA Q r8_4.1 r8_4.2 = true := by decide +kernel
theorem c8_5 : F.repChkA Q r8_5.1 r8_5.2 = true := by decide +kernel
theorem c8_6 : F.repChkA Q r8_6.1 r8_6.2 = true := by decide +kernel
theorem c8_7 : F.repChkA Q r8_7.1 r8_7.2 = true := by decide +kernel
theorem c8_8 : F.repChkA Q r8_8.1 r8_8.2 = true := by decide +kernel
theorem c8_9 : F.repChkA Q r8_9.1 r8_9.2 = true := by decide +kernel
theorem c8_10 : F.repChkA Q r8_10.1 r8_10.2 = true := by decide +kernel

def D8 : List ((ℤ × ℤ) × RepData) := [r8_0, r8_1, r8_2, r8_3, r8_4, r8_5, r8_6, r8_7, r8_8, r8_9, r8_10]

theorem chkA8 : D8.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D8, List.all_cons, List.all_nil, c8_0, c8_1, c8_2, c8_3, c8_4, c8_5, c8_6, c8_7, c8_8, c8_9, c8_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T
