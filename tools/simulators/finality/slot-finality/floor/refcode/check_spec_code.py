# Runs the Python as the specifications print it, against the same tests.
#   python3 check_spec_code.py <worktree root>
import ast
import re
import sys
from pathlib import Path

import reference as R
import test_reference as TR

root = Path(sys.argv[1])
raw = root / "docs" / "blockchain" / "raw"


def fences(text):
    return re.findall(r"^[ ]*```python\n(.*?)^[ ]*```", text, flags=re.S | re.M)


def fence_with(path, needle):
    hits = [f for f in fences(path.read_text()) if needle in f]
    assert len(hits) == 1, (path, needle, len(hits))
    return hits[0]


# ---- the floor, as cryptarchia-v1-protocol.md prints it
ns = {"K": 64800, "f": 1 / 30, "T_M": 15}
exec(fence_with(raw / "cryptarchia-v1-protocol.md", "def finality_floor"), ns)
got = ns["finality_floor"]()
assert got == 1291, got
print("finality_floor() as printed:", got, " blocks_short at it:", f"{ns['blocks_short'](got):.3g}", " one past it:", f"{ns['blocks_short'](got + 1):.3g}")
assert "ALPHA_MAX" not in ns and "DELTA" not in ns      # the floor reads neither any more
for t_m, K, want in ((10, 64800, 1443), (15, 36000, 689)):
    ns["T_M"], ns["K"] = t_m, K
    assert ns["finality_floor"]() == want
print("the same code at a delay of 10: 1443; at K = 36,000 and a delay of 15: 689")

# ---- the fork choices, as fork-choice.md prints them
ns = dict(common_prefix_depth=R.common_prefix_depth, grandparent=R.grandparent, density=R.density,
          is_ancestor=R.is_ancestor, block_id=R.block_id)
fc = raw / "fork-choice.md"
exec(fence_with(fc, "def bootstrap_fork_choice"), ns)
exec(fence_with(fc, "def online_fork_choice"), ns)
R.bootstrap_fork_choice = ns["bootstrap_fork_choice"]
R.online_fork_choice = ns["online_fork_choice"]
TR.ORIGINAL["bootstrap_fork_choice"] = R.bootstrap_fork_choice
TR.ORIGINAL["online_fork_choice"] = R.online_fork_choice
failed = TR.run_all(quiet=True)
assert not failed, failed
print(f"bootstrap_fork_choice and online_fork_choice as printed: {len(TR.TESTS)} of {len(TR.TESTS)} tests pass")

# ---- the last round and the download, as cryptarchia-v1-bootstr-sync.md prints them
sync = raw / "cryptarchia-v1-bootstr-sync.md"
for needle in ("def last_round", "def download_blocks"):
    ast.parse(fence_with(sync, needle))
last = fence_with(sync, "def last_round")
assert "peers=[peer]" in last and "known=known" in last
assert "last = last_delivered(peer)" in last
tree = ast.parse(last)
# The recorded block is named always, beside the last delivered block or the three blocks behind the tip.
named = next(ast.unparse(n) for n in ast.walk(tree)
             if isinstance(n, ast.Assign) and ast.unparse(n.targets[0]) == "known")
assert named == ("known = [recorded] + ([last] if last is not None else "
                 "local_tree.blocks_behind_tip([T_offline, s_gen, K]))"), named
# The tip is asked again in every repetition, and the wait follows a failed tip request too.
loop = next(n for n in ast.walk(tree) if isinstance(n, ast.While))
assert ast.unparse(loop.test) == "True"
assert ast.unparse(loop.body[0]) == "tip = get_tip(peer)" and ast.unparse(loop.body[-1]) == "sleep(T_round)"
down = fence_with(sync, "def download_blocks")
assert "peers or select_peers()" in down and "(known or [])" in down
print("last_round and download_blocks as printed: both parse; each repetition asks the peer's tip, "
      "and a download names the recorded block with the last delivered block, or with three "
      "blocks behind the local tip")

# ---- the values each document states
protocol = (raw / "cryptarchia-v1-protocol.md").read_text()
assert "64,800 slots (18 hours)" in protocol and 64800 == 2160 * 30 and 64800 / 3600 == 18
assert "1,291 occupied slots" in protocol
assert re.search(r"\$`3K \+ 3K \+ 4K = 10K`\$", protocol)
print("stated values agree: K = 64,800 slots = 18 h, phi = 1,291, epoch = 10K")
