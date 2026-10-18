module

public import Cryptarchia.Prob.Certs.E20D11T.R11
meta import Cryptarchia.Prob.Certs.E20D11T.R11

/-! # E20D11T: representatives 165 to 175, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r15_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 165 (0, 0))
def r15_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 166 (0, 0))
def r15_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 167 (0, 0))
def r15_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 168 (0, 0))
def r15_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 169 (0, 0))
def r15_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 170 (0, 0))
def r15_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 171 (0, 0))
def r15_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 172 (0, 0))
def r15_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 173 (0, 0))
def r15_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 174 (0, 0))
def r15_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 175 (0, 0))

theorem c15_0 : F.repChkA Q r15_0.1 r15_0.2 = true := by decide +kernel
theorem c15_1 : F.repChkA Q r15_1.1 r15_1.2 = true := by decide +kernel
theorem c15_2 : F.repChkA Q r15_2.1 r15_2.2 = true := by decide +kernel
theorem c15_3 : F.repChkA Q r15_3.1 r15_3.2 = true := by decide +kernel
theorem c15_4 : F.repChkA Q r15_4.1 r15_4.2 = true := by decide +kernel
theorem c15_5 : F.repChkA Q r15_5.1 r15_5.2 = true := by decide +kernel
theorem c15_6 : F.repChkA Q r15_6.1 r15_6.2 = true := by decide +kernel
theorem c15_7 : F.repChkA Q r15_7.1 r15_7.2 = true := by decide +kernel
theorem c15_8 : F.repChkA Q r15_8.1 r15_8.2 = true := by decide +kernel
theorem c15_9 : F.repChkA Q r15_9.1 r15_9.2 = true := by decide +kernel
theorem c15_10 : F.repChkA Q r15_10.1 r15_10.2 = true := by decide +kernel

def D15 : List ((ℤ × ℤ) × RepData) := [r15_0, r15_1, r15_2, r15_3, r15_4, r15_5, r15_6, r15_7, r15_8, r15_9, r15_10]

theorem chkA15 : D15.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D15, List.all_cons, List.all_nil, c15_0, c15_1, c15_2, c15_3, c15_4, c15_5, c15_6, c15_7, c15_8, c15_9, c15_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T
