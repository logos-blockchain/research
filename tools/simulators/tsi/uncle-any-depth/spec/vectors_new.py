"""Check the vectors of the drafted document: every body_root follows from the table's own inputs."""
import re, sys, hashlib
h = lambda *p: hashlib.blake2b(b"".join(p), digest_size=32).digest()
doc = open(sys.argv[1]).read(); hx = lambda s: bytes.fromhex(s[2:])
rows = [l for l in doc.splitlines() if l.startswith("| `uncles`")]
for r in rows:
    ent = [hx(x) for x in re.findall(r"`uncles\[\d\]`: (0x[0-9a-f]+)", r)]
    root = hx(re.search(r"`merkle_root\(transactions\)`: (0x[0-9a-f]{64})", r).group(1))
    want = hx(re.search(r"`body_root`: (0x[0-9a-f]{64})", r).group(1))
    assert all(len(e) == 40 for e in ent)
    print(len(ent), "entries:", h(b"BODY_ROOT_V1", bytes([len(ent)]) + b"".join(ent), root) == want)
