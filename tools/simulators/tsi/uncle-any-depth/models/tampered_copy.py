# Two readings of broadcast(Y) in Uncle Selection: "the node received the proposal of Y on the broadcasting channel",
# and "the node reconstructed Y from a proposal that it received there" (the drafted one, "accepted from the channel").
# The attacker owns Y (win 1) and Z (win 2, parent Y); both lose the fork race.
#  1. It sends a copy of Y's proposal with a genuine header and signature but tampered references to
#     node T0 only. T0 decodes it, passes Header Validation, fails body_root, keeps no verdict and does
#     not forward the copy. T0 has now received "the proposal of Y".
#  2. It broadcasts Z normally. Every node holds Z as an orphan and downloads Y in full.
# Selection (uncle_candidates): every Y' in branch(X, B) must satisfy broadcast(Y') or be referenced.
NODES = [f"N{i}" for i in range(10)]
T0 = "N3"
def flags(wording):
    out = {}
    for n in NODES:
        received_proposal_of_Y = (n == T0)            # only T0 got the tampered copy
        accepted_Y_from_channel = False               # nobody reconstructed Y from the channel
        out[n] = {"Y": received_proposal_of_Y if wording == "received the proposal" else accepted_Y_from_channel,
                  "Z": True}                          # Z came on the channel to everyone
    return out
for wording in ("received the proposal", "accepted from the channel"):
    fl = flags(wording)
    can_Y = [n for n in NODES if fl[n]["Y"]]                     # branch(Y) = {Y}
    can_Z = [n for n in NODES if fl[n]["Y"] and fl[n]["Z"]]      # branch(Z) = {Y, Z}
    print(f"{wording:26s}: nodes that may name Y: {can_Y or 'none'}, Z: {can_Z or 'none'}")
