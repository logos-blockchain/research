# Delivery messages on Logos Storage

Measurements, 2026-11-18 and 2026-11-19.

**Question.** A delivery message is 1208 bytes: the commitment of a note, then its ciphertext. If senders publish delivery messages on Logos Storage, should each be an object of its own, or should many be stored as one object?

**Result.**

- One object per message does not scale: a node keeps 500 provider records and a writer re-announces 500 keys, so only the 500 most recent objects of a writer resolve. Each object also takes 67 KB on disk.
- One object per batch has neither limit on a private network.
- On the live test network, from two nodes behind the same NAT, 2 of 20 single messages were fetched and no batch, whole or in parts.

## Setup

| | |
| --- | --- |
| Node | `logos-storage-nim` v0.5.3 (`56854f4`), prebuilt darwin-arm64 |
| Networking | `nim-libp2p` v2.3.6 (`9281a6d`), vendored |
| Machine | Apple M3, 8 cores, home connection behind a NAT |
| Private network | a writer and a reader on loopback, the reader bootstrapped from the writer, `--nat=extip:127.0.0.1` |
| Live network | both nodes with `--network=logos.test`, 300 s warm-up, 60 s between upload and fetch |
| Script | `bench.py`; one CSV row per fetch |

A fetch is the manifest request (`GET /data/{cid}/network/manifest`, retried until it answers), then the stream (`GET /data/{cid}/network/stream`), then a byte comparison.

## 1. Private network

| | One object per message | One batch of 1000 messages (1.21 MB) |
| --- | ---: | ---: |
| Upload | 2.3 ms | 0.02 s |
| Disk on the writer | 67 197 B per message, 56 × the payload | 1 263 496 B, 1.05 × the payload |
| Fetch, one after the other | 0.065 s (median) | 0.17 s |
| Fetch, 16 in parallel | 250 messages in 1.13 s | |

A CID is 52 characters, 38 bytes.

Batch of 196 messages (236 768 B): 0.07 s whole; 0.24 s as 4 parts of 49 messages (59 192 B each).

## 2. The 500 most recent objects

| Objects uploaded by the writer | Fetch of the oldest objects |
| ---: | --- |
| 200 | 100 of 100 |
| 500 | 250 of 250 |
| 750 | the first 5 attempted, all fail |
| 1000 | the first 5 attempted, all fail |
| 2000 | the first 5 attempted, all fail |

The script stops after 5 failed fetches and records the remaining objects as not fetched. The failure is `Failed to fetch manifest … after 10 attempts: Key doesn't exist`, about 27 s per attempt. A wait of 120 s between upload and fetch changes nothing. A batch uploaded after the single objects resolves every time.

With 750 objects, fetched from the newest to the oldest:

| Index of the object | Result |
| --- | --- |
| 749, 740, 700, 650, 600, 550, 500, 450, 400, 350, 300, 250 | found in 0.01 s |
| 200, 100, 0 | not found |

Cause, in the source:

- v0.5.3 resolves providers through the Kademlia of `nim-libp2p` (`storage/discovery.nim`, `d.kad.getProviders`) and builds it with `KadDHTConfig.new(addressPolicy = …)`, so the defaults of the library apply.
- `libp2p/protocols/kademlia/types.nim` at `9281a6d`: `DefaultProviderRecordCapacity = 500`, `DefaultProvidedKeyCapacity = 500`, `DefaultProviderExpirationInterval = 48.hours`, `DefaultRepublishInterval = 10.minutes`.
- Only the manifest CID of an object is announced (`storage/blockexchange/engine/advertiser.nim`).

## 3. Live test network

Both nodes on one machine, behind the same NAT.

| Run | Single messages | Batch of 196 messages | Same batch in 4 parts |
| --- | --- | --- | --- |
| 1, default options | 2 of 12 fetched (4.4 s and 4.8 s); manifest found in 1 to 4 s for all 12 | manifest in 0.9 s, stream fails | 0 of 4 |
| 2, `--max-peers=16` | 0 of 8, manifest not found in 120 s | fails | 0 of 4 |

Run 1, reader log: `Exception in blockexc read loop` 182 times (`Stream Closed!` 180, `Stream Reset!` 2), `Unable to get send connection` 94, `Direct lookup failed` 49, `Block retries exhausted` 10. The nodes advertise relay addresses only.

Run 2, reader log: no relay address.

## 4. Cost for a recipient

A recipient cannot tell its messages from the others, so it reads every message of a period and tries each with each of its keys. Opening one message takes 200 µs on the same machine (`note-encryption` benchmark, node PR 4153).

| Messages in the period | Download | Trial decryption, 1 key | Trial decryption, 20 keys |
| ---: | ---: | ---: | ---: |
| 10 000 | 12 MB | 2 s | 40 s |
| 1 000 000 | 1.2 GB | 200 s | 67 min |

One core. Each address of a wallet has its own encryption key; 20 is an example, the wallet standard sets no number of addresses.

## Not measured

- A reader or a writer with a public address.
- More than two nodes on the private network. Provider records then spread over several nodes, each with the same bound.
- How long an object stays available when no node re-announces it. Provider records expire after 48 hours; blocks have a TTL of 30 days (`DefaultBlockTtl`).
- Batches above 2.4 MB.

## Files

| File | Content |
| --- | --- |
| `bench.py` | the script |
| `results-private-{200,500,1000,2000}.csv` | section 1 and 2 |
| `results-private-1000-settle120.csv` | section 2, with the 120 s wait |
| (none) | section 2, 750 objects from the newest to the oldest: run by hand with the functions of `bench.py`, output copied into the table |
| `results-private-parts.csv` | section 1, the batch in parts |
| `results-logos-test-{1,2}.csv`, `live-run-{1,2}.out` | section 3 |
| `logs/` | node logs of the live runs |

## Reproduce

```
./bench.py --network private --messages 200
./bench.py --network private --messages 1000
./bench.py --network private --messages 20 --batch-messages 196 --part-messages 49
./bench.py --network logos.test --messages 12 --parallel 6 --batch-messages 196 --part-messages 49 --warmup 300 --settle 60 --lookup-timeout 180
```

The binary is not in the repository. `bench.py` expects the prebuilt v0.5.3 of `logos-storage-nim` at `../pseudo-da-storage/bin/logos-storage-darwin-arm64-v0.5.3`.
