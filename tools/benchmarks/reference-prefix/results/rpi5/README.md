# RPi5 results

Collected 2026-08-15 on a Raspberry Pi 5 Model B Rev 1.1 (Cortex-A76, 4 cores),
Debian kernel 6.18.34+rpt-rpi-2712, rustc 1.97.1 (the pinned toolchain), with
the CPU governor set to `performance` and no thermal throttling before or after
the run (`get_throttled=0x0`, ~56 °C). Produced by:

```bash
cd tools/benchmarks/reference-prefix
./scripts/run_all.sh rpi5
```

with no modification to sources, scripts, profile, or toolchain. The
`birthday.csv` determinism cross-check against `../mac/birthday.csv` passes:
all columns identical except the rate column.

To regenerate the report tables and the latency figure from these files:

```bash
python3 scripts/analyse.py --machines mac rpi5
```

The corresponding cells in
[`reports/block-proposal/reference-prefix-length.md`](../../../../reports/block-proposal/reference-prefix-length.md)
are filled from this run.
