#!/usr/bin/env python3
"""Delivery messages on Logos Storage: one object per message against one object per batch.

Two logos-storage-nim nodes on this machine, a writer (the sender, or an archiver) and a reader
(the recipient's wallet). `--network private` is the protocol floor: no relay, no live DHT, the
reader bootstrapped from the writer. `--network logos.test` joins the live testnet from both.

    ./bench.py --network private --messages 200 1000 --parallel 16
    ./bench.py --network logos.test --messages 20 --warmup 300

Writes results-<network>.csv (one row per fetch) and prints a summary.
"""
import argparse
import concurrent.futures
import csv
import os
import pathlib
import shutil
import statistics
import subprocess
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
BINARY = HERE.parent / "pseudo-da-storage" / "bin" / "logos-storage-darwin-arm64-v0.5.3"
MESSAGE = 1208  # a delivery message: commitment || note ciphertext
WRITER, READER = "http://127.0.0.1:8180/api/storage/v1", "http://127.0.0.1:8190/api/storage/v1"
BASE58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def http(method, url, data=None, timeout=120, headers=None):
    request = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.read()


def start(name, ports, extra):
    data = HERE / "data" / name
    shutil.rmtree(data, ignore_errors=True)
    data.mkdir(parents=True)
    api, listen = ports
    command = [
        str(BINARY),
        f"--data-dir={data}",
        f"--api-port={api}",
        f"--listen-port={listen}",
        "--log-level=info",
        f"--log-file={data / 'node.log'}",
        *extra,
    ]
    return subprocess.Popen(command, stdout=open(data / "stdout.log", "w"), stderr=subprocess.STDOUT)


def wait_api(base):
    for _ in range(120):
        try:
            return http("GET", f"{base}/spr", headers={"Accept": "text/plain"})[1].decode().strip()
        except (urllib.error.URLError, ConnectionError, OSError):
            time.sleep(0.5)
    raise SystemExit(f"{base} did not come up")


def upload(payload):
    started = time.time()
    _, cid = http(
        "POST", f"{WRITER}/data", payload, headers={"Content-Type": "application/octet-stream"}
    )
    return cid.decode().strip(), time.time() - started


def fetch(cid, expected, lookup_timeout):
    """Seconds until the reader resolves the manifest, then seconds to stream the object."""
    started = time.time()
    while True:
        try:
            if http("GET", f"{READER}/data/{cid}/network/manifest", timeout=30)[0] == 200:
                break
        except (urllib.error.URLError, ConnectionError, OSError):
            pass
        if time.time() - started > lookup_timeout:
            return time.time() - started, None, False
        time.sleep(0.05)
    resolved = time.time()
    try:
        body = http("GET", f"{READER}/data/{cid}/network/stream", timeout=lookup_timeout)[1]
    except (urllib.error.URLError, ConnectionError, OSError):
        return resolved - started, None, False
    return resolved - started, time.time() - resolved, body == expected


def cid_bytes(cid):
    if not cid.startswith("z"):
        return None
    number = 0
    for character in cid[1:]:
        number = number * 58 + BASE58.index(character)
    return (number.bit_length() + 7) // 8


def directory_size(path):
    return sum(file.stat().st_size for file in pathlib.Path(path).rglob("*") if file.is_file())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--network", default="private")
    parser.add_argument("--messages", type=int, nargs="+", default=[200])
    parser.add_argument("--parallel", type=int, default=16)
    parser.add_argument("--warmup", type=int, default=0, help="seconds on the live network first")
    parser.add_argument("--lookup-timeout", type=int, default=20)
    parser.add_argument("--node-arg", action="append", default=[], help="extra argument for both nodes on a live network")
    parser.add_argument("--settle", type=int, default=0, help="seconds between uploads and fetches")
    parser.add_argument("--part-messages", type=int, default=0, help="also store the batch in parts of this many messages")
    parser.add_argument("--batch-messages", type=int, default=0, help="size of the batch, default: the per-message count")
    args = parser.parse_args()

    private = args.network == "private"
    nodes = []
    try:
        if private:
            nodes.append(start("writer", (8180, 8181), ["--no-bootstrap-node", "--nat=extip:127.0.0.1"]))
            spr = wait_api(WRITER)
            nodes.append(
                start("reader", (8190, 8191), [f"--bootstrap-node={spr}", "--nat=extip:127.0.0.1"])
            )
        else:
            nodes.append(start("writer", (8180, 8181), [f"--network={args.network}", *args.node_arg]))
            nodes.append(start("reader", (8190, 8191), [f"--network={args.network}", *args.node_arg]))
            wait_api(WRITER)
        wait_api(READER)
        time.sleep(6 + args.warmup)

        rows = []
        for count in args.messages:
            messages = [os.urandom(MESSAGE) for _ in range(count)]
            before = directory_size(HERE / "data" / "writer")

            # One object per message: the sender uploads its message and inscribes its CID.
            started = time.time()
            uploads = [upload(message) for message in messages]
            upload_each = time.time() - started
            per_message_disk = directory_size(HERE / "data" / "writer") - before
            cids = [cid for cid, _ in uploads]
            time.sleep(args.settle)

            failures = []

            # After 5 failures the rest is not attempted: each one waits the whole timeout.
            def one(index):
                if len(failures) >= 5:
                    return 0.0, None, False
                result = fetch(cids[index], messages[index], args.lookup_timeout)
                if not result[2]:
                    failures.append(index)
                return result

            # The reader fetches a first half one after the other, the second half in parallel.
            half = count // 2
            started = time.time()
            sequential = [one(index) for index in range(half)]
            sequential_total = time.time() - started
            started = time.time()
            with concurrent.futures.ThreadPoolExecutor(args.parallel) as pool:
                parallel = list(pool.map(one, range(half, count)))
            parallel_total = time.time() - started
            for mode, results in (("sequential", sequential), ("parallel", parallel)):
                for lookup, download, ok in results:
                    rows.append([args.network, count, "per-message", mode, MESSAGE, lookup, download, ok])

            # One object for all of them: an archiver uploads the batch and inscribes one CID.
            batch_messages = messages if not args.batch_messages else [os.urandom(MESSAGE) for _ in range(args.batch_messages)]
            batch = b"".join(batch_messages)
            before = directory_size(HERE / "data" / "writer")
            batch_cid, upload_batch = upload(batch)
            batch_disk = directory_size(HERE / "data" / "writer") - before
            lookup, download, ok = fetch(batch_cid, batch, args.lookup_timeout)
            rows.append([args.network, count, "batch", "single", len(batch), lookup, download, ok])

            # The same batch in parts, each an object of its own: what a reader behind a relay can fetch.
            part_results = []
            if args.part_messages:
                step = args.part_messages * MESSAGE
                parts = [batch[i : i + step] for i in range(0, len(batch), step)]
                part_cids = [upload(part)[0] for part in parts]
                time.sleep(args.settle)
                started = time.time()
                for part, part_cid in zip(parts, part_cids):
                    result = fetch(part_cid, part, args.lookup_timeout)
                    part_results.append(result)
                    rows.append([args.network, count, "parts", "sequential", len(part), *result])
                parts_total = time.time() - started

            def summary(results):
                good = [lookup + download for lookup, download, ok in results if ok]
                if not good:
                    return "all failed"
                first_failure = next((i for i, result in enumerate(results) if not result[2]), None)
                return (
                    f"{len(good)}/{len(results)} ok, per message median {statistics.median(good):.3f} s, "
                    f"max {max(good):.3f} s, first failure at {first_failure}"
                )

            print(f"\n== {count} messages of {MESSAGE} bytes, network {args.network}", flush=True)
            print(f"CID: {len(cids[0])} characters, {cid_bytes(cids[0])} bytes ({cids[0]})")
            print(
                f"upload, one object per message: {upload_each:.2f} s total, "
                f"{1000 * upload_each / count:.1f} ms each, "
                f"{per_message_disk / count:.0f} bytes on disk per message"
            )
            print(f"fetch sequential ({half}): {sequential_total:.2f} s total; {summary(sequential)}")
            print(
                f"fetch parallel x{args.parallel} ({count - half}): {parallel_total:.2f} s total; "
                f"{summary(parallel)}"
            )
            print(
                f"batch of {len(batch)} bytes: upload {upload_batch:.2f} s, {batch_disk} bytes on disk, "
                f"lookup {lookup:.2f} s, download {download if download is None else round(download, 2)} s, "
                f"ok {ok}"
            )
            if part_results:
                good = [lookup + download for lookup, download, ok in part_results if ok]
                print(
                    f"same batch in {len(part_results)} parts of {args.part_messages} messages: {len(good)}/{len(part_results)} ok, "
                    f"{parts_total:.2f} s total, per part median {statistics.median(good) if good else float('nan'):.2f} s",
                    flush=True,
                )

        out = HERE / f"results-{args.network}.csv"
        with open(out, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                ["network", "messages", "layout", "mode", "object_bytes", "lookup_s", "download_s", "ok"]
            )
            writer.writerows(rows)
        print(f"\n{out}")
    finally:
        for node in nodes:
            node.terminate()
        for node in nodes:
            try:
                node.wait(timeout=20)
            except subprocess.TimeoutExpired:
                node.kill()


if __name__ == "__main__":
    main()
