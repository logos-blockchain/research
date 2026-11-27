# Models listen_and_process_new_blocks + download_missing_uncles as written in
# cryptarchia-v1-bootstr-sync.md before the download limits (logos-lips 115d2f93): after every received block the node
# walks missing_uncles() and calls download_blocks() for each entry. The fake IDs are
# served by nobody, so every call fails and nothing records the failure.
N_CONN, N_DISC, MAX_UNCLES = 16, 16, 4

def as_written(M):
    pending = []                 # (holding block, fake id) of every preferred, non-adoptable chain
    calls = 0
    for j in range(M):           # equivocation A_j of one lottery win arrives, extends c_loc
        pending += [(j, e) for e in range(MAX_UNCLES)]
        calls += len(pending)    # download_missing_uncles() walks all of them again
    return calls, calls * (N_CONN + N_DISC)

def capped(M, per_win=1):
    # one holding block per (slot, entropy_contribution) at a time, and an ID that no peer
    # served is not requested again while the same chain stays preferred
    calls = per_win * MAX_UNCLES
    return calls, calls * (N_CONN + N_DISC)

for M in (1, 10, 50, 200):
    print(f"M={M:4d} equivocations: as written {as_written(M)[0]:7d} downloads, {as_written(M)[1]:9d} peer requests per node;"
          f" capped {capped(M)[0]} downloads, {capped(M)[1]} requests")
