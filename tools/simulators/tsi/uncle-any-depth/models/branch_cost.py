# Blocks a node validates (full execution) for one entry of a block A at the tip whose uncle X
# sits on an attacker branch forked at G. download_missing_uncles streams from G (the LCA with
# A's parent) to X and runs on_block on each; nothing stops it when G or a slot is out of range.
# Step 8 admits the branch when sl_G + W/f > sl_imm, and B_imm trails the tip by about k/f slots.
k, f_inv, W = 2160, 30, 240
for alpha in (0.1, 0.3, 0.45):
    rate = alpha / f_inv                       # attacker wins per slot (small-alpha approximation)
    span_now = k * f_inv + W * f_inv           # slots from the earliest admitted fork point to sl_A
    span_ok = W * f_inv                        # slots a valid branch can span
    print(f"alpha={alpha:.2f}: as written up to {rate*span_now:6.0f} blocks per entry,"
          f" {4*rate*span_now:6.0f} per block of 4 entries; stopped at the window {rate*span_ok:4.0f} / {4*rate*span_ok:4.0f}")
