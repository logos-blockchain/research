# RPi5 results

Empty until the suite is run on the Raspberry Pi 5. From a clone of this repo on
the Pi:

```bash
cd tools/benchmarks/reference-prefix
./scripts/run_all.sh rpi5
```

That writes `machine.txt`, `toolchain.txt`, `candidate_generation.txt`,
`throughput.csv`, `birthday.csv` and `reconstruction.csv` into this directory.
Then, on the development machine:

```bash
python3 scripts/analyse.py --machines mac rpi5
```

and paste the regenerated tables into
[`reports/block-proposal/reference-prefix-length.md`](../../../../reports/block-proposal/reference-prefix-length.md),
replacing the cells marked `_(pending)_`.
