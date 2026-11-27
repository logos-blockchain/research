"""Sizes that follow from the uncle entry, before (361 bytes) and after (40 bytes)."""
MAX_UNCLES, MAX_TXS = 4, 1024
HEADER, SIG = 297, 64
def sizes(entry):
    uncles = 1 + MAX_UNCLES * entry
    refs = 2 + 16 * MAX_TXS
    proposal = HEADER + uncles + refs + SIG
    payload = proposal + 3
    overhead = 256 + 3 * 289
    msg = payload + overhead
    return dict(uncles_max=uncles, proposal_min=HEADER + 1 + 2 + SIG, proposal_max=proposal, payload=payload,
                overhead=overhead, overhead_pct=100 * overhead / payload, message=msg,
                read_MBps=124 * msg / 1e6, edge_s=msg * 8 / 1e6, edge_total=msg * 8 / 1e6 * 1.2 + 0.5)
a, b = sizes(361), sizes(40)
for k in a: print(f"{k:14s} {a[k]:>12.4f} -> {b[k]:>12.4f}")
print("saved per proposal/message:", a["proposal_max"] - b["proposal_max"], f"({100*(1-b['message']/a['message']):.2f}% of a Blend message)")
