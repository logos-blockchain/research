module

public import Cryptarchia.Prob.Certs.E20D11T.R17
meta import Cryptarchia.Prob.Certs.E20D11T.R17

/-! # E20D11T: representatives 231 to 241, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r21_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 231 (0, 0))
def r21_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 232 (0, 0))
def r21_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 233 (0, 0))
def r21_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 234 (0, 0))
def r21_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 235 (0, 0))
def r21_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 236 (0, 0))
def r21_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 237 (0, 0))
def r21_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 238 (0, 0))
def r21_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 239 (0, 0))
def r21_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 240 (0, 0))
def r21_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 241 (0, 0))

theorem c21_0 : F.repChkA Q r21_0.1 r21_0.2 = true := by decide +kernel
theorem c21_1 : F.repChkA Q r21_1.1 r21_1.2 = true := by decide +kernel
theorem c21_2 : F.repChkA Q r21_2.1 r21_2.2 = true := by decide +kernel
theorem c21_3 : F.repChkA Q r21_3.1 r21_3.2 = true := by decide +kernel
theorem c21_4 : F.repChkA Q r21_4.1 r21_4.2 = true := by decide +kernel
theorem c21_5 : F.repChkA Q r21_5.1 r21_5.2 = true := by decide +kernel
theorem c21_6 : F.repChkA Q r21_6.1 r21_6.2 = true := by decide +kernel
theorem c21_7 : F.repChkA Q r21_7.1 r21_7.2 = true := by decide +kernel
theorem c21_8 : F.repChkA Q r21_8.1 r21_8.2 = true := by decide +kernel
theorem c21_9 : F.repChkA Q r21_9.1 r21_9.2 = true := by decide +kernel
theorem c21_10 : F.repChkA Q r21_10.1 r21_10.2 = true := by decide +kernel

def D21 : List ((ℤ × ℤ) × RepData) := [r21_0, r21_1, r21_2, r21_3, r21_4, r21_5, r21_6, r21_7, r21_8, r21_9, r21_10]

theorem chkA21 : D21.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D21, List.all_cons, List.all_nil, c21_0, c21_1, c21_2, c21_3, c21_4, c21_5, c21_6, c21_7, c21_8, c21_9, c21_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T
