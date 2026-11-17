# Runs the Finality Floor code exactly as cryptarchia-v1-protocol.md prints it.
#   python3 run_printed_floor.py <worktree root> <K> <expected floor>
import re
import sys
from pathlib import Path

root, K, want = Path(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
text = (root / "docs" / "blockchain" / "raw" / "cryptarchia-v1-protocol.md").read_text(encoding="utf-8")
fences = [f for f in re.findall(r"^[ ]*```python\n(.*?)^[ ]*```", text, flags=re.S | re.M) if "def finality_floor" in f]
assert len(fences) == 1, len(fences)
code = fences[0]
assert "ALPHA_MAX" not in code and "DELTA" not in code and "p_h" not in code
ns = {"K": K, "f": 1 / 30, "T_M": 15}
exec(code, ns)
got = ns["finality_floor"]()
print(f"K = {K}: finality_floor() as printed returns {got}; blocks_short({got}) = {ns['blocks_short'](got):.4g}, "
      f"blocks_short({got + 1}) = {ns['blocks_short'](got + 1):.4g}, EPSILON = {ns['EPSILON']}")
assert got == want, (got, want)
assert f"{want:,} occupied slots" in text, "the phi row does not state the value"
assert f"returns $`{want}`$" in text, "the closing sentence does not state the value"
assert f"$`K = {K}`$" in text, "the closing sentence does not state K"
print("the phi row and the closing sentence state the same value")
