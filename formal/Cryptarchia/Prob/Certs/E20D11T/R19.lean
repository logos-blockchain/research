module

public import Cryptarchia.Prob.Certs.E20D11T.R15
meta import Cryptarchia.Prob.Certs.E20D11T.R15

/-! # E20D11T: representatives 209 to 219, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r19_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 209 (0, 0))
def r19_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 210 (0, 0))
def r19_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 211 (0, 0))
def r19_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 212 (0, 0))
def r19_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 213 (0, 0))
def r19_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 214 (0, 0))
def r19_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 215 (0, 0))
def r19_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 216 (0, 0))
def r19_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 217 (0, 0))
def r19_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 218 (0, 0))
def r19_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 219 (0, 0))

theorem c19_0 : F.repChkA Q r19_0.1 r19_0.2 = true := by decide +kernel
theorem c19_1 : F.repChkA Q r19_1.1 r19_1.2 = true := by decide +kernel
theorem c19_2 : F.repChkA Q r19_2.1 r19_2.2 = true := by decide +kernel
theorem c19_3 : F.repChkA Q r19_3.1 r19_3.2 = true := by decide +kernel
theorem c19_4 : F.repChkA Q r19_4.1 r19_4.2 = true := by decide +kernel
theorem c19_5 : F.repChkA Q r19_5.1 r19_5.2 = true := by decide +kernel
theorem c19_6 : F.repChkA Q r19_6.1 r19_6.2 = true := by decide +kernel
theorem c19_7 : F.repChkA Q r19_7.1 r19_7.2 = true := by decide +kernel
theorem c19_8 : F.repChkA Q r19_8.1 r19_8.2 = true := by decide +kernel
theorem c19_9 : F.repChkA Q r19_9.1 r19_9.2 = true := by decide +kernel
theorem c19_10 : F.repChkA Q r19_10.1 r19_10.2 = true := by decide +kernel

def D19 : List ((ℤ × ℤ) × RepData) := [r19_0, r19_1, r19_2, r19_3, r19_4, r19_5, r19_6, r19_7, r19_8, r19_9, r19_10]

theorem chkA19 : D19.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D19, List.all_cons, List.all_nil, c19_0, c19_1, c19_2, c19_3, c19_4, c19_5, c19_6, c19_7, c19_8, c19_9, c19_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T
