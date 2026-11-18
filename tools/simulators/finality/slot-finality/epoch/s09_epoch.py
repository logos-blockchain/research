"""An epoch that suffices to keep every rule of the latest #533 with today's nonce (REVIEW.md,
statement 5.9 and section 10). The lower bounds on the least epoch are in s14_bracket.py.

The epoch is the sum of three spans:
  phase 1  G*:  the snapshot is final when the phase ends, but for a chance of 1e-9 (statement 5.4);
  phase 2  w_B: the chain keeps an honest block of the phase, but for 1e-9 (section 9, with the
                finality study's survival law; read from out_08_buffer.txt);
  phase 3  G*:  the nonce and the inferred stake are final at their first use, but for 1e-9.
G* = G*(x, d) is the least gap at which the bound of statement 5.4 is at most 1e-9, x the share of the
inferred stake that builds and d the delay of every block. The observation window of the stake
inference, P slots, lies in phases 1 and 2, so the epoch is max(P, G* + w_B) + G*.

Part A gives G* and the epoch by the share that builds, every block T_M = 15 slots late.
Part B gives them for the states the K row of the specification names, with a coalition of 30 % of
the total active stake that does not build.
Part C gives what each epoch costs: the share of targets whose race meets two nonces (6.2), the
noise of the inference at the window that fits (7.4), the floor at that noise (7.6), the chance per
epoch that noise alone passes the limit the RFCs state at 15 s (7.7), the wins a coalition gives up
to deflate the inference (7.8), and the least share at which 5.4 certifies each phase's value final in time.
Usage: python s09_epoch.py > out_09_epoch.txt   (after s08_buffer.py)
"""
import math
import os

from scipy.stats import binom

from common import CASES, EPOCH, F, H, PERIOD, PHASE_1, PHASE_2, PHASE_3, S_GEN, T_M, least_gap, least_share, pct, upper
from s06_inference import floor_with_noise, noise_average

HERE = os.path.dirname(os.path.abspath(__file__))
F_HAT = 0.033
R_STAR = math.log1p(-F_HAT) / math.log1p(-F)
YEAR = 365.25 * 86400
# the largest true active stake over the inferred stake at which K still holds 30 % at 15 s
LIMIT = {"10 h (#533)": 1.094, "18 h (base)": 1.593}      # RFC-533 line 61, RFC-532 line 74

SHARES = ((1.0, "all of the inferred stake builds"), (0.9, "a tenth does not build"), (0.7, "30 % does not build"),
          (0.5, "a half builds"), (0.25, "a quarter builds"))

ONE = (   # (state, share of the inferred stake that builds, delay, buffer of out_08_buffer.txt)
    ("no disturbance, 10 s", 0.7, 10, "30 %, no disturbance, 10 s"),
    ("every block T_M = 15 s late", 0.7, 15, "30 %, every honest block 15 s late"),
    ("a tenth of the honest stake offline, 10 s", 0.63 / 0.93, 10, "30 %, a tenth of the honest stake offline, 10 s"),
    ("deflated inference, 10 s", 1.0, 10, "30 %, deflated inference, 10 s"),
)
TWO = (
    ("15 s and a tenth of the honest stake offline", 0.63 / 0.93, 15, "30 %, 15 s and a tenth of the honest stake offline"),
    ("15 s and a deflated inference", 1.0, 15, "30 %, 15 s and a deflated inference"),
    ("a tenth offline and a deflated inference, 10 s", 1.0, 10, "30 %, a tenth of the honest stake offline and a deflated inference, 10 s"),
)
ROW = {"10 h (#533)": ONE, "18 h (base)": ONE + TWO}       # one disturbance at a time; two together at 18 h


def read_buffers():
    out, name = {}, None
    for line in open(os.path.join(HERE, "out_08_buffer.txt")):
        if ": coalition's share" in line:
            name = line.split(": coalition's share")[0]
        elif line.strip().startswith("w_B =") and name is not None:
            out[name] = int(line.split("=")[1].split("slots")[0])
    return out


def costs(name, K, phi, L1, L2, L3, P, tag):
    E = L1 + L2 + L3
    sd = math.sqrt((1 - F_HAT) / (P * F_HAT))
    miss = noise_average(phi, K, P, F_HAT, R_STAR)
    floor = floor_with_noise(K, P, F_HAT, R_STAR)
    fast = float(binom.cdf(math.ceil(R_STAR * P * F_HAT / LIMIT[name]) - 1, P, F_HAT))
    two = f"{100 * K / E:5.2f} %" if K <= E else "all"
    x1 = least_share(lambda p: upper(L1, K, phi, p, T_M))
    x3 = least_share(lambda p: upper(L3, K, phi, p, T_M))
    deflate = -math.expm1(0.3 * math.log1p(-F)) * P
    s1 = "none" if x1 is None else f"{pct(x1)} %"
    s3 = "none" if x3 is None else f"{pct(x3)} %"
    print(f"  {E / H:7.2f} = {L1 / H:6.2f} + {L2 / H:5.2f} + {L3 / H:6.2f} | {P / H:6.2f} | {s1}, {s3} | {two} | {YEAR / E:6.1f} | "
          f"{E / H:6.1f} to {2 * E / H:6.1f} | {(E + L3) / H:6.1f} | {100 * sd:.3f} % | {miss:.2e} | {floor} ({floor - phi:+d}) | {fast:.2e} | "
          f"{deflate:6.0f} | {E * F:7.0f}   [{tag}]")


if __name__ == "__main__":
    buffers = read_buffers()
    for name, (K, phi) in CASES.items():
        print(f"=== {name}: K = {K}, phi = {phi}; today's epoch {EPOCH / H:g} h; window P = {PERIOD / H:g} h ===")
        w15 = buffers["30 %, every honest block 15 s late"]
        print(f"A. by the share of the inferred stake that builds, every block {T_M} slots late; buffer w_B = {w15} slots = {w15 / H:.2f} h")
        print("   share that builds | G* (h) | epoch that suffices, window shortened to G* + w_B (h) | epoch that suffices, window kept at 108 h (h)")
        for x, label in SHARES:
            g = least_gap(K, phi, x, T_M)
            print(f"   {100 * x:5.1f} % ({label}) | {g / H:6.2f} | {(2 * g + w15) / H:7.2f} | {(max(PERIOD, g + w15) + g) / H:7.2f}")

        print("B. by the state of the K row; the coalition of 30 % of the total active stake does not build")
        print("   state | share of the inferred stake that builds | G* (slots, h) | w_B (slots, h)")
        g_max, w_max = 0, 0
        for state, x, d, key in ROW[name]:
            g, w = least_gap(K, phi, x, d), buffers[key]
            g_max, w_max = max(g_max, g), max(w_max, w)
            print(f"   {state} | {100 * x:6.2f} % | {g:6d} {g / H:6.2f} | {w:6d} {w / H:5.2f}")
        g_trans = least_gap(K, phi, 0.63, 10)
        print(f"   (a tenth of the honest stake offline before the inference corrects, 10 s: 63.00 % builds, G* = {g_trans} slots = {g_trans / H:.2f} h)")
        g_all = least_gap(K, phi, 1.0, 10)
        print(f"   (no disturbance and the coalition builds, 10 s: 100 % builds, G* = {g_all} slots = {g_all / H:.2f} h)")
        short_epoch = 2 * g_max + w_max
        kept_epoch = max(PERIOD, g_max + w_max) + g_max
        print(f"   largest G* = {g_max} slots = {g_max / H:.2f} h; largest w_B = {w_max} slots = {w_max / H:.2f} h")
        print(f"   epoch that suffices in every state: window shortened {short_epoch} slots = {short_epoch / H:.2f} h; "
              f"window kept {kept_epoch} slots = {kept_epoch / H:.2f} h")
        print(f"   Theorem 2 of Ouroboros Genesis as written asks R >= 6 s_gen = {6 * S_GEN / H:g} h; its proof's use asks a gap of 2 s_gen = {2 * S_GEN / H:g} h")

        print("C. what each schedule costs")
        print("   epoch = phase 1 + phase 2 + phase 3 (h) | window P (h) | least share for phase 1, phase 3 (15 s) | targets that meet two nonces | "
              "cut-offs a year | new stake waits (h) | longest time with no correction of the inference (h) | sd of the inferred stake | "
              f"P(miss the floor at K) | floor at 1e-9 | P(true/inferred > {LIMIT[name]}) an epoch | wins 30 % gives up to deflate | blocks an epoch")
        g1 = least_gap(K, phi, 1.0, T_M)
        costs(name, K, phi, PHASE_1, PHASE_2, PHASE_3, PERIOD, "today")
        costs(name, K, phi, PHASE_1, PHASE_2, g_max, PERIOD, "phase 3 at the largest G* of the K row, window kept")
        costs(name, K, phi, PHASE_1, PHASE_2, g1, PERIOD, "phase 3 at G* with all of the stake building, window kept")
        if K != PHASE_1 // 3:
            costs(name, K, phi, 3 * K, 3 * K, 4 * K, 6 * K, "phases of 3 K, 3 K and 4 K, window 6 K")
        costs(name, K, phi, PHASE_1 // 2, PHASE_2 // 2, PHASE_3 // 2, PERIOD // 2, "every phase and the window halved")
        costs(name, K, phi, PHASE_1 // 3, PHASE_2 // 3, PHASE_3 // 3, PERIOD // 3, "every phase and the window at a third")
        costs(name, K, phi, g_max, w_max, g_max, g_max + w_max, "every phase at G* or w_B for the K row")
        costs(name, K, phi, g1, w15, g1, g1 + w15, "every phase at G* or w_B with all of the stake building")
        print()
