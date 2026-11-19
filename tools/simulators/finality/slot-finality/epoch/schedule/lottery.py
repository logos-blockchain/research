"""Blend's reward lottery by the length of the epoch (SCHEDULE.md, 6).

Rules as blend-protocol.md prints them (Core Quota, Activity Proof, Activity Threshold):
  Q_C = ceil(3 E / N) for E rounds and N core nodes (C = E F_C, F_C = 1, beta_C = 3, R_C = 0)
  Q_C^Total = N Q_C; chi = ceil(log2(Q_C^Total + 1)); nu = ceil(log2(N + 1)); theta = 1
  A = max(0, chi - nu - theta); eps = 8 ceil(chi / 8)
A token proves activity when the Hamming distance of its eps-bit digest to that of the next epoch's
randomness is at most A; digests are taken as uniform and independent. A core node holds Q_C tokens
(its share of the cover traffic). p is its chance of a base reward in an epoch.
Usage: python lottery.py > out_lottery.txt
"""
import math

EPOCHS = ((648000, "180 h"), (360000, "100 h"), (324000, "90 h"), (252000, "70 h"), (216000, "60 h"), (144000, "40 h"),
          (126000, "35 h"), (108000, "30 h"))


def lottery(E, N):
    QC = -(-(3 * E) // N)
    QT = N * QC
    chi, nu = QT.bit_length(), N.bit_length()        # bit_length(x) = ceil(log2(x + 1))
    A = max(0, chi - nu - 1)
    eps = -(-chi // 8) * 8
    q = sum(math.comb(eps, i) for i in range(A + 1)) / 2 ** eps
    return -math.expm1(QC * math.log1p(-q)), chi, A


def threshold(E, N):
    """A alone. From N = 3E on, Q_C = 1 and chi = nu, so A = 0 for every larger N."""
    return max(0, (N * -(-(3 * E) // N)).bit_length() - N.bit_length() - 1)


print("epoch | chi at 10,000 core nodes | p at 3,000, 10,000 and 30,000 | least N with p < 0.5, < 0.01 | least N with A = 0 | "
      "least N from which A = 0 for every larger N")
for E, name in EPOCHS:
    p = [lottery(E, N)[0] for N in (3000, 10000, 30000)]
    n50 = next(N for N in range(2, 2 ** 21) if lottery(E, N)[0] < 0.5)
    n01 = next(N for N in range(2, 2 ** 21) if lottery(E, N)[0] < 0.01)
    a0 = next(N for N in range(2, 2 ** 21) if lottery(E, N)[2] == 0)
    a0_all = 1 + max(N for N in range(2, 3 * E) if threshold(E, N) > 0)
    print(f"{name:>6} ({E}) | {lottery(E, 10000)[1]} | {p[0]:.4f}, {p[1]:.4f}, {p[2]:.4f} | {n50}, {n01} | {a0} | {a0_all}")
