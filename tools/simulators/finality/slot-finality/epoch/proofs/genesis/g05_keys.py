"""GENESIS.md, section 9: keys of stake acquired after the window (posterior corruption).

A coalition of share a later holds the keys of further notes of the window's distribution, of share
b, unspent at the divergence block. Within G + 1 slots of the divergence block the fork derives H's
epoch states (statement 4.2), and a ticket reads only the nonce, the slot, the note and its key
(leadership 180). So an acquired note wins on the fork exactly the slots it won on H, where it was
honest. Per slot, the coalition's own win (chance p(a)), the acquired stake's win (p(b)) and the win
of the stake that stays honest (p(1 - a - b)) are independent; the fork counts the first or the
second, the honest chain the second or the third (common_g.keys_step). The maxima keep the share a,
because they count blocks made at their time. The bound of statement 6.2 is computed by the forward
pass of Window.p1_curve with that joint law in the window's slots.
For comparison, the same bound when the acquired wins are drawn independently of the honest ones:
the fork wins with chance p(a + b), independent of the honest marks at p(1 - a).
Prints, at s = s_gen: the share b at which the fork's mean rate p(a + b) reaches the honest
Delta-separated rate 1 / (Delta + 1/p_h) and the bound there, the least b at which the bound exceeds
1e-9, and the bound at some values of b.
Usage: python g05_keys.py > out_05_keys.txt
"""
import math

from common_g import ALPHAS, DELTAS, EPS, F, S_GEN, Window, joint_step, keys_step, p_of, pct


def bound(w: Window, a: float, b: float, identical: bool) -> float:
    step = keys_step(a, b) if identical else joint_step(p_of(a + b), w.ph)
    return float(w.p1_curve(S_GEN, step=step)[S_GEN])


def threshold(w: Window, a: float, b_hi: float, identical: bool) -> float | None:
    if bound(w, a, 0.0, identical) > EPS:
        return None
    lo, hi = 0.0, b_hi
    for _ in range(24):
        mid = (lo + hi) / 2
        if bound(w, a, mid, identical) <= EPS:
            lo = mid
        else:
            hi = mid
    return hi


if __name__ == "__main__":
    print(f"s = s_gen = {S_GEN} slots")
    for a in ALPHAS:
        for d in DELTAS:
            pa, ph = p_of(a), p_of(1 - a)
            w = Window(pa, ph, d)
            rate = 1 / (d + 1 / ph)
            share_c = math.log1p(-rate) / math.log1p(-F)       # p(share_c) = rate
            b_c = share_c - a
            print(f"\n{pct(a)}, Delta = {d}")
            print(f"  fork's mean rate p(a + b) equals the honest rate {rate:.6f} at b = {b_c:.4f} (a + b = {share_c:.4f})")
            for identical, label in ((True, "identical tickets"), (False, "independent wins")):
                t = threshold(w, a, b_c, identical)
                head = (f"the bound exceeds 1e-9 already at b = 0" if t is None
                        else f"the bound reaches 1e-9 at b = {t:.4f} (a + b = {a + t:.4f})")
                vals = "; ".join(f"{b:g}: {bound(w, a, b, identical):.3e}" for b in (0.0, 0.02, 0.05, 0.1, 0.2))
                print(f"  {label}: {head}; bound at b = {vals}; at b = {b_c:.4f}: {bound(w, a, b_c, identical):.3f}")
