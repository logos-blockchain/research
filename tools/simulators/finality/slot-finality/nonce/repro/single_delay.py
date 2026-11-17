# An estimate, not a result of the finality study: how long one sequential delay on today's hash-chain
# value would have to be. It reuses two of the study's own quantities (finality_sim.formation):
#   branch_survival(T)  the chance that a branch from an honest block can still be published T later;
#   open_law(T)         the chance that some choice is still open T after the cut-off (random delay).
# With a delay T_a on the fastest hardware, a candidate (a fork point and a subset of the coalition's
# wins after it) is formed when its fork point arrives, since the coalition knows its own wins ahead,
# and its nonce is seen T_a later. It counts only if its branch can still be published then.
#   - A coalition with E delay evaluators sees at most E candidates of a surviving branch. Fork points
#     older than T_a must survive longer, so the fork points within T_a dominate: about T_a / clock.
#     bias - 1 <= E * (T_a / clock) * branch_survival(T_a)   (the study's evaluator bound, with the
#     delay's span in place of the sub-window)
#   - The honest value is seen T_a after the cut-off; keeping it or switching blind counts when a
#     choice is still open then: + open_law(T_a).
# Usage: python single_delay.py
import os
import sys

OLD = None
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "src"))
from finality_sim.formation import branch_survival, open_law   # noqa: E402
from finality_sim.slots import occupancy                        # noqa: E402

F = 1 / 30
G_SPEC = 0.845

print("share | T_a (h) | fork points within T_a | branch survival (worst 10 s) | bias - 1 per evaluator | "
      "choice still open at T_a (random delay) | evaluators for bias 1.10")
for alpha in (0.30, 1 / 3):
    h = occupancy(F, 1.0 - alpha)
    clock = 1.0 / h + 10
    for hours in (1.0, 2.0, 2.25, 3.0, 4.0, 4.49, 6.0, 9.0, 12.0):
        slots = int(hours * 3600)
        s = branch_survival(F, alpha, slots, delta=10)
        n_fp = slots / clock
        per_e = n_fp * s
        op = open_law(F, alpha, slots, growth=G_SPEC)
        e10 = (0.10 - op) / per_e if per_e > 0 and op < 0.10 else float("nan")
        who = "30 %" if alpha == 0.30 else "a third"
        print(f"{who:8s} | {hours:5.2f} | {n_fp:6.0f} | {s:9.2e} | {per_e:9.2e} | {op:9.2e} | {e10:9.2e}")
