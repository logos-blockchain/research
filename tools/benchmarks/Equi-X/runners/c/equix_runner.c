/* Equi-X C benchmark runner.
 *
 * Reads one job-spec JSON object on stdin, runs the requested operation against
 * the reference C implementation (tevador/equix + hashx), and writes one result
 * JSON object on stdout. All diagnostics go to stderr. See adapters/README.md
 * for the protocol.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/utsname.h>
#if defined(__APPLE__)
#include <sys/sysctl.h>
#define OS_STR "macos"
#else
#define OS_STR "linux"
#endif

/* The bundled HashX JITs via mmap(RW)+mprotect(RX) with no MAP_JIT, which the
 * Apple Silicon kernel (hard W^X) rejects and would crash on execution. So we
 * treat the compiler as unsupported there and fall back to the interpreter. */
#if defined(__APPLE__) && defined(__aarch64__)
#define JIT_SUPPORTED 0
#else
#define JIT_SUPPORTED 1
#endif

#include <equix.h>
#include <hashx.h>

#include "effort.h"
#include "json_min.h"
#include "sha256.h"
#include "timing.h"

#ifndef EQUIX_C_COMMIT
#define EQUIX_C_COMMIT "unknown"
#endif
#ifndef EQUIX_C_VERSION
#define EQUIX_C_VERSION "1.0.0"
#endif

#if defined(__clang__)
#define COMPILER_STR "clang-" __clang_version__
#elif defined(__GNUC__)
#define COMPILER_STR "gcc-" __VERSION__
#else
#define COMPILER_STR "unknown"
#endif

#if defined(__x86_64__) || defined(_M_X64)
#define ARCH_STR "x86_64"
#elif defined(__aarch64__)
#define ARCH_STR "aarch64"
#elif defined(__i386__)
#define ARCH_STR "x86"
#elif defined(__arm__)
#define ARCH_STR "arm"
#else
#define ARCH_STR "unknown"
#endif

#define MAX_CHALLENGE 256

/* CPU model string from /proc/cpuinfo, JSON-escaped, cached. Tries fields in
 * priority order so it works across architectures: "model name" (x86),
 * "Model" (Raspberry Pi board), "Hardware" (older ARM), "cpu model" (others).
 * Returns "unknown" when none are present. */
static const char *cpu_model(void) {
    static char model[256];
    if (model[0])
        return model;
    strcpy(model, "unknown");
#if defined(__APPLE__)
    /* macOS has no /proc; the CPU brand comes from sysctl (works on both Intel
     * and Apple Silicon, e.g. "Apple M2"). */
    size_t sz = sizeof model;
    if (sysctlbyname("machdep.cpu.brand_string", model, &sz, NULL, 0) != 0 || !model[0])
        strcpy(model, "unknown");
    return model;
#else
    FILE *f = fopen("/proc/cpuinfo", "r");
    if (!f)
        return model;
    /* Large enough that ARM's trailing "Model"/"Hardware" lines are captured
     * even on many-core machines. */
    static char buf[131072];
    size_t n = fread(buf, 1, sizeof buf - 1, f);
    buf[n] = '\0';
    fclose(f);

    static const char *fields[] = {"model name", "Model", "Hardware", "cpu model"};
    for (size_t fi = 0; fi < sizeof fields / sizeof fields[0]; fi++) {
        size_t fl = strlen(fields[fi]);
        for (const char *p = buf; p; p = strchr(p, '\n') ? strchr(p, '\n') + 1 : NULL) {
            if (strncmp(p, fields[fi], fl) != 0)
                continue;
            /* field must be followed by whitespace/':' (avoid partial matches) */
            char after = p[fl];
            if (after != ' ' && after != '\t' && after != ':')
                continue;
            const char *c = strchr(p, ':');
            const char *eol = strchr(p, '\n');
            if (!c || (eol && c > eol))
                continue;
            c++;
            while (*c == ' ' || *c == '\t')
                c++;
            size_t k = 0;
            for (size_t i = 0; c[i] && c[i] != '\n' && c[i] != '\r' && k + 2 < sizeof model; i++) {
                if (c[i] == '"' || c[i] == '\\')
                    model[k++] = '\\';
                model[k++] = c[i];
            }
            while (k > 0 && model[k - 1] == ' ')
                k--;
            model[k] = '\0';
            if (k > 0)
                return model;
        }
    }
    return model;
#endif /* !__APPLE__ */
}

/* OS kernel release (uname -r), e.g. "6.18.5" (Linux) or "23.5.0" (macOS/Darwin).
 * Cached; "unknown" on failure. uname() is portable across Linux and macOS. */
static const char *os_version(void) {
    static char v[128];
    if (v[0])
        return v;
    strcpy(v, "unknown");
    struct utsname u;
    if (uname(&u) == 0)
        snprintf(v, sizeof v, "%s", u.release);
    return v;
}

/* ------------------------------------------------------------------ helpers */

static char *read_all_stdin(void) {
    size_t cap = 4096, len = 0;
    char *buf = malloc(cap);
    if (!buf)
        return NULL;
    size_t n;
    while ((n = fread(buf + len, 1, cap - len - 1, stdin)) > 0) {
        len += n;
        if (len + 1 >= cap) {
            cap *= 2;
            char *nb = realloc(buf, cap);
            if (!nb) {
                free(buf);
                return NULL;
            }
            buf = nb;
        }
    }
    buf[len] = '\0';
    return buf;
}

/* Decode a hex string into `out` (capacity outcap). Returns byte length, or -1. */
static int hex_decode(const char *hex, uint8_t *out, size_t outcap) {
    size_t hl = strlen(hex);
    if (hl % 2 != 0)
        return -1;
    size_t bl = hl / 2;
    if (bl > outcap)
        return -1;
    for (size_t i = 0; i < bl; i++) {
        char c0 = hex[2 * i], c1 = hex[2 * i + 1];
        int hi = (c0 >= '0' && c0 <= '9')   ? c0 - '0'
                 : (c0 >= 'a' && c0 <= 'f') ? c0 - 'a' + 10
                 : (c0 >= 'A' && c0 <= 'F') ? c0 - 'A' + 10
                                            : -1;
        int lo = (c1 >= '0' && c1 <= '9')   ? c1 - '0'
                 : (c1 >= 'a' && c1 <= 'f') ? c1 - 'a' + 10
                 : (c1 >= 'A' && c1 <= 'F') ? c1 - 'A' + 10
                                            : -1;
        if (hi < 0 || lo < 0)
            return -1;
        out[i] = (uint8_t)((hi << 4) | lo);
    }
    return (int)bl;
}

/* One measured repetition. */
typedef struct {
    uint64_t wall_ns;
    int solutions;
    uint64_t compile_ns;
    uint64_t attempts;
    uint32_t achieved_effort;
    const char *verify_result; /* NULL unless a verify op */
} run_t;

static const char *verify_result_str(equix_result r) {
    switch (r) {
    case EQUIX_OK: return "OK";
    case EQUIX_CHALLENGE: return "CHALLENGE";
    case EQUIX_ORDER: return "ORDER";
    case EQUIX_PARTIAL_SUM: return "PARTIAL_SUM";
    case EQUIX_FINAL_SUM: return "FINAL_SUM";
    default: return "UNKNOWN";
    }
}

/* Emit a failure result JSON and exit. */
static void fail(const char *op, const char *runtime_req, const char *msg) {
    printf("{\"schema_version\":1,\"ok\":false,"
           "\"impl\":{\"name\":\"equix-c\",\"version\":\"%s\",\"commit\":\"%s\","
           "\"runtime_effective\":null},"
           "\"operation\":\"%s\",\"runtime_requested\":\"%s\","
           "\"runtime_effective\":null,"
           "\"env\":{\"os\":\"%s\",\"compiler\":\"%s\",\"cpu\":\"%s\","
           "\"arch\":\"%s\",\"device\":\"cpu\",\"os_version\":\"%s\"},"
           "\"runs\":[],\"peak_rss_kb\":%ld,\"error\":\"%s\"}\n",
           EQUIX_C_VERSION, EQUIX_C_COMMIT, op ? op : "", runtime_req ? runtime_req : "",
           OS_STR, COMPILER_STR, cpu_model(), ARCH_STR, os_version(), peak_rss_kb(), msg);
    exit(1);
}

/* solutions_hex_json: pre-formatted JSON array (e.g. ["aabb..",".."]) or NULL. */
static void emit_ex(const char *op, const char *runtime_req,
                    const char *runtime_eff, const run_t *runs, size_t nruns,
                    const char *solutions_hex_json,
                    const char *winning_nonce_hex);

static void emit(const char *op, const char *runtime_req,
                 const char *runtime_eff, const run_t *runs, size_t nruns,
                 const char *solutions_hex_json) {
    emit_ex(op, runtime_req, runtime_eff, runs, nruns, solutions_hex_json, NULL);
}

/* Like emit, plus an optional winning_nonce_hex field (effort op: the wire
 * bytes of the winning token's nonce, so the harness can measure sizes). */
static void emit_ex(const char *op, const char *runtime_req,
                    const char *runtime_eff, const run_t *runs, size_t nruns,
                    const char *solutions_hex_json,
                    const char *winning_nonce_hex) {
    printf("{\"schema_version\":1,\"ok\":true,"
           "\"impl\":{\"name\":\"equix-c\",\"version\":\"%s\",\"commit\":\"%s\","
           "\"runtime_effective\":\"%s\"},"
           "\"operation\":\"%s\",\"runtime_requested\":\"%s\","
           "\"runtime_effective\":\"%s\","
           "\"env\":{\"os\":\"%s\",\"compiler\":\"%s\",\"cpu\":\"%s\","
           "\"arch\":\"%s\",\"device\":\"cpu\",\"os_version\":\"%s\"},"
           "\"runs\":[",
           EQUIX_C_VERSION, EQUIX_C_COMMIT, runtime_eff, op, runtime_req,
           runtime_eff, OS_STR, COMPILER_STR, cpu_model(), ARCH_STR, os_version());
    for (size_t i = 0; i < nruns; i++) {
        const run_t *r = &runs[i];
        printf("%s{\"index\":%zu,\"wall_ns\":%llu,\"solutions\":%d,"
               "\"compile_ns\":%llu,\"attempts\":%llu,\"achieved_effort\":%u,"
               "\"verify_result\":",
               i ? "," : "", i, (unsigned long long)r->wall_ns, r->solutions,
               (unsigned long long)r->compile_ns,
               (unsigned long long)r->attempts, r->achieved_effort);
        if (r->verify_result)
            printf("\"%s\"}", r->verify_result);
        else
            printf("null}");
    }
    printf("],\"solutions_hex\":%s,",
           solutions_hex_json ? solutions_hex_json : "null");
    if (winning_nonce_hex)
        printf("\"winning_nonce_hex\":\"%s\",", winning_nonce_hex);
    printf("\"peak_rss_kb\":%ld,\"error\":null}\n", peak_rss_kb());
}

/* Format a solution as 32 lowercase hex chars (16 bytes little-endian). */
static void solution_to_hex(const equix_solution *sol, char out[33]) {
    static const char hx[] = "0123456789abcdef";
    uint8_t sb[16];
    effort_solution_bytes(sol, sb);
    for (int i = 0; i < 16; i++) {
        out[2 * i] = hx[sb[i] >> 4];
        out[2 * i + 1] = hx[sb[i] & 0xf];
    }
    out[32] = '\0';
}

/* ------------------------------------------------------- equix ctx creation */

/* Allocate an equix context honoring the requested runtime, reporting the
 * effective runtime. base_flag is EQUIX_CTX_SOLVE or EQUIX_CTX_VERIFY.
 * Returns NULL and sets *err on hard failure. */
static equix_ctx *alloc_ctx(int base_flag, const char *runtime,
                            const char **eff, const char **err) {
    equix_ctx *ctx;
    if (strcmp(runtime, "interpret") == 0) {
        ctx = equix_alloc((equix_ctx_flags)base_flag);
        *eff = "interpreted";
    } else if (strcmp(runtime, "must-compile") == 0) {
        if (!JIT_SUPPORTED) {
            *err = "must-compile requested but JIT compiler not supported on this platform";
            return NULL;
        }
        ctx = equix_alloc((equix_ctx_flags)(base_flag | EQUIX_CTX_COMPILE));
        if (ctx == EQUIX_NOTSUPP) {
            *err = "must-compile requested but JIT compiler not supported";
            return NULL;
        }
        *eff = "compiled";
    } else { /* try-compile (default) */
        ctx = JIT_SUPPORTED
                  ? equix_alloc((equix_ctx_flags)(base_flag | EQUIX_CTX_COMPILE))
                  : EQUIX_NOTSUPP;
        if (ctx == EQUIX_NOTSUPP) {
            ctx = equix_alloc((equix_ctx_flags)base_flag);
            *eff = "interpreted (fallback)";
        } else {
            *eff = "compiled";
        }
    }
    if (ctx == NULL || ctx == EQUIX_NOTSUPP) {
        *err = "equix_alloc failed";
        return NULL;
    }
    return ctx;
}

/* --------------------------------------------------------------- operations */

/* Read either a fixed challenge (challenge_hex) or a seed (challenge_seed_hex).
 * In seed mode each rep hashes the current challenge to get the next (a SHA-256
 * chain), so measurements span many challenges; that derivation is done OUTSIDE
 * every timed region. Returns 1 for seed mode, 0 for fixed, and fills the first
 * challenge into `chal`/`clen`. Fails the op if neither field is present. */
static int read_challenge_or_seed(const char *json, const char *op,
                                  const char *runtime, uint8_t chal[MAX_CHALLENGE],
                                  int *clen) {
    char hex[2 * MAX_CHALLENGE + 1] = {0};
    if (jm_get_str(json, "challenge_seed_hex", hex, sizeof hex)) {
        uint8_t seed[MAX_CHALLENGE];
        int slen = hex_decode(hex, seed, sizeof seed);
        if (slen < 0)
            fail(op, runtime, "invalid challenge_seed_hex");
        sha256(seed, (size_t)slen, chal); /* challenge for iteration 0 */
        *clen = 32;
        return 1;
    }
    if (!jm_get_str(json, "challenge_hex", hex, sizeof hex))
        fail(op, runtime, "requires challenge_hex or challenge_seed_hex");
    *clen = hex_decode(hex, chal, MAX_CHALLENGE);
    if (*clen < 0)
        fail(op, runtime, "invalid challenge_hex");
    return 0;
}

static void op_solve(const char *json, const char *runtime, uint64_t reps,
                     uint64_t warmup) {
    uint8_t chal[MAX_CHALLENGE];
    int clen;
    int seeded = read_challenge_or_seed(json, "solve", runtime, chal, &clen);

    const char *eff = "?", *err = NULL;
    equix_ctx *ctx = alloc_ctx(EQUIX_CTX_SOLVE, runtime, &eff, &err);
    if (!ctx)
        fail("solve", runtime, err);

    equix_solution sols[EQUIX_MAX_SOLS];
    for (uint64_t w = 0; w < warmup; w++) {
        (void)equix_solve(ctx, chal, clen, sols);
        if (seeded)
            sha256(chal, 32, chal); /* advance the chain (untimed) */
    }

    run_t *runs = calloc(reps ? reps : 1, sizeof(run_t));
    int last_n = 0;
    for (uint64_t i = 0; i < reps; i++) {
        uint64_t t0 = now_ns();
        int n = equix_solve(ctx, chal, clen, sols);
        uint64_t t1 = now_ns();
        if (seeded)
            sha256(chal, 32, chal); /* derive next challenge AFTER stopping the timer */
        runs[i].wall_ns = t1 - t0;
        runs[i].solutions = n;
        last_n = n;
    }
    /* Publish the solutions found in the final rep for cross-implementation
     * verification. Each solution = 32 hex chars; array fits comfortably. */
    char shex[EQUIX_MAX_SOLS * 40 + 4];
    size_t off = 0;
    off += (size_t)snprintf(shex + off, sizeof shex - off, "[");
    for (int s = 0; s < last_n; s++) {
        char h[33];
        solution_to_hex(&sols[s], h);
        off += (size_t)snprintf(shex + off, sizeof shex - off, "%s\"%s\"",
                                s ? "," : "", h);
    }
    snprintf(shex + off, sizeof shex - off, "]");
    emit("solve", runtime, eff, runs, reps, shex);
    free(runs);
    equix_free(ctx);
}

/* Seed mode, two-phase so the timed region contains ONLY equix_verify:
 *   phase 1 (untimed): walk the SHA-256 chain, self-solving each challenge to
 *     collect (challenge, solution) pairs — the setup solve, which touches the
 *     ~1.8 MB solver table, is kept out of timing so it cannot pollute the cache
 *     the tiny verify reads from;
 *   phase 2 (timed): verify the collected pairs back-to-back.
 * Uses a SOLVE context (it can verify too). Solution-less challenges are skipped. */
static void op_verify_seeded(const char *json, const char *runtime, uint64_t reps,
                             uint64_t warmup) {
    uint8_t chal[MAX_CHALLENGE];
    int clen;
    (void)read_challenge_or_seed(json, "verify", runtime, chal, &clen);

    const char *eff = "?", *err = NULL;
    equix_ctx *ctx = alloc_ctx(EQUIX_CTX_SOLVE, runtime, &eff, &err);
    if (!ctx)
        fail("verify", runtime, err);

    uint64_t want = warmup + reps;
    uint8_t *chals = malloc(want * 32);
    equix_solution *toks = malloc(want * sizeof(equix_solution));
    equix_solution sols[EQUIX_MAX_SOLS];

    /* Phase 1 — collect `want` valid (challenge, solution) pairs, untimed.
     * Cap draws so solution-less challenges cannot loop forever. */
    uint64_t got = 0, guard = 0, guard_max = want * 8 + 128;
    while (got < want && guard++ < guard_max) {
        if (equix_solve(ctx, chal, clen, sols) > 0) {
            memcpy(chals + got * 32, chal, 32);
            toks[got] = sols[0];
            got++;
        }
        sha256(chal, 32, chal); /* advance the chain (untimed) */
    }

    uint64_t warm = warmup < got ? warmup : got;
    uint64_t timed = got - warm;
    for (uint64_t w = 0; w < warm; w++)
        (void)equix_verify(ctx, chals + w * 32, 32, &toks[w]);

    run_t *runs = calloc(timed ? timed : 1, sizeof(run_t));
    for (uint64_t i = 0; i < timed; i++) {
        uint64_t idx = warm + i;
        uint64_t t0 = now_ns();
        equix_result r = equix_verify(ctx, chals + idx * 32, 32, &toks[idx]);
        uint64_t t1 = now_ns();
        runs[i].wall_ns = t1 - t0;
        runs[i].solutions = (r == EQUIX_OK) ? 1 : 0;
        runs[i].verify_result = verify_result_str(r);
    }
    emit("verify", runtime, eff, runs, timed, NULL);
    free(runs);
    free(chals);
    free(toks);
    equix_free(ctx);
}

static void op_verify(const char *json, const char *runtime, uint64_t reps,
                      uint64_t warmup) {
    char seed_probe[4] = {0};
    if (jm_get_str(json, "challenge_seed_hex", seed_probe, sizeof seed_probe)) {
        op_verify_seeded(json, runtime, reps, warmup);
        return;
    }

    char chal_hex[2 * MAX_CHALLENGE + 1] = {0};
    char sol_hex[64] = {0};
    if (!jm_get_str(json, "challenge_hex", chal_hex, sizeof chal_hex))
        fail("verify", runtime, "verify requires challenge_hex");
    if (!jm_get_str(json, "solution_hex", sol_hex, sizeof sol_hex))
        fail("verify", runtime, "verify requires solution_hex");
    uint8_t chal[MAX_CHALLENGE];
    int clen = hex_decode(chal_hex, chal, sizeof chal);
    if (clen < 0)
        fail("verify", runtime, "invalid challenge_hex");
    uint8_t sb[16];
    if (hex_decode(sol_hex, sb, sizeof sb) != 16)
        fail("verify", runtime, "solution_hex must be 16 bytes");
    equix_solution sol;
    for (int i = 0; i < EQUIX_NUM_IDX; i++)
        sol.idx[i] = (equix_idx)(sb[2 * i] | ((uint16_t)sb[2 * i + 1] << 8));

    const char *eff = "?", *err = NULL;
    equix_ctx *ctx = alloc_ctx(EQUIX_CTX_VERIFY, runtime, &eff, &err);
    if (!ctx)
        fail("verify", runtime, err);

    for (uint64_t w = 0; w < warmup; w++)
        (void)equix_verify(ctx, chal, clen, &sol);

    run_t *runs = calloc(reps ? reps : 1, sizeof(run_t));
    for (uint64_t i = 0; i < reps; i++) {
        uint64_t t0 = now_ns();
        equix_result r = equix_verify(ctx, chal, clen, &sol);
        uint64_t t1 = now_ns();
        runs[i].wall_ns = t1 - t0;
        runs[i].solutions = (r == EQUIX_OK) ? 1 : 0;
        runs[i].verify_result = verify_result_str(r);
    }
    emit("verify", runtime, eff, runs, reps, NULL);
    free(runs);
    equix_free(ctx);
}

/* Build challenge = base || little-endian(nonce, nonce_bytes) into buf. */
static int build_nonce_challenge(const uint8_t *base, int base_len,
                                 uint64_t nonce, int nonce_bytes, uint8_t *buf) {
    memcpy(buf, base, base_len);
    for (int i = 0; i < nonce_bytes; i++)
        buf[base_len + i] = (uint8_t)((nonce >> (8 * i)) & 0xff);
    return base_len + nonce_bytes;
}

static void op_effort(const char *json, const char *runtime, uint64_t reps,
                      uint64_t warmup) {
    char base_hex[2 * MAX_CHALLENGE + 1] = {0};
    if (!jm_get_str(json, "challenge_base_hex", base_hex, sizeof base_hex))
        fail("effort", runtime, "effort requires challenge_base_hex");
    uint8_t base[MAX_CHALLENGE];
    int base_len = hex_decode(base_hex, base, sizeof base);
    if (base_len < 0)
        fail("effort", runtime, "invalid challenge_base_hex");

    uint64_t nonce_bytes = 8, nonce_start = 0, target = 1000, max_attempts = 5000000;
    jm_get_u64(json, "nonce_bytes", &nonce_bytes);
    jm_get_u64(json, "nonce_start", &nonce_start);
    jm_get_u64(json, "target_effort", &target);
    jm_get_u64(json, "max_attempts", &max_attempts);
    if (nonce_bytes > 8 || (size_t)base_len + nonce_bytes > MAX_CHALLENGE)
        fail("effort", runtime, "nonce_bytes out of range");

    const char *eff = "?", *err = NULL;
    equix_ctx *ctx = alloc_ctx(EQUIX_CTX_SOLVE, runtime, &eff, &err);
    if (!ctx)
        fail("effort", runtime, err);

    equix_solution sols[EQUIX_MAX_SOLS];
    uint8_t chal[MAX_CHALLENGE];

    /* One search = one repetition; warmups run a full search but are discarded. */
    for (uint64_t w = 0; w < warmup; w++) {
        uint64_t nonce = nonce_start;
        for (uint64_t a = 0; a < max_attempts; a++, nonce++) {
            int clen = build_nonce_challenge(base, base_len, nonce, nonce_bytes, chal);
            int n = equix_solve(ctx, chal, clen, sols);
            int done = 0;
            for (int s = 0; s < n; s++)
                if (effort_of(chal, clen, &sols[s]) >= target) { done = 1; break; }
            if (done) break;
        }
    }

    run_t *runs = calloc(reps ? reps : 1, sizeof(run_t));
    /* The winning token's wire bytes (nonce LE + 16-byte solution): reported so
     * the harness can measure message sizes vs difficulty. */
    equix_solution win_sol;
    uint8_t win_nonce[8];
    int have_token = 0;
    for (uint64_t i = 0; i < reps; i++) {
        uint64_t nonce = nonce_start;
        uint64_t attempts = 0;
        uint32_t best = 0;
        uint64_t t0 = now_ns();
        for (uint64_t a = 0; a < max_attempts; a++, nonce++) {
            int clen = build_nonce_challenge(base, base_len, nonce, nonce_bytes, chal);
            int n = equix_solve(ctx, chal, clen, sols);
            attempts++;
            int done = 0;
            for (int s = 0; s < n; s++) {
                uint32_t e = effort_of(chal, clen, &sols[s]);
                if (e > best) best = e;
                if (e >= target) {
                    if (!done) {
                        win_sol = sols[s];
                        memcpy(win_nonce, chal + base_len, nonce_bytes);
                        have_token = 1;
                    }
                    done = 1;
                }
            }
            if (done) break;
        }
        uint64_t t1 = now_ns();
        runs[i].wall_ns = t1 - t0;
        runs[i].attempts = attempts;
        runs[i].achieved_effort = best;
        runs[i].solutions = (best >= target) ? 1 : 0;
    }
    if (have_token) {
        static const char hx[] = "0123456789abcdef";
        char shex[33], sjson[40], nhex[17];
        solution_to_hex(&win_sol, shex);
        snprintf(sjson, sizeof sjson, "[\"%s\"]", shex);
        for (uint64_t b = 0; b < nonce_bytes; b++) {
            nhex[2 * b] = hx[win_nonce[b] >> 4];
            nhex[2 * b + 1] = hx[win_nonce[b] & 0xf];
        }
        nhex[2 * nonce_bytes] = '\0';
        emit_ex("effort", runtime, eff, runs, reps, sjson, nhex);
    } else {
        emit("effort", runtime, eff, runs, reps, NULL);
    }
    free(runs);
    equix_free(ctx);
}

/* Isolate program generation+compile (hashx_make) from execution (hashx_exec)
 * using the hashx API directly -- libequix's public API cannot separate them.
 * Each rep uses a distinct seed (base || LE(nonce_start+i)) so we sample the
 * compile-time distribution across different generated programs. */
static void op_hashx_compile(const char *json, const char *runtime,
                             uint64_t reps, uint64_t warmup) {
    char base_hex[2 * MAX_CHALLENGE + 1] = {0};
    if (!jm_get_str(json, "challenge_base_hex", base_hex, sizeof base_hex) &&
        !jm_get_str(json, "challenge_hex", base_hex, sizeof base_hex))
        fail("hashx_compile", runtime, "hashx_compile requires a challenge");
    uint8_t base[MAX_CHALLENGE];
    int base_len = hex_decode(base_hex, base, sizeof base);
    if (base_len < 0)
        fail("hashx_compile", runtime, "invalid challenge");
    uint64_t nonce_start = 0;
    jm_get_u64(json, "nonce_start", &nonce_start);

    hashx_type type;
    const char *eff;
    if (strcmp(runtime, "interpret") == 0) {
        type = HASHX_INTERPRETED;
        eff = "interpreted";
    } else if (!JIT_SUPPORTED) {
        /* Avoid the Apple Silicon JIT crash: force interpreter / clean error. */
        if (strcmp(runtime, "must-compile") == 0)
            fail("hashx_compile", runtime,
                 "must-compile requested but JIT not supported on this platform");
        type = HASHX_INTERPRETED;
        eff = "interpreted (fallback)";
    } else {
        type = HASHX_COMPILED;
        eff = "compiled";
    }
    hashx_ctx *hx = hashx_alloc(type);
    if (hx == HASHX_NOTSUPP) {
        if (strcmp(runtime, "must-compile") == 0)
            fail("hashx_compile", runtime, "compiler not supported");
        hx = hashx_alloc(HASHX_INTERPRETED);
        eff = "interpreted (fallback)";
    }
    if (hx == NULL)
        fail("hashx_compile", runtime, "hashx_alloc failed");

    uint8_t seed[MAX_CHALLENGE + 8];
    uint8_t hout[HASHX_SIZE];

    for (uint64_t w = 0; w < warmup; w++) {
        int sl = build_nonce_challenge(base, base_len, nonce_start, 8, seed);
        if (hashx_make(hx, seed, sl))
            hashx_exec(hx, 0, hout);
    }

    run_t *runs = calloc(reps ? reps : 1, sizeof(run_t));
    for (uint64_t i = 0; i < reps; i++) {
        int sl = build_nonce_challenge(base, base_len, nonce_start + i, 8, seed);
        uint64_t t0 = now_ns();
        int made = hashx_make(hx, seed, sl);
        uint64_t t1 = now_ns();
        runs[i].compile_ns = t1 - t0;
        if (made) {
            /* Time a single hashx_exec as the per-hash execution cost. */
            uint64_t e0 = now_ns();
            hashx_exec(hx, 0, hout);
            uint64_t e1 = now_ns();
            runs[i].wall_ns = e1 - e0;
            runs[i].solutions = 1; /* program generated successfully */
        } else {
            runs[i].wall_ns = 0;
            runs[i].solutions = 0; /* rare invalid seed */
        }
    }
    emit("hashx_compile", runtime, eff, runs, reps, NULL);
    free(runs);
    hashx_free(hx);
}

int main(void) {
    char *json = read_all_stdin();
    if (!json)
        fail(NULL, NULL, "failed to read stdin");

    char op[32] = "solve";
    char runtime[32] = "try-compile";
    jm_get_str(json, "operation", op, sizeof op);
    jm_get_str(json, "runtime", runtime, sizeof runtime);

    uint64_t reps = 10, warmup = 3;
    jm_get_u64(json, "repetitions", &reps);
    jm_get_u64(json, "warmup", &warmup);
    if (reps == 0)
        reps = 1;

    if (strcmp(op, "solve") == 0)
        op_solve(json, runtime, reps, warmup);
    else if (strcmp(op, "verify") == 0)
        op_verify(json, runtime, reps, warmup);
    else if (strcmp(op, "effort") == 0)
        op_effort(json, runtime, reps, warmup);
    else if (strcmp(op, "hashx_compile") == 0)
        op_hashx_compile(json, runtime, reps, warmup);
    else
        fail(op, runtime, "unknown operation");

    free(json);
    return 0;
}
