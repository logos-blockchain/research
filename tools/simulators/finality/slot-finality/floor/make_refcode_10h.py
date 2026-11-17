# Builds refcode-10h/: the reference code and its tests at the stacked branch's constants (K = 36,000
# slots, phi = 689, the epoch in floor(k/f) = 64,800), and a check of the branch's printed code and
# stated values. The floor is derived with all of the stake building and every block T_M = 15 late.
# Run: python3 -B make_refcode_10h.py
import shutil
import sys
from pathlib import Path

SCRATCH = Path(__file__).resolve().parent
SRC, OUT = SCRATCH / "refcode", SCRATCH / "refcode-10h"
OUT.mkdir(exist_ok=True)
for name in ("reference.py", "test_reference.py"):
    shutil.copy(SRC / name, OUT / name)


def patch(path, pairs):
    text = path.read_text()
    for old, new in pairs:
        assert text.count(old) >= 1, (path.name, old)
        text = text.replace(old, new)
    path.write_text(text)


patch(OUT / "reference.py", [
    ("KK = int(k / f + 0.5)  # K = floor(k / f); f is 1/30 exactly, so k/f is an integer\n"
     "S_GEN = KK // 4        # s_gen = floor(k / 4f)\n",
     "U = int(k / f + 0.5)   # floor(k / f), the unit of the epoch schedule; f is 1/30 exactly\n"
     "KK = 36000             # K, the finality window: 10 hours\n"
     "S_GEN = U // 4         # s_gen = floor(k / 4f)\n"),
])

sys.path.insert(0, str(OUT))
import reference as R  # noqa: E402

phi = R.finality_floor(36000, 1 / 30, 15, 1e-9)
phi10 = R.finality_floor(36000, 1 / 30, 10, 1e-9)
at = R.blocks_short(phi, 36000, 1 / 30, 15)
past = R.blocks_short(phi + 1, 36000, 1 / 30, 15)
assert (phi, phi10) == (689, 768), (phi, phi10)

patch(OUT / "test_reference.py", [
    ("    assert R.KK == 64800\n"
     "    assert 3 * R.KK == 194400 and 6 * R.KK == 388800 and 10 * R.KK == 648000\n",
     "    assert R.KK == 36000\n"
     "    assert 3 * R.U == 194400 and 6 * R.U == 388800 and 10 * R.U == 648000\n"
     "    assert 3 * R.U >= R.KK               # each phase that waits for a value to finalize\n"),
    ("    assert R.finality_floor(36000, 1 / 30, 15, 1e-9) == 689    # the window of #533\n",
     "    assert R.finality_floor(36000, 1 / 30, 15, 1e-9) == 689    # the window of #533\n"
     f"    assert R.finality_floor(36000, 1 / 30, 10, 1e-9) == {phi10}   # so 689 holds at 10 s too\n"
     f"    assert R.finality_floor(R.KK, R.f, R.T_M, R.EPSILON) == {phi}\n"),
    ("    assert past > 1e-9, past\n",
     "    assert past > 1e-9, past\n"
     f"    at = R.blocks_short({phi}, 36000, 1 / 30, 15)\n"
     f"    past = R.blocks_short({phi + 1}, 36000, 1 / 30, 15)\n"
     "    assert at <= 1e-9 < past, (at, past)\n"),
    ("K, sg, phi = 64800, 16200, 1291", f"K, sg, phi = 36000, 16200, {phi}"),
    ("K, sg = 64800, 16200", "K, sg = 36000, 16200"),
])

check = (SRC / "check_spec_code.py").read_text()
for old, new in [
    ('ns = {"K": 64800, "f": 1 / 30, "T_M": 15}', 'ns = {"K": 36000, "f": 1 / 30, "T_M": 15}'),
    ("assert got == 1291, got", f"assert got == {phi}, got"),
    ("for t_m, K, want in ((10, 64800, 1443), (15, 36000, 689)):", f"for t_m, K, want in ((10, 36000, {phi10}), (15, 64800, 1291)):"),
    ('print("the same code at a delay of 10: 1443; at K = 36,000 and a delay of 15: 689")',
     f'print("the same code at a delay of 10: {phi10}; at K = 64,800 and a delay of 15: 1291")'),
    ('assert "64,800 slots (18 hours)" in protocol and 64800 == 2160 * 30 and 64800 / 3600 == 18',
     'assert "36,000 slots (10 hours)" in protocol and 36000 / 3600 == 10'),
    ('assert "1,291 occupied slots" in protocol', f'assert "{phi} occupied slots" in protocol'),
    (r'assert re.search(r"\$`3K \+ 3K \+ 4K = 10K`\$", protocol)',
     r'assert "3\\lfloor \\frac{k}{f}\\rfloor + 3\\lfloor \\frac{k}{f}\\rfloor + 4\\lfloor \\frac{k}{f}\\rfloor = 10\\lfloor \\frac{k}{f}\\rfloor" in protocol'
     '\nassert "\\\\alpha_\\\\text{max} = 3/10" in protocol and "returns $`' + str(phi) + '`$" in protocol'
     '\ntsi = (raw / "cryptarchia-total-stake-inference.md").read_text()'
     "\n" + r'assert r"| `PERIOD` | $`6\lfloor \frac{k}{f} \rfloor`$ |" in tsi'),
    ('print("stated values agree: K = 64,800 slots = 18 h, phi = 1,291, epoch = 10K")',
     f'print("stated values agree: K = 36,000 slots = 10 h, phi = {phi}, alpha_max = 3/10 in the K row, '
     'epoch = 10 floor(k/f), PERIOD = 6 floor(k/f)")'),
]:
    assert old in check, old
    check = check.replace(old, new)
(OUT / "check_spec_code.py").write_text(check)
print(f"refcode-10h written: phi = {phi} (at a delay of 10: {phi10}); "
      f"blocks_short at phi {at:.3g}, one past {past:.3g}")
