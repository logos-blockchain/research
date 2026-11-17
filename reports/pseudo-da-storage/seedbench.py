#!/usr/bin/env python3
"""Seeding scenarios on a private loopback network (logos-storage-nim v0.5.3).

Nodes: A = origin of the transactions (also bootstrap), B = node under test, F = feeder/verifier.
  s1  verify that B seeds CID X: F fetches the manifest, then the whole file; absent CID until 404
  s2  B uploads one block file (t1..tn concatenated), F downloads it
  s3a B fetches n files t1..tn from A (secondary seed), A drops them, F downloads the n files from B
  s3b B already holds the bytes and uploads them as n files, F downloads the n files from B
Usage: seedbench.py s1|s23 <out.csv> [reps] [concurrency]   (TX_BYTES="307200" overrides the transaction sizes)
"""
import csv, hashlib, os, shutil, subprocess, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
BIN = f"{HERE}/bin/logos-storage-darwin-arm64-v0.5.3"
D = f"{HERE}/data/seedbench"
API = {"A": 8080, "B": 8090, "F": 8100}
MET = {"A": 9500, "B": 9501, "F": 9502}
now = time.perf_counter


def req(node, path, method="GET", data=None, timeout=600):
    r = urllib.request.Request(f"http://127.0.0.1:{API[node]}/api/storage/v1/{path}", data=data, method=method,
                               headers={"Content-Type": "application/octet-stream", "Accept": "text/plain"})
    try:
        with urllib.request.urlopen(r, timeout=timeout) as f:
            return f.status, f.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def start():
    subprocess.run(["pkill", "-f", "logos-storage-darwin-arm64"]); time.sleep(1)
    shutil.rmtree(D, ignore_errors=True); os.makedirs(D)
    spr = None
    for k in "ABF":
        boot = f"--bootstrap-node={spr}" if spr else "--no-bootstrap-node"
        subprocess.Popen([BIN, boot, "--nat=extip:127.0.0.1", f"--data-dir={D}/{k}", f"--api-port={API[k]}",
                          f"--listen-port={API[k]+1}", "--metrics", f"--metrics-port={MET[k]}", "--log-level=warn",
                          f"--log-file={D}/{k}.log"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(5)
        if not spr:
            spr = req("A", "spr")[1].decode()
    time.sleep(5)


def sent(node):
    with urllib.request.urlopen(f"http://127.0.0.1:{MET[node]}/metrics", timeout=10) as f:
        for l in f.read().decode().splitlines():
            if l.startswith("storage_block_exchange_blocks_sent_total "):
                return float(l.split()[1])
    return 0.0


def upload(node, data):
    return req(node, "data", "POST", data)[1].decode()


def manifest(node, cid, limit=120):
    t0 = now()
    while now() - t0 < limit:
        if req(node, f"data/{cid}/network/manifest", timeout=60)[0] == 200:
            return True
        time.sleep(0.02)
    return False


def fetch(node, cid, digest):
    if not manifest(node, cid):
        return False
    code, body = req(node, f"data/{cid}/network/stream")
    return code == 200 and hashlib.sha256(body).digest() == digest


def fetch_all(node, cids, digests, c):
    with ThreadPoolExecutor(c) as ex:
        return sum(ex.map(lambda p: fetch(node, *p), zip(cids, digests)))


def drop(node, cids):
    with ThreadPoolExecutor(16) as ex:
        list(ex.map(lambda x: req(node, f"data/{x}", "DELETE"), cids))


def s1(out, reps):
    w = csv.writer(open(out, "w")); w.writerow("size_bytes,rep,manifest_s,full_s,ok".split(","))
    for size in (1024, 204800, 3145728, 31457280):
        for rep in range(reps):
            x = os.urandom(size); cid = upload("B", x)
            t0 = now(); m = manifest("F", cid); t1 = now()
            ok = fetch("F", cid, hashlib.sha256(x).digest()); t2 = now()
            w.writerow([size, rep, f"{t1-t0:.4f}", f"{t2-t0:.4f}", int(m and ok)]); print(size, rep, t1 - t0, t2 - t0, ok, flush=True)
            drop("F", [cid]); drop("B", [cid])
    for rep in range(3):  # CID nobody seeds
        cid = upload("A", os.urandom(1024)); drop("A", [cid]); time.sleep(1)
        t0 = now(); code = req("F", f"data/{cid}/network/manifest")[0]
        w.writerow(["absent", rep, f"{now()-t0:.4f}", "", code]); print("absent", now() - t0, code, flush=True)


def s23(out, reps, c):
    out_f = open(out, "w"); w = csv.writer(out_f)
    w.writerow("scenario,n,tx_bytes,rep,conc,seed_s,feed_s,ok,origin_blocks_in_feed".split(","))
    sizes = [int(x) for x in os.environ.get("TX_BYTES", "1024 204800 3145728").split()]
    for n, s in [(n, s) for s in sizes for n in (10, 100)]:
        for rep in range(reps):
            txs = [os.urandom(s) for _ in range(n)]; dg = [hashlib.sha256(t).digest() for t in txs]
            # s2: one block file
            blk = b"".join(txs); bd = hashlib.sha256(blk).digest()
            t0 = now(); cid = upload("B", blk); t1 = now()
            ok = fetch("F", cid, bd); t2 = now()
            w.writerow(["s2", n, s, rep, 1, f"{t1-t0:.4f}", f"{t2-t1:.4f}", int(ok), 0])
            drop("F", [cid]); drop("B", [cid])
            # s3b: B holds the bytes, uploads n files
            t0 = now()
            with ThreadPoolExecutor(c) as ex:
                cids = list(ex.map(lambda t: upload("B", t), txs))
            t1 = now(); got = fetch_all("F", cids, dg, c); t2 = now()
            w.writerow(["s3b", n, s, rep, c, f"{t1-t0:.4f}", f"{t2-t1:.4f}", int(got == n), 0])
            drop("F", cids); drop("B", cids)
            # s3a: B fetches n files from A, A drops them, F fetches from B (fresh bytes, so no CID was seen before)
            txs = [os.urandom(s) for _ in range(n)]; dg = [hashlib.sha256(t).digest() for t in txs]
            with ThreadPoolExecutor(c) as ex:
                cids = list(ex.map(lambda t: upload("A", t), txs))
            time.sleep(0.5)
            t0 = now(); got_b = fetch_all("B", cids, dg, c); t1 = now()
            drop("A", cids); a0 = sent("A")
            t2 = now(); got = fetch_all("F", cids, dg, c); t3 = now()
            w.writerow(["s3a", n, s, rep, c, f"{t1-t0:.4f}", f"{t3-t2:.4f}", int(got_b == n and got == n), int(sent("A") - a0)])
            drop("F", cids); drop("B", cids); out_f.flush()
            print(n, s, rep, "done", flush=True)


if __name__ == "__main__":
    mode, out = sys.argv[1], sys.argv[2]
    reps = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    start()
    try:
        s1(out, reps) if mode == "s1" else s23(out, reps, int(sys.argv[4]) if len(sys.argv) > 4 else 16)
    finally:
        subprocess.run(["pkill", "-f", "logos-storage-darwin-arm64"])
