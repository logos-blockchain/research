"""CHECK.md, item 4: one line per (K, G) from out_c4_sim.txt.
Usage: python c4_table.py out_c4_sim.txt > out_c4_table.txt
"""
import re
import sys

KEYS = {
    "S": "H choices with S:",
    "out": "passes ending outside G:",
    "missB": "B's events MISS",
    "missA": "A's events MISS",
    "missBs": "B's events, sharp form, MISS",
    "missAs": "A's events, sharp form, MISS",
    "cross": "Step 2: crossing (D after D_Y, X bad):",
    "genw": "crossing: GENESIS's witness X not under H's states:",
    "Eronly": "B covered only by E_r*, sharp form:",
    "v31": "3.1 VIOLATIONS:",
    "v53": "B 5.3 VIOLATIONS",
    "v71": "B 7.1 VIOLATIONS",
    "vEr": "crossing: (Y, H) not an E_r' witness VIOLATION:",
    "vstep": "VIOLATION:",
    "g61": "X's window not under H's states (6.1 needs",
    "gap72": "7.2 second bound, E_d with D after D_Y: an added slot not under H's states:",
    "gap72s": "7.2 second bound, E_d*: an added slot not under H's states:",
    "c1": "6.3 case 1, ",
}

rows, cur = [], None
for ln in open(sys.argv[1]).read().split("\n"):
    m = re.match(r"K = (\d+), G = (\d+)", ln)
    if m or ln.startswith("TOTAL"):
        if cur:
            rows.append(cur)
        cur = {"K": int(m.group(1)), "G": int(m.group(2))} if m else None
        if not m:
            break
        continue
    if cur is None or ":" not in ln or "example" in ln:
        continue
    val = ln.rsplit(":", 1)[1].strip()
    if not val.isdigit():
        continue
    for k, pat in KEYS.items():
        if pat in ln:
            if k == "vstep" and ("Step" not in ln):
                continue
            cur[k] = cur.get(k, 0) + int(val)
cols = ["S", "out", "missB", "missA", "missBs", "missAs", "cross", "genw", "Eronly", "v31", "v53", "v71",
        "vEr", "vstep", "g61", "gap72", "gap72s", "c1"]
print("K G " + " ".join(cols))
for r in rows:
    print(f"{r['K']} {r['G']} " + " ".join(str(r.get(c, 0)) for c in cols))
print("\nS: H choices with S; out: passes ending outside G; missB/missA: passes outside G that B's/A's events "
      "miss (literal); missBs/missAs: the same in the sharp form; cross: crossing exits (GENESIS 7.1 Step 2); "
      "genw: of which GENESIS's witness X is not under H's states; Eronly: passes outside G that only E_r* covers "
      "(sharp form); v31, v53, v71, vEr: failures of 3.1, of B 5.3, of B 7.1, of (Y, H) as an E_r' witness; vstep: "
      "exits that no step of the proof explains; g61: E_d witnesses with D at/after D_Y whose X window is not under "
      "H's states; gap72: E_d witnesses with D after D_Y whose 7.2 extension derives a non-H state; gap72s: the same "
      "for E_d* witnesses; c1: failures of the 6.3 first-case extension.")
