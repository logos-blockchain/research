"""The epochs that suffice of review 10.3, with the buffer of this folder (SURVIVAL.md, section 11).

E_suf = max(P, G* + w_B) + max(G*, 2 K - 1), and G* + w_B + max(G*, 2 K - 1) with the window shortened
to phases 1 and 2 (review 10.2: phase 3 also needs the 2 K - 1 slots of the argument of GENESIS 7.1).
G* is the largest value of review 5.9 over the states a case requires, recomputed here with the review's own
code (`common.least_gap`, read only) and set against the review's out_14_bracket.txt (part 3, read
only). w_B is the largest buffer over the same states: from the study's law (the review's
out_08_buffer.txt, part 1, as recorded in sv_common.STATES) and from this folder's proved law
(out_3_buffer.txt, part 1, and part 3 for the circuit's lottery).
Usage: python s4_epoch.py > out_4_epoch.txt   (after s3_buffer.py)
"""
import os
import re
import sys

from sv_common import H, HERE, REVIEW_DIR, STATE, STATES

sys.path.insert(0, REVIEW_DIR)
from common import CASES, GAP, PERIOD, least_gap   # noqa: E402  (the review's constants and 5.4)

ROWS = {   # case, reading: the states it requires (review 5.9 and 10.3)
    ("10 h (#533)", "a"): ("none", "late", "off", "defl"),
    ("10 h (#533)", "b"): ("none", "late", "off_b", "defl"),
    ("18 h (base)", "a"): ("none", "late", "off", "defl", "late_off", "late_defl", "off_defl"),
    ("18 h (base)", "b"): ("none", "late", "off_b", "defl", "late_off_b", "late_defl", "off_defl"),
}
READING = {"a": "a tenth offline read after the inference corrects", "b": "a tenth offline read before it corrects"}
REVIEW_READING = {"a": "the inference corrected", "b": "before the inference corrects"}


def read_buffers():
    """w_B per state from out_3_buffer.txt: part 1 (the model's lottery) and part 3 (the circuit's)."""
    main, circuit, part = {}, {}, 0
    labels = {s[1]: s[0] for s in STATES}
    for line in open(os.path.join(HERE, "out_3_buffer.txt")):
        if re.match(r"^\d\.", line):
            part = int(line[0])
        body = line.strip()
        for label, key in labels.items():
            if body.startswith(label + ":"):
                if part == 1:
                    main[key] = int(re.search(r"w_B\(Qhat\) =\s+(\d+) slots", body).group(1))
                elif part == 3:
                    circuit[key] = int(re.search(r":\s+(\d+) slots", body).group(1))
    return main, circuit


def review_gstar():
    """The largest G* per case and its line, from part 3 of the review's out_14_bracket.txt."""
    out, part = {}, 0
    for n, line in enumerate(open(os.path.join(REVIEW_DIR, "out_14_bracket.txt")), start=1):
        if re.match(r"^\d\.", line):
            part = int(line[0])
        m = re.match(r"\s+(10 h \(#533\)|18 h \(base\)), a tenth offline read (.+?) \| gap .* G\* (\d+)", line)
        if part == 3 and m:
            reading = next(r for r, text in REVIEW_READING.items() if text == m.group(2))
            out[(m.group(1), reading)] = (int(m.group(3)), n)
    return out


def hours(slots):
    return f"{slots:6d} slots ({slots / H:6.2f} h)"


def phase_3(g, K):
    """Phase 3 that suffices (review 10.2): G* for its value, and at least 2 K - 1 for GENESIS 7.1."""
    return max(g, 2 * K - 1)


if __name__ == "__main__":
    new, circ = read_buffers()
    rev = review_gstar()
    print("1. per case: G* recomputed with the review's code and the review's value; the largest w_B: the study's law, this folder's, the circuit's")
    out = {}
    for (case, reading), keys in ROWS.items():
        K, phi = CASES[case]
        g = max(least_gap(K, phi, STATE[k][2], STATE[k][4]) for k in keys)
        g_rev, line = rev[(case, reading)]
        w_old = max(STATE[k][5] for k in keys)
        w_new = max(new[k] for k in keys)
        w_circ = max(circ[k] for k in keys)
        arg = max(keys, key=lambda k: new[k])
        out[(case, reading)] = (g, w_old, w_new, w_circ)
        print(f"   {case}, {READING[reading]}: G* = {g} (the review: {g_rev}, out_14 line {line}) | "
              f"w_B: study's law {w_old}, here {w_new} (state: {STATE[arg][1]}), circuit {w_circ}")

    print(f"\n2. the epochs that suffice, E_suf = max(P, G* + w_B) + max(G*, 2 K - 1) with P = {PERIOD}, and G* + w_B + max(G*, 2 K - 1) "
          "with the window shortened")
    print("   case | window shortened: with the study's law, with this folder's w_B, circuit | window kept: the same")
    for key, (g, w_old, w_new, w_circ) in out.items():
        g3 = phase_3(g, CASES[key[0]][0])
        short = [g + w + g3 for w in (w_old, w_new, w_circ)]
        kept = [max(PERIOD, g + w) + g3 for w in (w_old, w_new, w_circ)]
        print(f"   {key[0]}, {READING[key[1]]}:")
        print(f"      shortened: study's law {hours(short[0])} | here {hours(short[1])} ({short[1] - short[0]:+d}) | "
              f"circuit {hours(short[2])} ({short[2] - short[0]:+d})")
        print(f"      kept:      study's law {hours(kept[0])} | here {hours(kept[1])} ({kept[1] - kept[0]:+d}) | "
              f"circuit {hours(kept[2])} ({kept[2] - kept[0]:+d})")

    print("\n3. other figures of the review that read w_B, latest #533: with the study's law -> with this folder's w_B")
    K, phi = CASES["10 h (#533)"]
    g1 = least_gap(K, phi, 1.0, 15)
    g13 = phase_3(g1, K)
    w15_old, w15_new = STATE["late"][5], new["late"]
    print(f"   all of the inferred stake builds, 15 s (review 10.3, second row): G* = {g1}, phase 3 {g13}; epoch with the window shortened "
          f"{hours(g1 + w15_old + g13)} -> {hours(g1 + w15_new + g13)}; window kept {hours(max(PERIOD, g1 + w15_old) + g13)} -> "
          f"{hours(max(PERIOD, g1 + w15_new) + g13)}")
    print(f"   a late snapshot, all of the inferred stake building at 15 s (review 11.3): G* + w_B + gap = "
          f"{hours(g1 + w15_old + GAP)} -> {hours(g1 + w15_new + GAP)}")
    for reading in ("a", "b"):
        g, w_old, w_new, _ = out[("10 h (#533)", reading)]
        print(f"   a late snapshot, every state of the K row, {READING[reading]}: {hours(g + w_old + GAP)} -> {hours(g + w_new + GAP)}")
