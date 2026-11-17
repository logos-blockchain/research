# Seeding scenarios on Logos Storage: verification, initial seed, secondary seed

Measurements for four questions from the LEZ side. 2026-11-17.

## Setup

- `logos-storage-nim` v0.5.3, default settings (64 KiB blocks).
- Three nodes on one Apple M3 (8 cores, 16 GB), loopback, private network:
  **A** holds the transactions at the start, **B** is the node under test, **F** is the feeder / verifier.
- Random payloads, every download checked against SHA-256 of the original. All runs passed.
- Script: `seedbench.py`. Raw data: `results-seed/`.
- To re-run: put the `logos-storage-darwin-arm64-v0.5.3` release binary under `bin/`, then `python3 seedbench.py s1 out.csv 5` and `python3 seedbench.py s23 out.csv 3 16`. `TX_BYTES="307200"` selects other transaction sizes.

These are protocol floors. There is no WAN, no NAT and no live DHT in the path.

## 1. How quick is it to verify that somebody seeds a file with CID X?

F has never seen X; B seeds it. 5 runs per size, medians.

| file size | manifest fetched | whole file fetched and hashed |
| ---: | ---: | ---: |
| 1 KiB | 5 ms | 0.06 s |
| 200 KiB | 4 ms | 0.07 s |
| 3 MiB | 5 ms | 0.33 s |
| 30 MiB | 5 ms | 3.0 s (2.8 to 5.9) |

- The manifest fetch shows that a provider answers for X and holds the manifest block. Only the full download shows that the whole file is there.
- A CID that nobody seeds: the request fails after 27.4 s (3 of 3 runs). A negative answer is a timeout.
- Not measured: a spot check of a few random blocks. The REST API has no call for it.

## 2. Block with transactions t1..tn: time to become the initial seed and to seed one feeder

B concatenates t1..tn into one file and uploads it. "Become seed" ends when the upload returns the CID. "Seed to 1 feeder" ends when F holds the whole block. Medians of 3.

| tx size | n | block size | become seed | seed to 1 feeder |
| ---: | ---: | ---: | ---: | ---: |
| 1 KiB | 10 | 10 KiB | 2 ms | 0.06 s |
| 1 KiB | 100 | 100 KiB | 3 ms | 0.06 s |
| 200 KiB | 10 | 2 MiB | 0.03 s | 0.24 s |
| 200 KiB | 100 | 20 MiB | 0.23 s | 1.9 s |
| 300 KiB | 10 | 3 MiB | 0.04 s | 0.33 s |
| 300 KiB | 100 | 30 MiB | 0.34 s | 2.8 s |
| 3 MiB | 10 | 30 MiB | 0.38 s | 2.8 s |
| 3 MiB | 100 | 300 MiB | 3.7 s | 29.7 s |

## 3. Same block: time to become a secondary seed of n files t1..tn and to seed one feeder

Each transaction is its own Storage file. Two variants, 16 files in parallel in both:

- **3a, from the network.** B downloads the n files from A. "Become seed" ends when B holds all n. A then deletes them, and F downloads the n files. A served 0 blocks during that phase in every run, so F was served by B alone.
- **3b, bytes already local.** B already has the transactions and uploads them as n files. F downloads the n files.

| tx size | n | become seed, 3a | become seed, 3b | seed to 1 feeder, 3a | seed to 1 feeder, 3b |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 KiB | 10 | 0.10 s | 13 ms | 0.09 s | 0.09 s |
| 1 KiB | 100 | 0.51 s | 0.22 s | 0.50 s | 0.50 s |
| 200 KiB | 10 | 0.14 s | 0.03 s | 0.13 s | 0.13 s |
| 200 KiB | 100 | 0.88 s | 0.39 s | 2.5 s | 2.2 s |
| 300 KiB | 10 | 0.16 s | 0.04 s | 0.15 s | 0.16 s |
| 300 KiB | 100 | 1.05 s | 0.43 s | 1.2 s | 2.8 s |
| 3 MiB | 10 | 1.3 s | 0.26 s | 0.88 s | 0.88 s |
| 3 MiB | 100 | 10.1 s | 2.6 s | 11.5 s | 10.7 s |

## 4. Comparison of 2 and 3

Total time, become seed plus seed to one feeder (sums of the medians above):

| tx size | n | 2: one block file | 3a: n files from the network | 3b: n files, bytes local |
| ---: | ---: | ---: | ---: | ---: |
| 1 KiB | 10 | 0.06 s | 0.19 s | 0.10 s |
| 1 KiB | 100 | 0.06 s | 1.0 s | 0.72 s |
| 200 KiB | 10 | 0.26 s | 0.27 s | 0.16 s |
| 200 KiB | 100 | 2.1 s | 3.4 s | 2.6 s |
| 300 KiB | 10 | 0.36 s | 0.31 s | 0.20 s |
| 300 KiB | 100 | 3.1 s | 2.3 s | 3.2 s |
| 3 MiB | 10 | 3.2 s | 2.2 s | 1.1 s |
| 3 MiB | 100 | 33.4 s | 21.7 s | 13.3 s |

- **Small transactions:** one block file wins. Each separate file costs about 5 ms on each side (its own manifest, lookup and request), so the n-file path grows with n while the block stays flat.
- **Large transactions:** n files win. One file downloads at about 10 MB/s whatever its size; 16 files in parallel reach about 27 MB/s in total. This comes from how v0.5.3 downloads a single file, not from the data.
- **Around 200 to 300 KiB per transaction** the two are about equal. With n = 100 the time to feed the n files varies between runs, about 1 s in some and 2.5 to 3 s in others, at both sizes.
- **Becoming a secondary seed from the network (3a)** costs 2 to 8 times the local upload of the same bytes, and roughly as much as feeding one peer.

## Does the formulation of 2 and 3 make sense?

Yes, with one split. Scenario 3 as written contains two costs: getting the n files and serving them. If the node already holds the transactions (for example from its mempool), only the per-file overhead remains. That is 3b, and 3b against 2 is the direct one-file-against-n-files comparison. 3a adds the fetch from the network.

## Limits

- Loopback only. On the live network, finding the provider takes seconds to minutes and the transfer depends on the link; neither is in these numbers.
- One feeder, parallelism 16, 3 runs per cell.
- A second run of the whole grid (`results-seed/s23-c16-rerun.csv`) gave medians within about 15% of these, except the cell affected by the run-to-run variation above (200 KiB, n = 100, 3a feed: 0.94 s against 2.5 s).
- n = 1000 with 1 KiB transactions did not complete: after some point every manifest request from F failed. Cause not found yet.
