module

public import Cryptarchia.Prob.Certs.E20D11T.R7
meta import Cryptarchia.Prob.Certs.E20D11T.R7

/-! # E20D11T: representatives 121 to 131, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r11_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 121 (0, 0))
def r11_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 122 (0, 0))
def r11_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 123 (0, 0))
def r11_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 124 (0, 0))
def r11_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 125 (0, 0))
def r11_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 126 (0, 0))
def r11_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 127 (0, 0))
def r11_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 128 (0, 0))
def r11_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 129 (0, 0))
def r11_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 130 (0, 0))
def r11_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 131 (0, 0))

theorem c11_0 : F.repChkA Q r11_0.1 r11_0.2 = true := by decide +kernel
theorem c11_1 : F.repChkA Q r11_1.1 r11_1.2 = true := by decide +kernel
theorem c11_2 : F.repChkA Q r11_2.1 r11_2.2 = true := by decide +kernel
theorem c11_3 : F.repChkA Q r11_3.1 r11_3.2 = true := by decide +kernel
theorem c11_4 : F.repChkA Q r11_4.1 r11_4.2 = true := by decide +kernel
theorem c11_5 : F.repChkA Q r11_5.1 r11_5.2 = true := by decide +kernel
theorem c11_6 : F.repChkA Q r11_6.1 r11_6.2 = true := by decide +kernel
theorem c11_7 : F.repChkA Q r11_7.1 r11_7.2 = true := by decide +kernel
theorem c11_8 : F.repChkA Q r11_8.1 r11_8.2 = true := by decide +kernel
theorem c11_9 : F.repChkA Q r11_9.1 r11_9.2 = true := by decide +kernel
theorem c11_10 : F.repChkA Q r11_10.1 r11_10.2 = true := by decide +kernel

def D11 : List ((ℤ × ℤ) × RepData) := [r11_0, r11_1, r11_2, r11_3, r11_4, r11_5, r11_6, r11_7, r11_8, r11_9, r11_10]

theorem chkA11 : D11.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D11, List.all_cons, List.all_nil, c11_0, c11_1, c11_2, c11_3, c11_4, c11_5, c11_6, c11_7, c11_8, c11_9, c11_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T
