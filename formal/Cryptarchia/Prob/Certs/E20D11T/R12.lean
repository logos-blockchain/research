module

public import Cryptarchia.Prob.Certs.E20D11T.R8
meta import Cryptarchia.Prob.Certs.E20D11T.R8

/-! # E20D11T: representatives 132 to 142, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r12_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 132 (0, 0))
def r12_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 133 (0, 0))
def r12_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 134 (0, 0))
def r12_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 135 (0, 0))
def r12_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 136 (0, 0))
def r12_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 137 (0, 0))
def r12_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 138 (0, 0))
def r12_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 139 (0, 0))
def r12_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 140 (0, 0))
def r12_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 141 (0, 0))
def r12_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 142 (0, 0))

theorem c12_0 : F.repChkA Q r12_0.1 r12_0.2 = true := by decide +kernel
theorem c12_1 : F.repChkA Q r12_1.1 r12_1.2 = true := by decide +kernel
theorem c12_2 : F.repChkA Q r12_2.1 r12_2.2 = true := by decide +kernel
theorem c12_3 : F.repChkA Q r12_3.1 r12_3.2 = true := by decide +kernel
theorem c12_4 : F.repChkA Q r12_4.1 r12_4.2 = true := by decide +kernel
theorem c12_5 : F.repChkA Q r12_5.1 r12_5.2 = true := by decide +kernel
theorem c12_6 : F.repChkA Q r12_6.1 r12_6.2 = true := by decide +kernel
theorem c12_7 : F.repChkA Q r12_7.1 r12_7.2 = true := by decide +kernel
theorem c12_8 : F.repChkA Q r12_8.1 r12_8.2 = true := by decide +kernel
theorem c12_9 : F.repChkA Q r12_9.1 r12_9.2 = true := by decide +kernel
theorem c12_10 : F.repChkA Q r12_10.1 r12_10.2 = true := by decide +kernel

def D12 : List ((ℤ × ℤ) × RepData) := [r12_0, r12_1, r12_2, r12_3, r12_4, r12_5, r12_6, r12_7, r12_8, r12_9, r12_10]

theorem chkA12 : D12.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D12, List.all_cons, List.all_nil, c12_0, c12_1, c12_2, c12_3, c12_4, c12_5, c12_6, c12_7, c12_8, c12_9, c12_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T
