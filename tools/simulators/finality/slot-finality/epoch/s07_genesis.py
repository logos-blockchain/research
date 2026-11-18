"""The hypotheses of Theorems 1 and 2 of Ouroboros Genesis at the specification's parameters
(REVIEW.md, section 8).

Cited from "Ouroboros Genesis: Composable Proof-of-Stake Blockchains with Dynamic Availability",
full version of February 22, 2019 (ePrint 2018/378):
  Theorem 1:  alpha (1 - f)^(Delta + 1) >= (1 + eps) / 2 for some eps in (0, 1),  R >= 144 Delta / (eps beta f);
  Theorem 2:  k > 192 Delta / (eps beta),  R / 6 >= s = k / (4 f) >= 48 Delta / (eps beta f).
alpha is the alert ratio and beta the participating ratio. With a coalition of share a of the total
active stake and all of the honest stake online, alpha = 1 - a and beta = 1. The largest eps that
the first condition allows is eps_max = 2 (1 - a) (1 - f)^(Delta + 1) - 1, and the other conditions are
easiest at eps_max.
Usage: python s07_genesis.py > out_07_genesis.txt
"""
from common import CASES, EPOCH, F, GAP, H, K_SEC, S_GEN, U

if __name__ == "__main__":
    print(f"specification: k = {K_SEC}, f = 1/30, R = {EPOCH} slots, s = s_gen = {S_GEN} slots, beta = 1")
    for a, name in ((0.30, "30 %"), (1 / 3, "a third")):
        print(f"\ncoalition of {name} of the total active stake, alpha = {1 - a:.4f}")
        print(" Delta | eps_max | k must exceed 192 Delta/eps_max | s must be at least 48 Delta/(eps_max f) | R must be at least 144 Delta/(eps_max f) | all hold")
        last_ok = None
        for delta in range(0, 17):
            eps = 2 * (1 - a) * (1 - F) ** (delta + 1) - 1
            if eps <= 0:
                print(f" {delta:5d} | {eps:+.4f} | the first condition has no eps | - | - | no")
                continue
            eps = min(eps, 1.0)
            k_min = 192 * delta / eps
            s_min = 48 * delta / (eps * F)
            r_min = 144 * delta / (eps * F)
            ok = K_SEC > k_min and S_GEN >= s_min and EPOCH >= r_min and EPOCH / 6 >= S_GEN
            if ok:
                last_ok = delta
            print(f" {delta:5d} | {eps:.4f} | {k_min:9.1f} | {s_min:9.1f} | {r_min:9.1f} | {'yes' if ok else 'no'}")
        print(f" the hypotheses hold up to Delta = {last_ok} slots")

    # Statement 8.4 (b) of REVIEW.md, by enumeration at small sizes. An epoch of E slots with a gap of
    # G slots: the state of the epoch that holds slot t reads the blocks with slot below
    # floor(t / E) E - G. Two chains share the blocks with slot <= a only. They read the same blocks
    # for slot t exactly when floor(t / E) E - G - 1 <= a.
    checked = 0
    for E in range(3, 31):
        for G in range(1, E):
            def same_for_all(two_s):
                return all((t // E) * E - G - 1 <= a for a in range(5 * E, 6 * E) for t in range(a + 1, a + two_s + 1))
            largest = max(two_s for two_s in range(0, 2 * E + 2) if same_for_all(two_s))
            assert largest == G + 1
            assert all(same_for_all(two_s) for two_s in range(0, G + 2))
            checked += 1
    print(f"\nenumeration, {checked} pairs (E, G) with G < E <= 30: both chains read the same blocks for every slot of the two windows,")
    print("  for every divergence slot, exactly when 2 s <= G + 1")

    print("\nwhat the proof of Theorem 2 reads of the schedule, in the specification's symbols")
    print(f"  two windows: 2 s_gen = {2 * S_GEN} slots = {2 * S_GEN / H:g} h")
    print(f"  the paper's R/6 >= s is 2 s <= R/3; R/3 is the span from the end of the nonce's inputs to the next epoch")
    print(f"  the specification's span from the cut-off to the next epoch: {GAP} slots = {GAP / H:g} h = {GAP / S_GEN:g} s_gen")
    for name, (K, _) in CASES.items():
        print(f"  {name}: K = {K}; 2 s_gen <= K: {2 * S_GEN <= K}; K - 2 s_gen = {K - 2 * S_GEN} slots = {(K - 2 * S_GEN) / H:g} h")
    print(f"  the theorem's R >= 6 s read on the whole epoch: {6 * S_GEN} slots = {6 * S_GEN / H:g} h; the specification's epoch: {EPOCH / H:g} h")
    print(f"  floor(k/f) = {U} = {U // S_GEN} s_gen")
