module

public import Cryptarchia.Prob.Certs.E20D11T.R19
meta import Cryptarchia.Prob.Certs.E20D11T.R19

/-! # E20D11T: representatives 253 to 263, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r23_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 253 (0, 0))
def r23_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 254 (0, 0))
def r23_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 255 (0, 0))
def r23_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 256 (0, 0))
def r23_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 257 (0, 0))
def r23_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 258 (0, 0))
def r23_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 259 (0, 0))
def r23_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 260 (0, 0))
def r23_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 261 (0, 0))
def r23_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 262 (0, 0))
def r23_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 263 (0, 0))

theorem c23_0 : F.repChkA Q r23_0.1 r23_0.2 = true := by decide +kernel
theorem c23_1 : F.repChkA Q r23_1.1 r23_1.2 = true := by decide +kernel
theorem c23_2 : F.repChkA Q r23_2.1 r23_2.2 = true := by decide +kernel
theorem c23_3 : F.repChkA Q r23_3.1 r23_3.2 = true := by decide +kernel
theorem c23_4 : F.repChkA Q r23_4.1 r23_4.2 = true := by decide +kernel
theorem c23_5 : F.repChkA Q r23_5.1 r23_5.2 = true := by decide +kernel
theorem c23_6 : F.repChkA Q r23_6.1 r23_6.2 = true := by decide +kernel
theorem c23_7 : F.repChkA Q r23_7.1 r23_7.2 = true := by decide +kernel
theorem c23_8 : F.repChkA Q r23_8.1 r23_8.2 = true := by decide +kernel
theorem c23_9 : F.repChkA Q r23_9.1 r23_9.2 = true := by decide +kernel
theorem c23_10 : F.repChkA Q r23_10.1 r23_10.2 = true := by decide +kernel

def D23 : List ((ℤ × ℤ) × RepData) := [r23_0, r23_1, r23_2, r23_3, r23_4, r23_5, r23_6, r23_7, r23_8, r23_9, r23_10]

theorem chkA23 : D23.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D23, List.all_cons, List.all_nil, c23_0, c23_1, c23_2, c23_3, c23_4, c23_5, c23_6, c23_7, c23_8, c23_9, c23_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T
