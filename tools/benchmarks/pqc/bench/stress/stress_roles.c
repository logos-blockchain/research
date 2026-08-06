/* ===========================================================================
 * stress_roles.c — sender/receiver (encoder/decoder) asymmetry under load.
 *
 * bench_pq.c answers "what does one operation cost?" one operation at a time,
 * on an idle pinned core. This harness answers a different question: when the
 * two sides of an exchange run FLAT OUT AT THE SAME TIME, how does the cost
 * split between them?
 *
 * That split is a protocol-design number, not a microbenchmark curiosity. If
 * producing a message is much cheaper than consuming it, a sender can impose
 * more work than it performs — the receiver is the side that falls over first,
 * and it falls over at a rate set by the ratio, not by either side's absolute
 * speed.
 *
 * ---- the role model -------------------------------------------------------
 * ENCODER = the side that PRODUCES the wire object.
 * DECODER = the side that CONSUMES it.
 *
 *   KEM  encoder = encaps   (produces the ciphertext)
 *        decoder = decaps   (consumes it, using its own secret key)
 *        keygen is measured separately as decoder SETUP: the decoder is the
 *        side that must publish a public key first. Two cost models follow,
 *        and both are reported because both occur in practice:
 *          per_message — a long-lived key, keygen amortised away
 *          per_session — an ephemeral keypair per exchange (the TLS shape),
 *                        so the decoder pays keygen + decaps every time
 *   SIG  encoder = sign     (produces the signature)
 *        decoder = verify   (consumes it)
 *        signature keys are long-lived identities, so keygen is not part of
 *        either per-message cost; it is still reported for completeness.
 *
 * The classical Logos baselines are measured under the SAME role model, via
 * OpenSSL EVP, because the migration question is not "how expensive is PQ" but
 * "does PQ move the cost from one side to the other":
 *   X25519    both sides perform the identical operation (a keygen and a
 *             derive), so the exchange is symmetric BY CONSTRUCTION. Its
 *             measured ratio of ~1.0 doubles as a check on this harness.
 *   Ed25519   encoder = sign, decoder = verify, as for any signature.
 *
 * ---- the phases -----------------------------------------------------------
 *   isolated   one thread, one role at a time. Uncontended cost per role: the
 *              latency ratio here is the algorithm's intrinsic asymmetry.
 *   saturated  T threads, one role at a time. Each role's throughput ceiling
 *              on this machine. The ratio of ceilings is what a deployment
 *              actually experiences, and it can differ from the isolated ratio
 *              when the two roles have different memory or cache behaviour.
 *   contended  1 encoder thread against T decoder threads, CONCURRENTLY. The
 *              adversarial shape: one sender, a receiver with the whole
 *              machine. If the encoder still outruns T decoders, the ratio is
 *              a denial-of-service multiplier rather than a curiosity.
 *
 * Every phase reports completed operations, sustained rate, and the latency
 * distribution from an unbiased reservoir sample (so a 30-second run at a
 * million ops/sec does not need a gigabyte of timestamps).
 *
 * NOT a reference-grade measurement, deliberately: it uses every core, so it
 * is a throughput measurement subject to thermal and scheduler effects that
 * the single-pinned-core protocol exists to exclude. Ratios between roles
 * measured in the same phase are the durable output; absolute rates are not
 * comparable across machines.
 *
 *   stress_roles --kind kem --alg ML-KEM-768 --duration-ms 2000 --threads 8
 *
 * Emits one JSON object per invocation on stdout.
 * ===========================================================================*/
#define _POSIX_C_SOURCE 200809L
/* sysconf(_SC_NPROCESSORS_ONLN) is an XSI/GNU extension that strict POSIX
 * hides; both feature macros below are needed to see it on glibc and on
 * macOS respectively. online_cpus() still falls back if it is absent. */
#define _DEFAULT_SOURCE
#define _DARWIN_C_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <math.h>
#include <time.h>
#include <unistd.h>
#include <pthread.h>

#include <oqs/oqs.h>
#include <openssl/evp.h>

#define MSGLEN 32
#define DEFAULT_SAMPLE_CAP 100000u
#define MAX_THREADS 256
/* Worker stacks are set explicitly: the default pthread stack (512 KB on
 * macOS, 8 MB on glibc) is not enough for the largest Classic McEliece
 * parameter sets, which keep multi-megabyte working arrays on the stack.
 * bench_pq never hit this because it runs on the main thread, whose stack the
 * kernel grows on demand; a pthread stack is a fixed mapping and overflowing
 * it is an immediate SIGBUS/SIGSEGV rather than an error we could report.
 * 32 MB is lazily committed, so the cost of the headroom is address space. */
#define WORKER_STACK_BYTES (32u * 1024u * 1024u)

static volatile int g_stop = 0;   /* set by the driver thread to end a phase */
static uint64_t g_sink = 0;       /* keeps the optimiser from eliding work   */

static inline uint64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
}

/* Saturation width defaults to every online core: the point of the saturated
 * and contended phases is what the machine can actually absorb. */
static int online_cpus(void) {
#if defined(_SC_NPROCESSORS_ONLN)
    long n = sysconf(_SC_NPROCESSORS_ONLN);
    if (n > 0) return (int)n;
#endif
    return 4;
}

static void sleep_ms(unsigned ms) {
    struct timespec ts = { .tv_sec = ms / 1000, .tv_nsec = (long)(ms % 1000) * 1000000L };
    nanosleep(&ts, NULL);
}

/* ---- statistics ---------------------------------------------------------- */
typedef struct {
    double median, mad, p95, p99, min, max, mean;
    uint64_t n;
} lat_t;

static int cmp_u64(const void *a, const void *b) {
    uint64_t x = *(const uint64_t *)a, y = *(const uint64_t *)b;
    return (x > y) - (x < y);
}

static double pct_sorted(const uint64_t *s, uint64_t n, double p) {
    if (n == 0) return 0;
    if (n == 1) return (double)s[0];
    double idx = p * (double)(n - 1);
    uint64_t lo = (uint64_t)idx;
    double frac = idx - (double)lo;
    if (lo + 1 >= n) return (double)s[n - 1];
    return (double)s[lo] + frac * ((double)s[lo + 1] - (double)s[lo]);
}

static lat_t latency_of(uint64_t *s, uint64_t n) {
    lat_t l; memset(&l, 0, sizeof l);
    l.n = n;
    if (n == 0) return l;
    qsort(s, n, sizeof(uint64_t), cmp_u64);
    l.min = (double)s[0];
    l.max = (double)s[n - 1];
    l.median = pct_sorted(s, n, 0.5);
    l.p95 = pct_sorted(s, n, 0.95);
    l.p99 = pct_sorted(s, n, 0.99);
    double sum = 0;
    for (uint64_t i = 0; i < n; i++) sum += (double)s[i];
    l.mean = sum / (double)n;
    uint64_t *dev = malloc(n * sizeof(uint64_t));
    if (dev) {
        for (uint64_t i = 0; i < n; i++) {
            double d = (double)s[i] - l.median;
            dev[i] = (uint64_t)(d < 0 ? -d : d);
        }
        qsort(dev, n, sizeof(uint64_t), cmp_u64);
        l.mad = pct_sorted(dev, n, 0.5);
        free(dev);
    }
    return l;
}

/* ---- per-thread work ----------------------------------------------------- */
/* Each worker owns its algorithm object and every buffer it touches: no shared
 * mutable state, so what the phase measures is the roles competing for CPU and
 * memory bandwidth, never for a lock this harness introduced. */
typedef enum { OP_KEM_KEYGEN, OP_KEM_ENCAPS, OP_KEM_DECAPS,
               OP_SIG_KEYGEN, OP_SIG_SIGN, OP_SIG_VERIFY,
               OP_X25519_KEYGEN, OP_X25519_DERIVE,
               OP_ED_KEYGEN, OP_ED_SIGN, OP_ED_VERIFY } op_kind;

typedef struct {
    op_kind op;
    const char *alg;
    /* KEM state */
    OQS_KEM *kem;
    uint8_t *pk, *sk, *ct, *ss_a, *ss_b, *pk_s, *sk_s;
    /* SIG state */
    OQS_SIG *sig;
    uint8_t *msg, *sg; size_t sglen;
    uint8_t *sg_s; size_t sg_s_len;
    /* classical (OpenSSL EVP) state */
    EVP_PKEY *ev_self, *ev_peer, *ev_scratch;
    unsigned char ed_msg[MSGLEN], ed_sig[64]; size_t ed_siglen;
    /* results */
    uint64_t ops, busy_ns, failures;
    uint64_t *samples; uint64_t nsamples, cap, seen;
    uint64_t rng;
    pthread_t tid;
} worker_t;

static inline uint64_t xorshift64(uint64_t *s) {
    uint64_t x = *s;
    x ^= x << 13; x ^= x >> 7; x ^= x << 17;
    return (*s = x);
}

/* Reservoir sampling (Vitter R): an unbiased sample of the whole run, not just
 * its first moments — a truncated buffer would report the warm-up. */
static inline void record(worker_t *w, uint64_t ns) {
    w->seen++;
    if (w->nsamples < w->cap) {
        w->samples[w->nsamples++] = ns;
    } else {
        uint64_t j = xorshift64(&w->rng) % w->seen;
        if (j < w->cap) w->samples[j] = ns;
    }
}

/* ---- classical (OpenSSL EVP) roles --------------------------------------
 * Same shape as the liboqs roles: each worker owns its keys, and the timed
 * call is the whole operation a peer actually performs — for X25519 that is
 * one derive against a fixed peer share, for Ed25519 one sign or one verify.
 * Context objects are created and freed inside the timed call because that is
 * what an implementation does per exchange; hoisting them out would measure a
 * shape no protocol uses. */
static EVP_PKEY *evp_keygen(int id) {
    EVP_PKEY *k = NULL;
    EVP_PKEY_CTX *p = EVP_PKEY_CTX_new_id(id, NULL);
    if (!p) return NULL;
    if (EVP_PKEY_keygen_init(p) <= 0 || EVP_PKEY_keygen(p, &k) <= 0) k = NULL;
    EVP_PKEY_CTX_free(p);
    return k;
}

static int evp_derive_into(EVP_PKEY *a, EVP_PKEY *b, unsigned char out[32]) {
    EVP_PKEY_CTX *p = EVP_PKEY_CTX_new(a, NULL);
    if (!p) return 0;
    size_t slen = 32;
    int ok = EVP_PKEY_derive_init(p) > 0 &&
             EVP_PKEY_derive_set_peer(p, b) > 0 &&
             EVP_PKEY_derive(p, out, &slen) > 0;
    EVP_PKEY_CTX_free(p);
    return ok;
}

static int evp_sign(worker_t *w) {
    EVP_MD_CTX *m = EVP_MD_CTX_new();
    if (!m) return 1;
    w->ed_siglen = sizeof w->ed_sig;
    int ok = EVP_DigestSignInit(m, NULL, NULL, NULL, w->ev_self) > 0 &&
             EVP_DigestSign(m, w->ed_sig, &w->ed_siglen, w->ed_msg, MSGLEN) > 0;
    EVP_MD_CTX_free(m);
    if (!ok) return 1;
    g_sink += w->ed_sig[0];
    return 0;
}

static int evp_verify(worker_t *w) {
    EVP_MD_CTX *m = EVP_MD_CTX_new();
    if (!m) return 1;
    int ok = EVP_DigestVerifyInit(m, NULL, NULL, NULL, w->ev_self) > 0 &&
             EVP_DigestVerify(m, w->ed_sig, w->ed_siglen, w->ed_msg, MSGLEN) > 0;
    EVP_MD_CTX_free(m);
    if (!ok) return 1;
    g_sink += 1;
    return 0;
}

static int do_op(worker_t *w) {
    switch (w->op) {
    case OP_KEM_KEYGEN:
        if (OQS_KEM_keypair(w->kem, w->pk_s, w->sk_s) != OQS_SUCCESS) return 1;
        g_sink += w->pk_s[0]; return 0;
    case OP_KEM_ENCAPS:
        if (OQS_KEM_encaps(w->kem, w->ct, w->ss_a, w->pk) != OQS_SUCCESS) return 1;
        g_sink += w->ct[0]; return 0;
    case OP_KEM_DECAPS:
        if (OQS_KEM_decaps(w->kem, w->ss_b, w->ct, w->sk) != OQS_SUCCESS) return 1;
        g_sink += w->ss_b[0]; return 0;
    case OP_SIG_KEYGEN:
        if (OQS_SIG_keypair(w->sig, w->pk_s, w->sk_s) != OQS_SUCCESS) return 1;
        g_sink += w->pk_s[0]; return 0;
    case OP_SIG_SIGN:
        w->sg_s_len = w->sig->length_signature;
        if (OQS_SIG_sign(w->sig, w->sg_s, &w->sg_s_len, w->msg, MSGLEN, w->sk)
            != OQS_SUCCESS) return 1;
        g_sink += w->sg_s[0]; return 0;
    case OP_SIG_VERIFY:
        if (OQS_SIG_verify(w->sig, w->msg, MSGLEN, w->sg, w->sglen, w->pk)
            != OQS_SUCCESS) return 1;
        g_sink += 1; return 0;
    case OP_X25519_KEYGEN:
    case OP_ED_KEYGEN: {
        int id = (w->op == OP_X25519_KEYGEN) ? EVP_PKEY_X25519 : EVP_PKEY_ED25519;
        EVP_PKEY *k = evp_keygen(id);
        if (!k) return 1;
        if (w->ev_scratch) EVP_PKEY_free(w->ev_scratch);
        w->ev_scratch = k;
        g_sink += 1; return 0;
    }
    case OP_X25519_DERIVE: {
        unsigned char secret[32];
        if (!evp_derive_into(w->ev_self, w->ev_peer, secret)) return 1;
        g_sink += secret[0]; return 0;
    }
    case OP_ED_SIGN:   return evp_sign(w);
    case OP_ED_VERIFY: return evp_verify(w);
    }
    return 1;
}

static void *worker_main(void *arg) {
    worker_t *w = arg;
    while (!g_stop) {
        uint64_t t0 = now_ns();
        int rc = do_op(w);
        uint64_t dt = now_ns() - t0;
        if (rc) { w->failures++; continue; }
        w->ops++;
        w->busy_ns += dt;
        record(w, dt);
    }
    return NULL;
}

/* ---- per-role state setup ------------------------------------------------ */
static void die(const char *alg, const char *what) {
    fprintf(stderr, "FATAL [%s]: %s\n", alg, what);
    exit(3);
}

/* Every worker gets its own algorithm object and its own VALIDATED inputs: a
 * decaps worker decapsulates a ciphertext that really matches its secret key,
 * a verify worker verifies a signature that really verifies. Measuring the
 * rejection path by accident would understate the decoder's cost — for several
 * of these algorithms a malformed input is rejected far earlier than a valid
 * one is accepted. */
static void worker_init(worker_t *w, const char *kind, const char *alg,
                        op_kind op, uint64_t cap, uint64_t seed) {
    memset(w, 0, sizeof *w);
    w->op = op; w->alg = alg; w->cap = cap; w->rng = seed | 1u;
    w->samples = calloc(cap, sizeof(uint64_t));
    if (!w->samples) die(alg, "out of memory (sample buffer)");

    if (w->op == OP_X25519_KEYGEN || w->op == OP_X25519_DERIVE) {
        w->ev_self = evp_keygen(EVP_PKEY_X25519);
        w->ev_peer = evp_keygen(EVP_PKEY_X25519);
        if (!w->ev_self || !w->ev_peer) die(alg, "X25519 keygen failed");
        unsigned char sa[32], sb[32];
        if (!evp_derive_into(w->ev_self, w->ev_peer, sa) ||
            !evp_derive_into(w->ev_peer, w->ev_self, sb)) die(alg, "X25519 derive failed");
        if (memcmp(sa, sb, 32) != 0)
            die(alg, "X25519 shared-secret mismatch — refusing to stress a broken build");
        return;
    }
    if (w->op == OP_ED_KEYGEN || w->op == OP_ED_SIGN || w->op == OP_ED_VERIFY) {
        w->ev_self = evp_keygen(EVP_PKEY_ED25519);
        if (!w->ev_self) die(alg, "Ed25519 keygen failed");
        memset(w->ed_msg, 0xA5, MSGLEN);
        if (evp_sign(w) != 0) die(alg, "Ed25519 sign failed");
        if (evp_verify(w) != 0)
            die(alg, "Ed25519 verify failed on a valid signature — refusing to stress a broken build");
        return;
    }
    if (strcmp(kind, "kem") == 0) {
        w->kem = OQS_KEM_new(alg);
        if (!w->kem) die(alg, "KEM not enabled in this liboqs build");
        w->pk   = malloc(w->kem->length_public_key);
        w->sk   = malloc(w->kem->length_secret_key);
        w->ct   = malloc(w->kem->length_ciphertext);
        w->ss_a = malloc(w->kem->length_shared_secret);
        w->ss_b = malloc(w->kem->length_shared_secret);
        w->pk_s = malloc(w->kem->length_public_key);
        w->sk_s = malloc(w->kem->length_secret_key);
        if (!w->pk||!w->sk||!w->ct||!w->ss_a||!w->ss_b||!w->pk_s||!w->sk_s)
            die(alg, "out of memory");
        if (OQS_KEM_keypair(w->kem, w->pk, w->sk) != OQS_SUCCESS) die(alg, "keygen failed");
        if (OQS_KEM_encaps(w->kem, w->ct, w->ss_a, w->pk) != OQS_SUCCESS) die(alg, "encaps failed");
        if (OQS_KEM_decaps(w->kem, w->ss_b, w->ct, w->sk) != OQS_SUCCESS) die(alg, "decaps failed");
        if (memcmp(w->ss_a, w->ss_b, w->kem->length_shared_secret) != 0)
            die(alg, "KEM shared-secret mismatch — refusing to stress a broken build");
    } else {
        w->sig = OQS_SIG_new(alg);
        if (!w->sig) die(alg, "signature not enabled in this liboqs build");
        w->pk   = malloc(w->sig->length_public_key);
        w->sk   = malloc(w->sig->length_secret_key);
        w->msg  = malloc(MSGLEN);
        w->sg   = malloc(w->sig->length_signature);
        w->sg_s = malloc(w->sig->length_signature);
        w->pk_s = malloc(w->sig->length_public_key);
        w->sk_s = malloc(w->sig->length_secret_key);
        if (!w->pk||!w->sk||!w->msg||!w->sg||!w->sg_s||!w->pk_s||!w->sk_s)
            die(alg, "out of memory");
        memset(w->msg, 0xA5, MSGLEN);
        if (OQS_SIG_keypair(w->sig, w->pk, w->sk) != OQS_SUCCESS) die(alg, "keygen failed");
        w->sglen = w->sig->length_signature;
        if (OQS_SIG_sign(w->sig, w->sg, &w->sglen, w->msg, MSGLEN, w->sk) != OQS_SUCCESS)
            die(alg, "sign failed");
        if (OQS_SIG_verify(w->sig, w->msg, MSGLEN, w->sg, w->sglen, w->pk) != OQS_SUCCESS)
            die(alg, "verify failed on a valid signature — refusing to stress a broken build");
    }
}

static void worker_free(worker_t *w) {
    free(w->samples);
    if (w->ev_self) EVP_PKEY_free(w->ev_self);
    if (w->ev_peer) EVP_PKEY_free(w->ev_peer);
    if (w->ev_scratch) EVP_PKEY_free(w->ev_scratch);
    free(w->pk); free(w->sk); free(w->ct); free(w->ss_a); free(w->ss_b);
    free(w->pk_s); free(w->sk_s); free(w->msg); free(w->sg); free(w->sg_s);
    if (w->kem) OQS_KEM_free(w->kem);
    if (w->sig) OQS_SIG_free(w->sig);
}

/* ---- a measured group of workers ----------------------------------------- */
typedef struct {
    const char *role;      /* "encoder" / "decoder" / "decoder_setup" */
    const char *operation; /* "encaps" / "decaps" / "sign" / ...      */
    int threads;
    uint64_t ops, failures, busy_ns, wall_ns;
    lat_t lat;
} group_t;

/* Runs `groups` concurrently for duration_ms and fills in their results. This
 * is the only place a phase's wall clock is taken, so every group in a phase
 * shares one clock and the rates are directly comparable. */
static void run_phase(worker_t *ws, int nws, group_t *gs, int ngs,
                      const int *group_of, unsigned duration_ms) {
    pthread_attr_t attr;
    if (pthread_attr_init(&attr) != 0) die(ws[0].alg, "pthread_attr_init failed");
    if (pthread_attr_setstacksize(&attr, WORKER_STACK_BYTES) != 0)
        die(ws[0].alg, "pthread_attr_setstacksize failed");

    g_stop = 0;
    uint64_t t0 = now_ns();
    for (int i = 0; i < nws; i++)
        if (pthread_create(&ws[i].tid, &attr, worker_main, &ws[i]) != 0)
            die(ws[i].alg, "pthread_create failed");
    pthread_attr_destroy(&attr);
    sleep_ms(duration_ms);
    g_stop = 1;
    for (int i = 0; i < nws; i++) pthread_join(ws[i].tid, NULL);
    uint64_t wall = now_ns() - t0;

    for (int g = 0; g < ngs; g++) {
        gs[g].wall_ns = wall;
        gs[g].ops = gs[g].failures = gs[g].busy_ns = 0;
    }
    /* pool each group's reservoirs; every worker sampled its own stream
     * uniformly, and equal-length runs make a plain concatenation fair */
    for (int g = 0; g < ngs; g++) {
        uint64_t total = 0;
        for (int i = 0; i < nws; i++) if (group_of[i] == g) total += ws[i].nsamples;
        uint64_t *pool = malloc((total ? total : 1) * sizeof(uint64_t));
        if (!pool) die(gs[g].operation, "out of memory (pooling samples)");
        uint64_t k = 0;
        for (int i = 0; i < nws; i++) {
            if (group_of[i] != g) continue;
            gs[g].ops += ws[i].ops;
            gs[g].failures += ws[i].failures;
            gs[g].busy_ns += ws[i].busy_ns;
            memcpy(pool + k, ws[i].samples, ws[i].nsamples * sizeof(uint64_t));
            k += ws[i].nsamples;
        }
        gs[g].lat = latency_of(pool, total);
        free(pool);
    }
}

static void reset_counters(worker_t *ws, int n) {
    for (int i = 0; i < n; i++) {
        ws[i].ops = ws[i].busy_ns = ws[i].failures = 0;
        ws[i].nsamples = ws[i].seen = 0;
    }
}

/* ---- JSON ---------------------------------------------------------------- */
static double rate(const group_t *g) {
    return g->wall_ns ? (double)g->ops * 1e9 / (double)g->wall_ns : 0;
}

static void print_group(FILE *f, const group_t *g) {
    fprintf(f, "{\"role\":\"%s\",\"operation\":\"%s\",\"threads\":%d,"
               "\"ops\":%llu,\"failures\":%llu,\"wall_ns\":%llu,"
               "\"ops_per_sec\":%.2f,\"ops_per_sec_per_thread\":%.2f,"
               "\"cpu_ns_per_op\":%.2f,"
               "\"latency_ns\":{\"median\":%.2f,\"mad\":%.2f,\"p95\":%.2f,\"p99\":%.2f,"
               "\"min\":%.2f,\"max\":%.2f,\"mean\":%.2f,\"samples\":%llu}}",
            g->role, g->operation, g->threads,
            (unsigned long long)g->ops, (unsigned long long)g->failures,
            (unsigned long long)g->wall_ns,
            rate(g), g->threads ? rate(g) / g->threads : 0,
            g->ops ? (double)g->busy_ns / (double)g->ops : 0,
            g->lat.median, g->lat.mad, g->lat.p95, g->lat.p99,
            g->lat.min, g->lat.max, g->lat.mean,
            (unsigned long long)g->lat.n);
}

static void usage(void) {
    fprintf(stderr,
      "usage: stress_roles --kind kem|sig --alg NAME [--duration-ms N] [--threads N]\n"
      "                    [--max-samples N]\n"
      "  --duration-ms  per phase-leg, default 2000\n"
      "  --threads      saturation width, default = online CPUs\n");
}

int main(int argc, char **argv) {
    const char *kind = NULL, *alg = NULL;
    unsigned duration_ms = 2000, cap = DEFAULT_SAMPLE_CAP;
    int threads = 0;

    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--kind") && i + 1 < argc) kind = argv[++i];
        else if (!strcmp(argv[i], "--alg") && i + 1 < argc) alg = argv[++i];
        else if (!strcmp(argv[i], "--duration-ms") && i + 1 < argc) duration_ms = (unsigned)strtoul(argv[++i], NULL, 10);
        else if (!strcmp(argv[i], "--threads") && i + 1 < argc) threads = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--max-samples") && i + 1 < argc) cap = (unsigned)strtoul(argv[++i], NULL, 10);
        else if (!strcmp(argv[i], "-h") || !strcmp(argv[i], "--help")) { usage(); return 0; }
        else { fprintf(stderr, "unknown arg: %s\n", argv[i]); usage(); return 2; }
    }
    if (!kind || !alg || (strcmp(kind, "kem") && strcmp(kind, "sig"))) { usage(); return 2; }
    if (threads <= 0) threads = online_cpus();
    if (threads > MAX_THREADS) threads = MAX_THREADS;
    if (cap == 0) cap = 1;

    const int is_kem = !strcmp(kind, "kem");
    /* The two classical baselines are named, not detected: they are the whole
     * point of comparison and must not be silently skipped if liboqs happens
     * to expose an algorithm by the same name. */
    const int is_x25519 = !strcmp(alg, "X25519");
    const int is_ed     = !strcmp(alg, "Ed25519");
    const int classical = is_x25519 || is_ed;

    op_kind enc_op, dec_op, setup_op;
    const char *enc_name, *dec_name;
    if (is_x25519) {
        /* Both peers run the identical operation, so the roles are the same
         * op measured twice — the symmetry is structural, and the measured
         * ratio near 1.0 is the harness checking itself. */
        enc_op = dec_op = OP_X25519_DERIVE; setup_op = OP_X25519_KEYGEN;
        enc_name = dec_name = "derive";
    } else if (is_ed) {
        enc_op = OP_ED_SIGN; dec_op = OP_ED_VERIFY; setup_op = OP_ED_KEYGEN;
        enc_name = "sign"; dec_name = "verify";
    } else if (is_kem) {
        enc_op = OP_KEM_ENCAPS; dec_op = OP_KEM_DECAPS; setup_op = OP_KEM_KEYGEN;
        enc_name = "encaps"; dec_name = "decaps";
    } else {
        enc_op = OP_SIG_SIGN; dec_op = OP_SIG_VERIFY; setup_op = OP_SIG_KEYGEN;
        enc_name = "sign"; dec_name = "verify";
    }

    /* An unavailable algorithm is a recorded absence, not a crash: the driver
     * sweeps a candidate list and a build without (say) Falcon must still
     * produce a complete, self-describing result for everything else. */
    if (classical) {
        /* nothing to probe: OpenSSL EVP always has X25519 and Ed25519 */
    } else if (is_kem) {
        OQS_KEM *probe = OQS_KEM_new(alg);
        if (!probe) {
            printf("{\"alg\":\"%s\",\"kind\":\"kem\",\"implementation\":\"liboqs\","
                   "\"enabled\":false,\"reason\":\"not enabled in this liboqs build\"}\n", alg);
            return 0;
        }
        OQS_KEM_free(probe);
    } else {
        OQS_SIG *probe = OQS_SIG_new(alg);
        if (!probe) {
            printf("{\"alg\":\"%s\",\"kind\":\"sig\",\"implementation\":\"liboqs\","
                   "\"enabled\":false,\"reason\":\"not enabled in this liboqs build\"}\n", alg);
            return 0;
        }
        OQS_SIG_free(probe);
    }

    /* One worker pool, reused across phases: allocating T encoders and T
     * decoders once means no phase pays another phase's allocation or
     * first-touch page-fault cost. */
    worker_t *enc = calloc(threads, sizeof(worker_t));
    worker_t *dec = calloc(threads, sizeof(worker_t));
    worker_t setup;
    if (!enc || !dec) die(alg, "out of memory (worker pools)");
    for (int i = 0; i < threads; i++) {
        worker_init(&enc[i], kind, alg, enc_op, cap, 0x9E3779B97F4A7C15ull ^ (uint64_t)(i + 1));
        worker_init(&dec[i], kind, alg, dec_op, cap, 0xD1B54A32D192ED03ull ^ (uint64_t)(i + 1));
    }
    worker_init(&setup, kind, alg, setup_op, cap, 0xA24BAED4963EE407ull);

    size_t pk_len, sk_len, wire_len;
    int nist_level;
    if (is_x25519) {
        pk_len = sk_len = wire_len = 32;   /* the share each peer puts on the wire */
        nist_level = 1;
    } else if (is_ed) {
        pk_len = 32; sk_len = 32; wire_len = 64;
        nist_level = 1;
    } else if (is_kem) {
        pk_len = enc[0].kem->length_public_key;
        sk_len = enc[0].kem->length_secret_key;
        wire_len = enc[0].kem->length_ciphertext;
        nist_level = enc[0].kem->claimed_nist_level;
    } else {
        pk_len = enc[0].sig->length_public_key;
        sk_len = enc[0].sig->length_secret_key;
        wire_len = enc[0].sig->length_signature;
        nist_level = enc[0].sig->claimed_nist_level;
    }

    int *gmap = calloc(2 * threads, sizeof(int));
    if (!gmap) die(alg, "out of memory (group map)");

    /* ---- phase: isolated (1 thread, one role at a time) ------------------ */
    group_t iso_enc = { "encoder", enc_name, 1, 0,0,0,0, {0} };
    group_t iso_dec = { "decoder", dec_name, 1, 0,0,0,0, {0} };
    /* For a KEM the keypair is the decoder's setup cost, and for an ephemeral
     * exchange it is paid per session. A signature keypair is a long-lived
     * identity belonging to the signer, so calling it "decoder_setup" there
     * would misattribute it — it is reported, but under its own name. */
    group_t iso_setup = { is_kem ? "decoder_setup" : "signer_setup",
                          "keygen", 1, 0,0,0,0, {0} };
    gmap[0] = 0;
    reset_counters(enc, 1);   run_phase(enc, 1, &iso_enc, 1, gmap, duration_ms);
    reset_counters(dec, 1);   run_phase(dec, 1, &iso_dec, 1, gmap, duration_ms);
    reset_counters(&setup, 1);run_phase(&setup, 1, &iso_setup, 1, gmap, duration_ms);

    /* ---- phase: saturated (T threads, one role at a time) ---------------- */
    group_t sat_enc = { "encoder", enc_name, threads, 0,0,0,0, {0} };
    group_t sat_dec = { "decoder", dec_name, threads, 0,0,0,0, {0} };
    for (int i = 0; i < threads; i++) gmap[i] = 0;
    reset_counters(enc, threads); run_phase(enc, threads, &sat_enc, 1, gmap, duration_ms);
    reset_counters(dec, threads); run_phase(dec, threads, &sat_dec, 1, gmap, duration_ms);

    /* ---- phase: contended (1 encoder vs T decoders, together) ------------ */
    /* The adversarial shape: one sender, a receiver with the whole machine.
     * Both groups share one wall clock, so the rates are directly comparable
     * and the question "can one sender outrun T receivers?" is answered by
     * numbers taken at the same instant under the same thermal conditions. */
    int nmix = 1 + threads;
    worker_t *mix = calloc(nmix, sizeof(worker_t));
    if (!mix) die(alg, "out of memory (mixed pool)");
    mix[0] = enc[0];
    for (int i = 0; i < threads; i++) mix[1 + i] = dec[i];
    gmap[0] = 0;
    for (int i = 0; i < threads; i++) gmap[1 + i] = 1;
    group_t con[2] = {
        { "encoder", enc_name, 1, 0,0,0,0, {0} },
        { "decoder", dec_name, threads, 0,0,0,0, {0} },
    };
    reset_counters(mix, nmix);
    run_phase(mix, nmix, con, 2, gmap, duration_ms);

    /* ---- derived asymmetry ---------------------------------------------- */
    /* Ratios, not absolute rates, are what survives leaving this machine. */
    double iso_ratio = iso_enc.lat.median > 0 ? iso_dec.lat.median / iso_enc.lat.median : 0;

    /* Per-session: who pays when the keypair is ephemeral and generated for
     * this exchange alone (the TLS shape)?
     *   KEM   only the decoder generates a keypair — it is the side that
     *         publishes a public key for the encoder to encapsulate against.
     *   DH    BOTH peers generate an ephemeral share, so keygen lands on both
     *         sides and a symmetric exchange stays symmetric. Adding it to one
     *         side only would have reported X25519 as 1.87 — an asymmetry that
     *         does not exist.
     *   SIG   signature keys are long-lived identities, not per-session, so
     *         per-session is the same as per-message. */
    double sess_enc = iso_enc.lat.median + (is_x25519 ? iso_setup.lat.median : 0);
    double sess_dec = iso_dec.lat.median + (is_kem ? iso_setup.lat.median : 0);
    double iso_ratio_session = sess_enc > 0 ? sess_dec / sess_enc : 0;

    double sat_ratio = rate(&sat_dec) > 0 ? rate(&sat_enc) / rate(&sat_dec) : 0;
    /* How many decoder cores one saturated encoder core keeps busy: the
     * denial-of-service multiplier, in units of CPU cores. Taken from the
     * saturated per-thread rates rather than isolated latency, so it reflects
     * what the roles actually sustain when every core is working. */
    double enc_pt = sat_enc.threads ? rate(&sat_enc) / sat_enc.threads : 0;
    double dec_pt = sat_dec.threads ? rate(&sat_dec) / sat_dec.threads : 0;
    double dec_per_enc = dec_pt > 0 ? enc_pt / dec_pt : 0;
    /* The contended phase runs 1 encoder against T decoders, so the raw rate
     * ratio mostly reports T. What is wanted is per-decoder-thread: how many
     * decoder cores one encoder thread keeps busy while they actually compete
     * for the machine. That is the denial-of-service multiplier, measured
     * rather than derived. NB the single encoder is oversubscribed alongside T
     * decoders on T cores, so this is a conservative (low) estimate. */
    double con_dec_pt = con[1].threads ? rate(&con[1]) / con[1].threads : 0;
    double con_cores_per_enc = con_dec_pt > 0 ? rate(&con[0]) / con_dec_pt : 0;

    printf("{\"alg\":\"%s\",\"kind\":\"%s\",\"implementation\":\"%s\","
           "\"classical\":%s,\"enabled\":true,\"claimed_nist_level\":%d,",
           alg, kind, classical ? "openssl" : "liboqs",
           classical ? "true" : "false", nist_level);
    printf("\"roles\":{\"encoder\":\"%s\",\"decoder\":\"%s\"},", enc_name, dec_name);
    printf("\"sizes\":{\"public_key\":%zu,\"secret_key\":%zu,\"encoder_emits\":%zu},",
           pk_len, sk_len, wire_len);
    printf("\"config\":{\"duration_ms\":%u,\"threads\":%d,\"max_samples_per_worker\":%u},",
           duration_ms, threads, cap);

    printf("\"phases\":{");
    printf("\"isolated\":{\"encoder\":");    print_group(stdout, &iso_enc);
    printf(",\"decoder\":");                 print_group(stdout, &iso_dec);
    printf(",\"decoder_setup\":");           print_group(stdout, &iso_setup);
    printf("},\"saturated\":{\"encoder\":"); print_group(stdout, &sat_enc);
    printf(",\"decoder\":");                 print_group(stdout, &sat_dec);
    printf("},\"contended\":{\"encoder\":"); print_group(stdout, &con[0]);
    printf(",\"decoder\":");                 print_group(stdout, &con[1]);
    printf("}},");

    printf("\"asymmetry\":{"
           "\"latency_ratio_decoder_over_encoder\":%.4f,"
           "\"latency_ratio_per_session\":%.4f,"
           "\"throughput_ratio_encoder_over_decoder\":%.4f,"
           "\"decoder_cores_per_encoder_core\":%.4f,"
           "\"contended_decoder_cores_per_encoder_core\":%.4f,"
           "\"symmetric_by_construction\":%s,"
           "\"cheaper_side\":\"%s\"}",
           iso_ratio, iso_ratio_session, sat_ratio, dec_per_enc, con_cores_per_enc,
           is_x25519 ? "true" : "false",
           iso_ratio > 1.05 ? "encoder"
                            : (iso_ratio < 0.95 ? "decoder" : "neither"));
    printf("}\n");

    free(gmap); free(mix);
    for (int i = 0; i < threads; i++) { worker_free(&enc[i]); worker_free(&dec[i]); }
    worker_free(&setup);
    free(enc); free(dec);
    return 0;
}
