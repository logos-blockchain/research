#!/usr/bin/env bash
# Resilient corrected-mechanism rerun: each step runs independently; a failure is logged and
# the batch continues. Summary at the end. Light studies first, heavy fullscale last.
cd "$(dirname "$0")/.." || exit 1
source .venv/bin/activate 2>/dev/null
LOG=runs/rerun_status.log
: > "$LOG"
step() {
  local name="$1"; shift
  echo "=== [$(date +%H:%M:%S)] START $name ===" | tee -a "$LOG"
  if "$@" >>"$LOG" 2>&1; then
    echo "=== OK    $name ===" | tee -a "$LOG"
  else
    echo "=== FAIL  $name (exit $?) ===" | tee -a "$LOG"
  fi
}
# light config sweeps
step nscaling-a       make nscaling-a       SWEEP_ARGS="--n-jobs 6"
step nscaling-b       make nscaling-b       SWEEP_ARGS="--n-jobs 6"
step nscaling32-a     make nscaling32-a     SWEEP_ARGS="--n-jobs 2"
step nscaling32-b     make nscaling32-b     SWEEP_ARGS="--n-jobs 2"
step uncle-window     make uncle-window     SWEEP_ARGS="--n-jobs 6"
step window-uncles    make window-uncles    SWEEP_ARGS="--n-jobs 6"
step block-rate       make block-rate       SWEEP_ARGS="--n-jobs 6"
step blend-hops-delay make blend-hops-delay SWEEP_ARGS="--n-jobs 6"
step window-scale     make window-scale     SWEEP_ARGS="--n-jobs 6"
step expdist          make expdist          SWEEP_ARGS="--n-jobs 8"
step pareto133        make pareto133        SWEEP_ARGS="--n-jobs 8"
step default          make default          SWEEP_ARGS="--n-jobs 6"
# scripts
step stake_vs_delay   python scripts/stake_vs_delay.py
step bootstrap        python scripts/bootstrap_dynamics.py
step fluctuation      python scripts/appendix_fluct.py --run
step jitter_grid      python scripts/jitter_grid.py
step adversary_grid   python scripts/adversary_grid.py
step dynamic_withhold python scripts/dynamic_withhold.py
step selfish_mining   python scripts/selfish_mining.py
step selfish_rewards  python scripts/selfish_rewards.py
step reward_mandate   python scripts/reward_mandate.py
# heavy last so nothing waits on it
step fullscale        make fullscale        SWEEP_ARGS="--n-jobs 3 --mem-frac 0.55"
echo "=== [$(date +%H:%M:%S)] BATCH DONE ===" | tee -a "$LOG"
grep -E "OK|FAIL" "$LOG" | tee -a "$LOG"
