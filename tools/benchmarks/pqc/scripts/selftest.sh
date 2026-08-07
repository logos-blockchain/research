#!/usr/bin/env bash
# =============================================================================
# make test — the consolidated fast verification gate (~1-2 min).
#
# CORRECTNESS tests (1-4) exercise the measurement pipeline and BLOCK (nonzero
# exit): harness micro-runs + correctness gates, cross-implementation size
# agreement, the three TLS stacks incl. the native no-OQS-provider negative
# control, the role-asymmetry stress harness (3b), the no-privilege governor
# path against a fixture (3c), and a schema round-trip through assemble.py.
#
# HYGIENE tests (5-7) check repo consistency (v1-compat merge fixture, the
# published_runs manifest, absence-array propagation) and only WARN — a
# hygiene failure must never block a 30-minute measurement run.
#
# EVERYTHING this script produces lives under one mktemp dir: it never writes
# into the results directory or bench/tls/pki/ (a test must not be able to leak
# into the published set or clobber certs a real run depends on).
#
# Fixture note: hygiene test 5 reads rasberrypi5-20260614T205226Z.json from the
# results directory as the schema-1.0.0 COMPATIBILITY FIXTURE (see
# analyze/published_runs.txt) — retired from the published set, but
# load-bearing here; do not delete it.
# =============================================================================
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"
# shellcheck source=setup/lib_platform.sh
source "$HERE/setup/lib_platform.sh"
RESULTS="$(pqb_results_dir "$HERE")"
export PQC_RESULTS_DIR="$RESULTS"   # merge.py must resolve the same directory
LOCK="$HERE/setup/versions.lock"
# shellcheck disable=SC1090
[ -f "$LOCK" ] && source "$LOCK"
OSSL="${OPENSSL_BIN:-openssl}"

T="$(mktemp -d /tmp/pqb-selftest.XXXXXX)"
trap 'rm -rf "$T"' EXIT

PASS=0; FAIL=0; WARN=0; SKIP=0
pass() { printf '  PASS  %s\n' "$1"; PASS=$((PASS+1)); }
fail() { printf '  FAIL  %s\n' "$1"; FAIL=$((FAIL+1)); }
warnf(){ printf '  WARN  %s\n' "$1"; WARN=$((WARN+1)); }
skip() { printf '  SKIP  %s\n' "$1"; SKIP=$((SKIP+1)); }

HAVE_CARGO=0
cargo --version >/dev/null 2>&1 && [ -x bench/rust/target/release/pqb-rust ] \
  && [ -x bench/rust-tls/target/release/pqb-rust-tls ] && HAVE_CARGO=1

KEMSIG="$T/kemsig.jsonl"; : > "$KEMSIG"
MICRO=(--iters 20 --warmup 5 --reps 1)

echo "== correctness 1: C harness micro-runs (correctness gate + row shape) =="
for spec in "kem ML-KEM-768" "sig ML-DSA-65" "kem X25519" "sig Ed25519"; do
  kind="${spec%% *}"; alg="${spec#* }"
  if ./bench/kem_sig/bench_pq --kind "$kind" --alg "$alg" "${MICRO[@]}" \
       >> "$KEMSIG" 2>"$T/err.txt"; then
    pass "bench_pq $alg (exit 0 — correctness gate passed)"
  else
    fail "bench_pq $alg exited $? ($(tail -1 "$T/err.txt" 2>/dev/null))"
  fi
done
python3 - "$KEMSIG" <<'PY' && pass "C rows: valid JSON, enabled, implementation field" || fail "C row shape"
import json,sys
rows=[json.loads(l) for l in open(sys.argv[1])]
assert len(rows)==4 and all(r["enabled"] for r in rows)
assert {r["implementation"] for r in rows} == {"liboqs","openssl"}
PY

echo "== correctness 1b: link targets (vendored liboqs, pinned OpenSSL) =="
# A successful build is not evidence — the failure mode that matters is
# building fine while linking the WRONG library (a system liboqs / another
# OpenSSL). Verify the actual link targets of the built binary.
if [ "$(uname -s)" = "Darwin" ]; then
  if otool -l bench/kem_sig/bench_pq | grep -A2 LC_RPATH | grep -q "$HERE/vendor/install/lib" \
     && otool -L bench/kem_sig/bench_pq | grep -q '@rpath/liboqs'; then
    pass "bench_pq links the VENDORED liboqs (rpath -> vendor/install/lib)"
  else
    fail "bench_pq rpath does not include $HERE/vendor/install/lib (pinned layout) — rebuild with 'make build'; if it persists, a wrong liboqs may be linked"
  fi
  if [ -n "${OPENSSL_PREFIX:-}" ] && otool -L bench/kem_sig/bench_pq | grep -q "$OPENSSL_PREFIX/lib/libcrypto"; then
    pass "bench_pq links the pinned OpenSSL ($OPENSSL_PREFIX)"
  else
    fail "bench_pq libcrypto is not the pinned OpenSSL ($(otool -L bench/kem_sig/bench_pq | grep libcrypto | head -1))"
  fi
else
  LIBOQS_RESOLVED="$(ldd bench/kem_sig/bench_pq 2>/dev/null | awk '/liboqs/{print $3}')"
  case "$LIBOQS_RESOLVED" in
    "$HERE"/vendor/install/lib/*) pass "bench_pq links the VENDORED liboqs ($LIBOQS_RESOLVED)" ;;
    *) fail "bench_pq resolves liboqs to '$LIBOQS_RESOLVED' — NOT the vendored build" ;;
  esac
  CRYPTO_RESOLVED="$(ldd bench/kem_sig/bench_pq 2>/dev/null | awk '/libcrypto/{print $3}')"
  if [ "${OPENSSL_PREFIX:-/usr}" = "/usr" ]; then
    [ -n "$CRYPTO_RESOLVED" ] && pass "bench_pq libcrypto: $CRYPTO_RESOLVED (system prefix, as locked)" \
      || fail "bench_pq has no resolvable libcrypto"
  else
    case "$CRYPTO_RESOLVED" in
      "$OPENSSL_PREFIX"/*) pass "bench_pq links the pinned OpenSSL ($CRYPTO_RESOLVED)" ;;
      *) fail "bench_pq libcrypto '$CRYPTO_RESOLVED' is not the locked prefix $OPENSSL_PREFIX" ;;
    esac
  fi
fi
case "${OQSPROVIDER_MODULE:-}" in
  "$HERE"/vendor/*) [ -f "$OQSPROVIDER_MODULE" ] && pass "oqs-provider module is the vendored one" \
      || fail "vendored oqs-provider module missing" ;;
  *) fail "oqs-provider module is not under vendor/ (${OQSPROVIDER_MODULE:-unset})" ;;
esac

echo "== correctness 2: Rust harness micro-runs + cross-implementation sizes =="
if [ "$HAVE_CARGO" = 1 ]; then
  for spec in "kem ML-KEM-768" "sig ML-DSA-65"; do
    kind="${spec%% *}"; alg="${spec#* }"
    ./bench/rust/target/release/pqb-rust --kind "$kind" --alg "$alg" "${MICRO[@]}" \
      >> "$KEMSIG" 2>/dev/null && pass "pqb-rust $alg" || fail "pqb-rust $alg"
    ./bench/rust-tls/target/release/pqb-rust-tls --kind "$kind" --alg "$alg" "${MICRO[@]}" \
      >> "$KEMSIG" 2>/dev/null && pass "pqb-rust-tls (aws-lc-rs) $alg" || fail "aws-lc-rs $alg"
  done
else
  skip "Rust micro-runs (cargo/harnesses unavailable)"
fi

echo "== correctness 3: TLS stacks + native no-provider negative control =="
PKI="$T/pki"; mkdir -p "$PKI"
gen_cert() { # replicates run_tls.sh gen_cert (ed25519, with the SAN webpki needs)
  "$OSSL" req -x509 -new -newkey ed25519 -nodes -keyout "$PKI/ca.key" -out "$PKI/ca.pem" \
      -days 30 -subj "/CN=PQB Selftest CA" >/dev/null 2>&1 &&
  "$OSSL" genpkey -algorithm ed25519 -out "$PKI/sv.key" >/dev/null 2>&1 &&
  "$OSSL" req -new -key "$PKI/sv.key" -out "$PKI/sv.csr" -subj "/CN=localhost" \
      -addext "subjectAltName = DNS:localhost" >/dev/null 2>&1 &&
  "$OSSL" x509 -req -in "$PKI/sv.csr" -CA "$PKI/ca.pem" -CAkey "$PKI/ca.key" \
      -copy_extensions copyall -out "$PKI/sv.pem" -days 30 -CAcreateserial >/dev/null 2>&1
}
gen_cert && pass "test PKI generated (in $T, never bench/tls/pki)" || fail "test PKI generation"
TLSARGS=(--ca "$PKI/ca.pem" --cert "$PKI/sv.pem" --key "$PKI/sv.key" \
         --connections 5 --warmup 2 --sig-alg ed25519)
ROWS="$T/tls_rows.jsonl"; : > "$ROWS"

./bench/tls/bench_tls --group X25519 "${TLSARGS[@]}" --label "X25519+ed25519" \
  --phase baseline --implementation openssl-native >> "$ROWS" 2>/dev/null
python3 -c "import json,sys; r=json.loads(open(sys.argv[1]).readlines()[-1]); assert r['enabled'] and not r['have_oqs_provider']" "$ROWS" \
  && pass "openssl-native baseline handshakes (no provider loaded)" \
  || fail "openssl-native baseline cell"

./bench/tls/bench_tls --group frodo640aes "${TLSARGS[@]}" --label negctl \
  --phase phase0 --implementation openssl-native >> "$ROWS" 2>/dev/null
python3 -c "import json,sys; r=json.loads(open(sys.argv[1]).readlines()[-1]); assert not r['enabled'] and 'group-not-supported' in r['reason']" "$ROWS" \
  && pass "negative control: provider-only group REJECTED in native mode" \
  || fail "native-mode isolation (provider algorithm accepted?)"

if [ -n "${OQSPROVIDER_MODULE:-}" ] && [ -f "$OQSPROVIDER_MODULE" ]; then
  OPENSSL_MODULES="$(dirname "$OQSPROVIDER_MODULE")" \
  ./bench/tls/bench_tls --group X25519MLKEM768 "${TLSARGS[@]}" \
    --label "X25519MLKEM768+ed25519" --phase phase0 --implementation oqs-provider \
    >> "$ROWS" 2>/dev/null
  python3 -c "import json,sys; r=json.loads(open(sys.argv[1]).readlines()[-1]); assert r['enabled'] and r['have_oqs_provider']" "$ROWS" \
    && pass "oqs-provider phase0 cell (provider loads + negotiates)" \
    || fail "oqs-provider cell"
else
  fail "oqs-provider module not found (make build should have produced it)"
fi

if [ "$HAVE_CARGO" = 1 ]; then
  ./bench/rust-tls/target/release/pqb-rust-tls --group X25519 "${TLSARGS[@]}" \
    --label "X25519+ed25519" --phase baseline >> "$ROWS" 2>/dev/null
  python3 -c "import json,sys; r=json.loads(open(sys.argv[1]).readlines()[-1]); assert r['enabled'] and r['implementation']=='rustls-awslc'" "$ROWS" \
    && pass "rustls-awslc baseline cell (webpki accepts the SAN certs)" \
    || fail "rustls-awslc cell"
else
  skip "rustls-awslc cell (cargo unavailable)"
fi

echo "== correctness 3b: role-asymmetry stress harness =="
STRESS=bench/stress/stress_roles
if [ ! -x "$STRESS" ]; then
  fail "stress harness not built (make build should have produced $STRESS)"
else
  # X25519 is the harness checking itself: both peers run the identical
  # operation, so anything but ~1.0 means the role plumbing is wrong, not that
  # the algorithm is asymmetric.
  "$STRESS" --kind kem --alg X25519 --duration-ms 200 --threads 2 > "$T/stress_x.json" 2>"$T/stress_x.err" \
    && python3 - "$T/stress_x.json" <<'PY' && pass "symmetric control: X25519 encoder/decoder ratio ~1.0" || fail "X25519 role ratio is not ~1.0 — role plumbing is wrong (see above)"
import json,sys
d=json.load(open(sys.argv[1]))
a=d["asymmetry"]
assert a["symmetric_by_construction"] is True, "X25519 not flagged symmetric"
r=a["latency_ratio_decoder_over_encoder"]
assert 0.75 <= r <= 1.33, f"X25519 decoder/encoder ratio {r} is not ~1.0"
assert a["cheaper_side"]=="neither", f"X25519 cheaper_side={a['cheaper_side']}"
PY

  # Shape + liveness on one PQ algorithm of each kind, and no failed operations:
  # a worker that cannot complete its op would otherwise show up as a fast role.
  for spec in "kem ML-KEM-768" "sig ML-DSA-65"; do
    k="${spec%% *}"; a="${spec#* }"
    "$STRESS" --kind "$k" --alg "$a" --duration-ms 200 --threads 2 > "$T/stress_$k.json" 2>/dev/null \
      && python3 - "$T/stress_$k.json" <<'PY' && pass "stress $k: three phases, both roles live, zero failures" || fail "stress harness output malformed for $k"
import json,sys
d=json.load(open(sys.argv[1]))
assert d["enabled"] and d["roles"]["encoder"] and d["roles"]["decoder"]
for ph in ("isolated","saturated","contended"):
    p=d["phases"][ph]
    for role in ("encoder","decoder"):
        g=p[role]
        assert g["ops"]>0, f"{ph}/{role} completed no operations"
        assert g["failures"]==0, f"{ph}/{role} had {g['failures']} failures"
        assert g["latency_ns"]["median"]>0, f"{ph}/{role} has no latency"
        assert g["latency_ns"]["samples"]>0, f"{ph}/{role} recorded no samples"
assert d["phases"]["contended"]["decoder"]["threads"]>=1
PY
  done

  # A build without an algorithm must say so in-band, not crash the sweep.
  if "$STRESS" --kind kem --alg NoSuchAlgorithm-9000 --duration-ms 50 2>/dev/null \
     | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['enabled'] is False and d['reason']"; then
    pass "unknown algorithm is a recorded absence, not a crash"
  else
    fail "unknown algorithm did not produce an absence row"
  fi

  # Classic McEliece keeps multi-megabyte arrays on the stack; a default-sized
  # pthread stack SIGBUSes on it. This is the regression guard for that fix.
  if OQS_MC=Classic-McEliece-348864; "$STRESS" --kind kem --alg "$OQS_MC" --duration-ms 200 --threads 2 >"$T/stress_mc.json" 2>/dev/null \
     && python3 -c "import json,sys; d=json.load(open('$T/stress_mc.json')); assert not d['enabled'] or d['phases']['isolated']['decoder']['ops']>0"; then
    pass "large-stack algorithm (Classic McEliece) runs on worker threads"
  else
    fail "Classic McEliece crashed a worker thread — check the worker stack size"
  fi
fi

echo "== correctness 3c: governor handling (no-privilege path) =="
# The sudo assessment recommends pinning the governor at boot so the run needs
# no privilege at all. That path is Linux-only and cannot be exercised on a Mac
# without a fixture, which is exactly why it once emitted a spurious "could not
# set governor" warning on a correctly configured machine.
GOVDIR="$T/cpufreq"
mkdir -p "$GOVDIR/cpu0/cpufreq" "$GOVDIR/cpu1/cpufreq"
echo performance > "$GOVDIR/cpu0/cpufreq/scaling_governor"
echo performance > "$GOVDIR/cpu1/cpufreq/scaling_governor"
gov_out="$(PQB_OS=linux PQB_CPUFREQ_ROOT="$GOVDIR" bash -c \
  'source setup/lib_platform.sh; pqb_set_governor_performance' 2>"$T/gov.err")"
gov_rc=$?
if [ "$gov_out" = performance ] && [ "$gov_rc" -eq 0 ] && ! grep -q WARN "$T/gov.err"; then
  pass "governor already 'performance': accepted silently, no privilege needed"
else
  fail "pre-set governor mishandled (out='$gov_out' rc=$gov_rc; $(cat "$T/gov.err"))"
fi

# cpu0 still reads 'performance' but cpu1 does not. The probe must not
# short-circuit on cpu0, or a partly-configured host would be recorded as clean.
echo ondemand > "$GOVDIR/cpu1/cpufreq/scaling_governor"
chmod a-w "$GOVDIR"/cpu*/cpufreq/scaling_governor 2>/dev/null || true
gov_out="$(PQB_OS=linux PQB_CPUFREQ_ROOT="$GOVDIR" bash -c \
  'source setup/lib_platform.sh; pqb_set_governor_performance' 2>/dev/null || true)"
chmod u+w "$GOVDIR"/cpu*/cpufreq/scaling_governor 2>/dev/null || true
if [ "$gov_out" != performance ]; then
  pass "a single non-performance core is not reported as performance"
else
  fail "governor probe short-circuits on cpu0 (a mixed-governor host looks clean)"
fi

echo "== correctness 4: schema round-trip through assemble.py =="
cat > "$T/meta.env" <<EOF
TOOL_VERSION=selftest
HOSTNAME=selftest
OS=$(uname -s | tr 'A-Z' 'a-z')
IS_RPI=0
TS_END_UTC=fixture
EOF
python3 - "$ROWS" "$T/tls.json" <<'PY'
import json,sys
rows=[json.loads(l) for l in open(sys.argv[1])]
json.dump({"available":True,"have_oqs_provider":True,
           "baseline":{"kem_group":"X25519","sig_alg":"ed25519","label":"X25519+ed25519"},
           "matrix":rows}, open(sys.argv[2],"w"))
PY
python3 bench/lib/assemble.py --meta "$T/meta.env" --lock "$LOCK" \
  --kemsig "$KEMSIG" --tls "$T/tls.json" --thermal /dev/null \
  --out "$T/result.json" >/dev/null 2>"$T/assemble.err"
python3 - "$T/result.json" $HAVE_CARGO <<'PY' && pass "round-trip: schema 2.0.0, totals, acceleration, phases, sums, sizes agree" || fail "schema round-trip (see above)"
import json,sys
d=json.load(open(sys.argv[1])); have_cargo=sys.argv[2]=="1"
assert d["schema_version"]=="2.0.0", "schema version"
prims=[r for r in d["kem"]+d["sig"] if r.get("enabled")]
assert prims and all(r.get("total",{}).get("sum_of_medians_ns") for r in prims), "totals"
assert all(r.get("acceleration") for r in prims), "acceleration fields"
assert not any("SIZE MISMATCH" in w for w in d["warnings"]), "cross-implementation size mismatch"
cells=[c for c in d["tls"]["matrix"] if c.get("enabled")]
assert cells and all(c.get("phase") and c.get("sig_alg") and c.get("implementation") for c in cells), "tls fields"
for c in cells:  # covered cells must have complete, per-stack-priced sums
    if c["implementation"]=="openssl-native" and c["phase"]=="baseline":
        assert c["handshake_primitive_sum"]["complete"], "native baseline sum incomplete"
        assert all(x["implementation"] in ("liboqs","openssl") for x in c["handshake_primitive_sum"]["components"]), "wrong pricing stack"
    if have_cargo and c["implementation"]=="rustls-awslc":
        assert all(x["implementation"]=="aws-lc-rs" for x in c["handshake_primitive_sum"]["components"]), "rustls cell not priced from aws-lc-rs"
PY

echo "== hygiene 5: schema-1.0.0 compatibility fixture through merge.py =="
FIX="$RESULTS/rasberrypi5-20260614T205226Z.json"
if [ -f "$FIX" ]; then
  python3 analyze/merge.py "$FIX" -o "$T/merged_v1.json" >/dev/null 2>&1
  python3 - "$FIX" "$T/merged_v1.json" <<'PY' && pass "v1 fixture: rows preserved, implementation/phase/totals injected" || warnf "v1 compatibility regressed"
import json,sys
src=json.load(open(sys.argv[1])); m=json.load(open(sys.argv[2]))
want=sum(len(r.get("operations") or {}) for k in ("kem","sig") for r in src[k] if r.get("enabled"))
got=len(m["kem"])+len(m["sig"])
assert got==want, f"row count {got}!={want}"
assert all(r.get("implementation") for r in m["kem"]+m["sig"]), "implementation injection"
assert all(r.get("total_sum_of_medians_ns") is not None for r in m["kem"]+m["sig"]), "derived totals"
assert all(r.get("phase") for r in m["tls"]), "phase inference"
PY
else
  warnf "fixture $FIX missing — it is the schema-1.0.0 compatibility fixture (see published_runs.txt); restore it"
fi

echo "== hygiene 6: published_runs manifest vs disk vs committed merged.json =="
python3 - <<'PY' && pass "manifest entries exist; merged.json matches the published set" || warnf "manifest/merged.json drift — re-run 'make merge'"
import json,os
results=os.environ["PQC_RESULTS_DIR"]
entries=[l.strip() for l in open("analyze/published_runs.txt")
         if l.strip() and not l.startswith("#")]
missing=[e for e in entries if not os.path.isfile(os.path.join(results,e))]
assert not missing, f"missing on disk: {missing}"
m=json.load(open("dashboard/data/merged.json"))
assert sorted(r["source_file"] for r in m["runs"])==sorted(entries), "merged.json != manifest"
PY

echo "== hygiene 7: absence rows propagate (never silently dropped) =="
python3 - <<'PY' && pass "merged.json carries kem/sig/tls _absent arrays with reasons" || warnf "absence arrays missing from merged.json"
import json
m=json.load(open("dashboard/data/merged.json"))
assert all(k in m for k in ("kem_absent","sig_absent","tls_absent"))
assert m["tls_absent"] and all(a.get("reason") for a in m["tls_absent"])
PY

echo
echo "selftest: $PASS passed, $FAIL failed, $WARN hygiene warnings, $SKIP skipped"
[ "$FAIL" -eq 0 ] || { echo "CORRECTNESS FAILURES — do not trust measurement output until fixed."; exit 1; }
[ "$WARN" -gt 0 ] && echo "(hygiene warnings do not block runs — fix when convenient)"
exit 0
