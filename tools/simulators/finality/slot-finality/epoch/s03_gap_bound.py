"""The chance that the value read at the cut-off is not final when it is first used, in the model of
the specification's Finality Floor section (REVIEW.md, statements 5.4 and 5.5).

For a gap G from the cut-off to the first use, a finality window K, a floor phi, a share x of the
inferred stake that builds (chance per slot p = 1 - (1 - f)^x) and a delay d of every block:
  upper bound (holds whatever uncles are referenced):
      P(not final) <= P(Bin(G - (phi + 1) d, p) <= phi) + P(Bin(G - K - 2 d + 1, p) <= 1)
  lower bound when only blocks of the chain count:
      P(not final) >= max( P(Bin(G + 1 - phi d, p) <= phi), (1 - p)^(G - K + 1) )
  lower bound in every case (every win counted, no delay):
      P(not final) >= max( P(Bin(G, p) <= phi - 1), (1 - p)^(G - K + 1) )
The script solves each for the least share x that keeps the chance at most 1e-9, and for the least
gap at a given share. The mean-rate share of the RFCs (p_x G = phi) is printed beside them.
Usage: python s03_gap_bound.py > out_03_gap_bound.txt
"""
import math

from common import CASES, DELTA, EPS, F, H, T_M, at_most_one, least_gap, least_int, least_share, lower_chain, lower_wins, mean_rate_share, p_of, pct, short, upper

GAPS = {
    "10 h (#533)": (72, 54, 45, 40, 36, 30, 24, 22, 20, 18, 16, 14, 12, 11, 10.5, 10.25),
    "18 h (base)": (72, 54, 45, 40, 36, 30, 27, 24, 22, 20, 19, 18.5, 18.25),
}
SHARES = (1.0, 0.93, 0.9, 0.7, 0.63, 0.5, 0.4, 0.3, 0.25, 0.2, 0.15, 0.1)

if __name__ == "__main__":
    for name, (K, phi) in CASES.items():
        print(f"=== {name}: K = {K}, phi = {phi}, epsilon = {EPS:g} ===")
        print("least share x of the inferred stake that must build, in %, by gap ('none': no share up to 100 %)")
        print(" gap (h) | mean rate | every win counted (necessary) | chain only, 10 s: necessary, sufficient | chain only, 15 s: necessary, sufficient")
        for hours in GAPS[name]:
            G = int(round(hours * H))
            row = [f"{hours:8.2f}", pct(mean_rate_share(G, phi)), pct(least_share(lambda p: lower_wins(G, K, phi, p)))]
            for d in (DELTA, T_M):
                row.append(pct(least_share(lambda p: lower_chain(G, K, phi, p, d))))
                row.append(pct(least_share(lambda p: upper(G, K, phi, p, d))))
            print(" | ".join(row))
        print("\nat the mean-rate share: the chance that the value is not final when first used (lower bound with every win counted, upper bound at 15 s)")
        for hours in (72, 54):
            G = int(round(hours * H))
            p = p_of(mean_rate_share(G, phi))
            print(f"   gap {hours} h, share {100 * mean_rate_share(G, phi):.2f} %: between {lower_wins(G, K, phi, p):.4f} and {upper(G, K, phi, p, T_M):.4f}")
        print("\nthe two terms of the upper bound at the sufficient share, 15 s")
        print(" gap (h) | share % | floor term | age term")
        for hours in GAPS[name]:
            G = int(round(hours * H))
            x = least_share(lambda p: upper(G, K, phi, p, T_M))
            if x is None:
                x = 1.0
            p = p_of(x)
            print(f"{hours:8.2f} | {100 * x:6.2f} | {short(phi + 1, G, p, T_M):.3e} | {at_most_one(G - K - 2 * T_M + 1, p):.3e}")
        print("\nleast gap G*(x) with the upper bound at most 1e-9, by share x and delay d")
        print(" share % | d = 0: slots, h, G* - K | d = 10 | d = 15")
        for x in SHARES:
            cells = []
            for d in (0, DELTA, T_M):
                g = least_gap(K, phi, x, d)
                cells.append(f"{g:7d} {g / H:6.2f} h {g - K:+7d}")
            print(f"{100 * x:7.1f} | " + " | ".join(cells))
        print("\nleast gap at which each lower bound falls to 1e-9: no shorter gap keeps the chance at most 1e-9")
        print(" share % | every win counted: slots, h, minus K | chain only, d = 15 | G*(x) at d = 15, for comparison")
        for x in SHARES:
            p = p_of(x)
            g_wins = least_int(lambda G: lower_wins(G, K, phi, p), K, 40_000_000)
            g_chain = least_int(lambda G: lower_chain(G, K, phi, p, T_M), K, 40_000_000)
            g_up = least_gap(K, phi, x, T_M)
            print(f"{100 * x:7.1f} | {g_wins:7d} {g_wins / H:6.2f} h {g_wins - K:+7d} | {g_chain:7d} {g_chain / H:6.2f} h {g_chain - K:+7d} | "
                  f"{g_up:7d} {g_up / H:6.2f} h {g_up - K:+7d}")
        print("\na gap of exactly K, and a little more (all of the inferred stake builds, p = f):")
        for extra in (0, 1, 30, 300, 600, 765, 900, 1800):
            G = K + extra
            lo = math.exp((G - K + 1) * math.log1p(-F))
            print(f"  G = K + {extra:4d}: P(not final) >= (1 - f)^(G - K + 1) = {lo:.3e}; "
                  f"upper bound at 15 s = {upper(G, K, phi, F, T_M):.3e}")
        need = math.log(1 / EPS) / (-math.log1p(-F))
        print(f"  (1 - f)^(x (G - K + 1)) <= 1e-9 needs G - K + 1 >= {need:.2f} / x slots")
        print()
