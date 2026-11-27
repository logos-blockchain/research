"""Reproduce the block vectors of Cryptarchia 1.2.5 and compute the ones the ID+slot entries change.

Usage: python3 vectors.py <cryptarchia-v1-protocol.md as master 3b3298f5 has it>
"""
import re, sys, hashlib
h = lambda *parts: hashlib.blake2b(b"".join(parts), digest_size=32).digest()
doc = open(sys.argv[1]).read()
hexs = lambda s: bytes.fromhex(s[2:])
leaf_row = [l for l in doc.splitlines() if l.startswith("| one transaction per operation kind")][0]
root = hexs(re.search(r"`merkle_root\(transactions\)`: (0x[0-9a-f]{64})", leaf_row).group(1))
body_root = lambda ser, r: h(b"BODY_ROOT_V1", ser, r)
rows = [l for l in doc.splitlines() if "`uncle_headers`" in l and "`body_root`" in l]
empty_row = [l for l in rows if "empty list" in l][0]
two_row = [l for l in rows if "2 entries" in l][0]
want = lambda row: hexs(re.search(r"`body_root`: (0x[0-9a-f]{64})", row).group(1))
entries = [hexs(x) for x in re.findall(r"`uncle_headers\[\d\]`: (0x[0-9a-f]+)", two_row)]
assert all(len(e) == 361 for e in entries)
print("body_root(empty) ok:", body_root(b"\x00", root) == want(empty_row))
print("body_root(2 x 361) ok:", body_root(b"\x02" + b"".join(entries), root) == want(two_row))
def block_id(header: bytes):
    assert len(header) == 297
    v, par, slot, br = header[:1], header[1:33], header[33:41], header[41:73]
    proof, entropy, key, voucher = header[73:201], header[201:233], header[233:265], header[265:297]
    return h(b"BLOCK_ID_V1", v, par, slot, br, voucher, entropy, proof, key)
hdr_row = [l for l in doc.splitlines() if l.startswith("| `Header`:")][0]
g = lambda name: hexs(re.search(r"`%s`: (0x[0-9a-f]+)" % name, hdr_row).group(1))
header = b"\x01" + g("parent_block") + (42).to_bytes(8, "little") + g("body_root") + g("proof") + g("entropy_contribution") + g("leader_key") + g("leader_voucher")
print("block_id ok:", block_id(header) == hexs(re.search(r"`block_id`: (0x[0-9a-f]{64})", hdr_row).group(1)))
new = [block_id(e[:297]) + e[33:41] for e in entries]
for e in new: print("entry 0x" + e.hex())
print("body_root(2 x 40) = 0x" + body_root(bytes([len(new)]) + b"".join(new), root).hex())
