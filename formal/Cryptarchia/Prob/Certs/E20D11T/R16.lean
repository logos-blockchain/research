module

public import Cryptarchia.Prob.Certs.E20D11T.R12
meta import Cryptarchia.Prob.Certs.E20D11T.R12

/-! # E20D11T: representatives 176 to 186, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r16_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 176 (0, 0))
def r16_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 177 (0, 0))
def r16_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 178 (0, 0))
def r16_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 179 (0, 0))
def r16_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 180 (0, 0))
def r16_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 181 (0, 0))
def r16_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 182 (0, 0))
def r16_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 183 (0, 0))
def r16_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 184 (0, 0))
def r16_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 185 (0, 0))
def r16_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 186 (0, 0))

theorem c16_0 : F.repChkA Q r16_0.1 r16_0.2 = true := by decide +kernel
theorem c16_1 : F.repChkA Q r16_1.1 r16_1.2 = true := by decide +kernel
theorem c16_2 : F.repChkA Q r16_2.1 r16_2.2 = true := by decide +kernel
theorem c16_3 : F.repChkA Q r16_3.1 r16_3.2 = true := by decide +kernel
theorem c16_4 : F.repChkA Q r16_4.1 r16_4.2 = true := by decide +kernel
theorem c16_5 : F.repChkA Q r16_5.1 r16_5.2 = true := by decide +kernel
theorem c16_6 : F.repChkA Q r16_6.1 r16_6.2 = true := by decide +kernel
theorem c16_7 : F.repChkA Q r16_7.1 r16_7.2 = true := by decide +kernel
theorem c16_8 : F.repChkA Q r16_8.1 r16_8.2 = true := by decide +kernel
theorem c16_9 : F.repChkA Q r16_9.1 r16_9.2 = true := by decide +kernel
theorem c16_10 : F.repChkA Q r16_10.1 r16_10.2 = true := by decide +kernel

def D16 : List ((ℤ × ℤ) × RepData) := [r16_0, r16_1, r16_2, r16_3, r16_4, r16_5, r16_6, r16_7, r16_8, r16_9, r16_10]

theorem chkA16 : D16.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D16, List.all_cons, List.all_nil, c16_0, c16_1, c16_2, c16_3, c16_4, c16_5, c16_6, c16_7, c16_8, c16_9, c16_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T
