# Does the benchmark need sudo?

*Assessment of the privilege the [`pqc`](../../tools/benchmarks/pqc) benchmark asks for: what it buys, what is lost without it, and how to remove the need entirely.*

**Short answer: no.** The run completes, produces every measurement group, and
writes a complete results file with no privilege at all. What privilege buys is
one thing — a *constant CPU clock* — and it buys it for one step. A run without
it is a valid measurement of a machine whose clock was free to move, and it is
recorded as such rather than silently presented as a reference number.

## What privilege is actually used for

Exactly one operation in the whole run escalates: writing `performance` into
`/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor`
(`pqb_set_governor_performance` in `setup/lib_platform.sh`). Everything else —
the cargo builds, every benchmark binary, the TLS harnesses, the results file —
runs as the invoking user.

Three things that *look* like they should need root do not:

| step | privilege | why not |
|---|---|---|
| core pinning (`taskset`) | none | pinning a process you own to a CPU is unprivileged |
| SoC clock/temperature trace (`vcgencmd`) | none | needs the `video` group, which the default Pi user is already in |
| reading `/proc/cpuinfo`, `/proc/device-tree/model` | none | world-readable |

`make run` reflects that narrowness: it caches credentials once up front
(`sudo -v`, one prompt before any measurement) and the governor write then uses
non-interactive `sudo -n`, so a run can never stall on a password prompt
mid-measurement. `NOSUDO=1 make run` skips the attempt entirely. An earlier
design ran the *whole* thing under sudo and caused three distinct failures —
root-owned scratch directories, cargo unable to resolve a toolchain under root's
`HOME`, and root-owned build trees — which is why the escalation is now confined
to the single write.

`make deps` also uses sudo, but that is a package installer, opt-in and separate
from measurement: nothing about running the benchmark requires it.

## What the governor buys

A constant clock, and the evidence for that is in the published reference run.
Over 1659 samples spanning a 28-minute run, the reference platform's ARM clock
under `performance` reads:

| metric | value |
|---|---|
| min | 2 400 017 408 Hz |
| max | 2 400 037 120 Hz |
| mean | 2 400 025 928 Hz |
| **spread** | **0.0** (`arm_clock_hz.spread_frac`) |

The clock does not move at all — 20 kHz of jitter on 2.4 GHz, or 8 parts per
million. Every median, MAD and IQR in that run is therefore a property of the
algorithm, not of what the frequency scaler happened to be doing at the time.

Without the write, the governor stays at the system default — `ondemand` on
Raspberry Pi OS, `schedutil` on most other distributions — and the clock is free
to move between the SoC's minimum and maximum (1.5–2.4 GHz on the reference
platform, a 1.6× range).

## What it costs to run without it

Four distinct consequences, in descending order of importance:

1. **The run is not reference-grade, by design.** `is_baseline_grade` becomes
   `false` with the reason `CPU governor is '<x>', not 'performance'`, the
   dashboard labels it a cross-platform datapoint, and `plot.py` excludes it
   from figures by default. This is a labelling consequence, not a failure: the
   file is complete and every number in it is real.
2. **Variance, more than slowdown.** A demand-driven governor ramps to maximum
   within tens of milliseconds of sustained load, and every operation here is
   measured in bursts that saturate one core — so most of a long run executes at
   full clock either way. The damage concentrates at *transitions*: the first
   iterations after each idle gap run at a lower clock. That inflates MAD and
   IQR rather than shifting the median uniformly, and it hits **fast operations
   hardest** — an ML-KEM operation at ~30 µs can finish inside the ramp window
   entirely, while a Classic McEliece keygen at hundreds of milliseconds barely
   notices. A no-governor run therefore distorts the *comparison between
   algorithms*, which is exactly what this benchmark exists to measure.
3. **Cross-machine comparability is void.** Two machines whose governors made
   different decisions cannot be compared, and the decisions are not recorded
   beyond the governor name. This is the reason the gate exists at all.
4. **No measured slowdown figure — and this dataset cannot supply one.** Every
   run in `results/` was measured with the governor at `performance`; three of
   them started from `ondemand` and were switched before measurement. There is
   no committed A/B pair, so any specific "×N slower" number would be
   invention. The bound that *can* be stated from the hardware is the frequency
   range: worst case, operations that execute entirely at minimum clock take
   ~1.6× longer on the reference platform.

## Getting the number, if it matters

The A/B is cheap and needs no code — two full runs on one machine, back to back:

```bash
cd tools/benchmarks/pqc
make run                 # governor forced to performance
NOSUDO=1 make run        # whatever the system default is
```

Then compare the two result files. The comparison to make first is not the
medians but `thermal_trace.arm_clock_hz.spread_frac`: it is `0.0` above, and any
non-zero value in the second run is the mechanism in question, directly
observed. After that, compare per-operation MAD and IQR (the predicted effect)
before medians (the smaller one), and look specifically at whether fast and slow
algorithms diverge.

## Recommendation

**Keep the governor step, and take the privilege out of the run instead.** On a
machine that exists to run benchmarks, set the governor persistently at boot —
a `cpupower.service` unit, a `tmpfiles.d` rule writing the sysfs file, or
`cpufreq.default_governor=performance` on the kernel command line — and the
benchmark then needs no privilege whatsoever: it detects that the governor is
already `performance`, skips the write, does not prompt, and still passes the
reference-grade gate.

That path is now explicitly supported: `pqb_set_governor_performance` probes
every CPU's governor before attempting any write and returns success
immediately if they are all already `performance`. Before that fix, a correctly
pre-configured machine still got told it "could not set governor to
performance" — the run was fine and the gate passed, but the warning implied a
privilege problem that did not exist.

For anyone else — a contributor running it once on a laptop, a cross-platform
datapoint, a smoke test — sudo is not worth asking for. `NOSUDO=1 make run` is
the right call, and the resulting file is honest about what it is.
