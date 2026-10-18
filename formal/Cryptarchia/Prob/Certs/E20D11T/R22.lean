module

public import Cryptarchia.Prob.Certs.E20D11T.R18
meta import Cryptarchia.Prob.Certs.E20D11T.R18

/-! # E20D11T: representatives 242 to 252, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r22_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 242 (0, 0))
def r22_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 243 (0, 0))
def r22_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 244 (0, 0))
def r22_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 245 (0, 0))
def r22_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 246 (0, 0))
def r22_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 247 (0, 0))
def r22_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 248 (0, 0))
def r22_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 249 (0, 0))
def r22_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 250 (0, 0))
def r22_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 251 (0, 0))
def r22_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 252 (0, 0))

theorem c22_0 : F.repChkA Q r22_0.1 r22_0.2 = true := by decide +kernel
theorem c22_1 : F.repChkA Q r22_1.1 r22_1.2 = true := by decide +kernel
theorem c22_2 : F.repChkA Q r22_2.1 r22_2.2 = true := by decide +kernel
theorem c22_3 : F.repChkA Q r22_3.1 r22_3.2 = true := by decide +kernel
theorem c22_4 : F.repChkA Q r22_4.1 r22_4.2 = true := by decide +kernel
theorem c22_5 : F.repChkA Q r22_5.1 r22_5.2 = true := by decide +kernel
theorem c22_6 : F.repChkA Q r22_6.1 r22_6.2 = true := by decide +kernel
theorem c22_7 : F.repChkA Q r22_7.1 r22_7.2 = true := by decide +kernel
theorem c22_8 : F.repChkA Q r22_8.1 r22_8.2 = true := by decide +kernel
theorem c22_9 : F.repChkA Q r22_9.1 r22_9.2 = true := by decide +kernel
theorem c22_10 : F.repChkA Q r22_10.1 r22_10.2 = true := by decide +kernel

def D22 : List ((ℤ × ℤ) × RepData) := [r22_0, r22_1, r22_2, r22_3, r22_4, r22_5, r22_6, r22_7, r22_8, r22_9, r22_10]

theorem chkA22 : D22.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D22, List.all_cons, List.all_nil, c22_0, c22_1, c22_2, c22_3, c22_4, c22_5, c22_6, c22_7, c22_8, c22_9, c22_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T
