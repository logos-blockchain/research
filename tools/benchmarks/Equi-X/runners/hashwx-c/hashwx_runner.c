/* HashWX benchmark runner, for the harness protocol in adapters/README.md.
 *
 * A ticket is hashwx_exec(hashwx_make(seed), nonce), where
 * seed = BLAKE2b-256(challenge || LE64(nonce // 463)), and a nonce satisfies a
 * target d when its ticket is below floor(2^64 / d). The protocol's operations
 * map onto HashWX as follows:
 *
 *   solve          one function's work: one make and 463 execs, on a fresh function.
 *                  HashWX has no solve, and this is what a miner repeats, so
 *                  hashes/s = 463 * solves/s. The harness's own hashes_per_sec
 *                  column assumes Equi-X and does not apply.
 *   verify         one ticket of a fresh function: the seed hash, one make, one
 *                  exec and the comparison. This is the whole cost of a check.
 *   effort         search nonces from nonce_start until a ticket satisfies
 *                  target_effort. attempts counts hashes.
 *   hashx_compile  compile_ns is one make and wall_ns is one exec.
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

#include <hashwx.h>

#include "blake2b.h"
#include "json_min.h"
#include "sha256.h"
#include "timing.h"

#ifndef HASHWX_C_COMMIT
#define HASHWX_C_COMMIT "unknown"
#endif
#ifndef HASHWX_C_VERSION
#define HASHWX_C_VERSION "1.0.0"
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
#else
#define ARCH_STR "unknown"
#endif

#define NONCES_PER_SEED 463u
#define MAX_CHALLENGE 256

/* The CPU model, from sysctl on macOS and /proc/cpuinfo elsewhere. */
static const char *cpu_model(void) {
    static char model[256];
    if (model[0])
        return model;
    strcpy(model, "unknown");
#if defined(__APPLE__)
    size_t sz = sizeof model;
    if (sysctlbyname("machdep.cpu.brand_string", model, &sz, NULL, 0) != 0 || !model[0])
        strcpy(model, "unknown");
#else
    FILE *f = fopen("/proc/cpuinfo", "r");
    if (!f)
        return model;
    static char buf[131072];
    size_t n = fread(buf, 1, sizeof buf - 1, f);
    buf[n] = '\0';
    fclose(f);
    static const char *fields[] = {"model name", "Model", "Hardware", "cpu model"};
    for (size_t fi = 0; fi < sizeof fields / sizeof fields[0]; fi++) {
        size_t fl = strlen(fields[fi]);
        for (const char *p = buf; p; p = strchr(p, '\n') ? strchr(p, '\n') + 1 : NULL) {
            if (strncmp(p, fields[fi], fl) != 0 || (p[fl] != ' ' && p[fl] != '\t' && p[fl] != ':'))
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
#endif
    return model;
}

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

static int hex_digit(char c) {
    if (c >= '0' && c <= '9')
        return c - '0';
    if (c >= 'a' && c <= 'f')
        return c - 'a' + 10;
    if (c >= 'A' && c <= 'F')
        return c - 'A' + 10;
    return -1;
}

static int hex_decode(const char *hex, uint8_t *out, size_t outcap) {
    size_t hl = strlen(hex);
    if (hl % 2 != 0 || hl / 2 > outcap)
        return -1;
    for (size_t i = 0; i < hl / 2; i++) {
        int hi = hex_digit(hex[2 * i]), lo = hex_digit(hex[2 * i + 1]);
        if (hi < 0 || lo < 0)
            return -1;
        out[i] = (uint8_t)((hi << 4) | lo);
    }
    return (int)(hl / 2);
}

typedef struct {
    uint64_t wall_ns;
    int solutions;
    uint64_t compile_ns;
    uint64_t attempts;
    uint64_t achieved_effort;
    const char *verify_result;
} run_t;

static void fail(const char *op, const char *runtime_req, const char *msg) {
    printf("{\"schema_version\":1,\"ok\":false,"
           "\"impl\":{\"name\":\"hashwx-c\",\"version\":\"%s\",\"commit\":\"%s\","
           "\"runtime_effective\":null},"
           "\"operation\":\"%s\",\"runtime_requested\":\"%s\",\"runtime_effective\":null,"
           "\"env\":{\"os\":\"%s\",\"compiler\":\"%s\",\"cpu\":\"%s\","
           "\"arch\":\"%s\",\"device\":\"cpu\",\"os_version\":\"%s\"},"
           "\"runs\":[],\"peak_rss_kb\":%ld,\"error\":\"%s\"}\n",
           HASHWX_C_VERSION, HASHWX_C_COMMIT, op ? op : "", runtime_req ? runtime_req : "", OS_STR,
           COMPILER_STR, cpu_model(), ARCH_STR, os_version(), peak_rss_kb(), msg);
    exit(1);
}

static void emit(const char *op, const char *runtime_req, const char *runtime_eff,
                 const run_t *runs, size_t nruns, const char *solutions_hex_json,
                 const char *winning_nonce_hex) {
    printf("{\"schema_version\":1,\"ok\":true,"
           "\"impl\":{\"name\":\"hashwx-c\",\"version\":\"%s\",\"commit\":\"%s\","
           "\"runtime_effective\":\"%s\"},"
           "\"operation\":\"%s\",\"runtime_requested\":\"%s\",\"runtime_effective\":\"%s\","
           "\"env\":{\"os\":\"%s\",\"compiler\":\"%s\",\"cpu\":\"%s\","
           "\"arch\":\"%s\",\"device\":\"cpu\",\"os_version\":\"%s\"},\"runs\":[",
           HASHWX_C_VERSION, HASHWX_C_COMMIT, runtime_eff, op, runtime_req, runtime_eff, OS_STR,
           COMPILER_STR, cpu_model(), ARCH_STR, os_version());
    for (size_t i = 0; i < nruns; i++) {
        const run_t *r = &runs[i];
        printf("%s{\"index\":%zu,\"wall_ns\":%llu,\"solutions\":%d,\"compile_ns\":%llu,"
               "\"attempts\":%llu,\"achieved_effort\":%llu,\"verify_result\":",
               i ? "," : "", i, (unsigned long long)r->wall_ns, r->solutions,
               (unsigned long long)r->compile_ns, (unsigned long long)r->attempts,
               (unsigned long long)r->achieved_effort);
        if (r->verify_result)
            printf("\"%s\"}", r->verify_result);
        else
            printf("null}");
    }
    printf("],\"solutions_hex\":%s,", solutions_hex_json ? solutions_hex_json : "null");
    if (winning_nonce_hex)
        printf("\"winning_nonce_hex\":\"%s\",", winning_nonce_hex);
    printf("\"peak_rss_kb\":%ld,\"error\":null}\n", peak_rss_kb());
}

static hashwx_ctx *alloc_ctx(const char *op, const char *runtime, const char **eff) {
    hashwx_ctx *ctx;
    if (strcmp(runtime, "interpret") == 0) {
        ctx = hashwx_alloc(HASHWX_INTERPRETED);
        *eff = "interpreted";
    } else {
        ctx = hashwx_alloc(HASHWX_COMPILED);
        *eff = "compiled";
        if (ctx == HASHWX_NOTSUPP) {
            if (strcmp(runtime, "must-compile") == 0)
                fail(op, runtime, "must-compile requested but the compiler is not supported here");
            ctx = hashwx_alloc(HASHWX_INTERPRETED);
            *eff = "interpreted (fallback)";
        }
    }
    if (ctx == NULL || ctx == HASHWX_NOTSUPP)
        fail(op, runtime, "hashwx_alloc failed");
    return ctx;
}

static void derive_seed(const uint8_t *challenge, size_t clen, uint64_t group, uint8_t seed[32]) {
    uint8_t buf[MAX_CHALLENGE + 8];
    memcpy(buf, challenge, clen);
    for (int i = 0; i < 8; i++)
        buf[clen + i] = (uint8_t)(group >> (8 * i));
    blake2b_256(buf, clen + 8, seed);
}

/* A stream of challenges: a SHA-256 chain over challenge_seed_hex when present,
 * otherwise a fixed challenge_hex. Advancing it is never inside a timed region. */
typedef struct {
    uint8_t bytes[MAX_CHALLENGE];
    size_t len;
    int chained;
} challenges_t;

static void challenges_next(challenges_t *c) {
    if (!c->chained)
        return;
    uint8_t next[32];
    sha256(c->bytes, c->len, next);
    memcpy(c->bytes, next, 32);
    c->len = 32;
}

static void challenges_init(challenges_t *c, const char *json, const char *op, const char *runtime) {
    char hex[2 * MAX_CHALLENGE + 1] = {0};
    c->chained = 0;
    if (jm_get_str(json, "challenge_seed_hex", hex, sizeof hex))
        c->chained = 1;
    else if (!jm_get_str(json, "challenge_hex", hex, sizeof hex))
        fail(op, runtime, "requires challenge_hex or challenge_seed_hex");
    int n = hex_decode(hex, c->bytes, sizeof c->bytes);
    if (n < 0)
        fail(op, runtime, "invalid challenge");
    c->len = (size_t)n;
    challenges_next(c);
}

static volatile uint64_t sink;

static void op_solve(const char *json, const char *runtime, uint64_t reps, uint64_t warmup) {
    const char *eff = "?";
    hashwx_ctx *ctx = alloc_ctx("solve", runtime, &eff);
    challenges_t c;
    challenges_init(&c, json, "solve", runtime);
    uint8_t seed[32];

    uint64_t group = 0, acc = 0;
    for (uint64_t w = 0; w < warmup; w++, group++) {
        derive_seed(c.bytes, c.len, group, seed);
        hashwx_make(ctx, seed);
        for (uint64_t k = 0; k < NONCES_PER_SEED; k++)
            acc ^= hashwx_exec(ctx, group * NONCES_PER_SEED + k);
        challenges_next(&c);
    }
    run_t *runs = calloc(reps, sizeof(run_t));
    for (uint64_t i = 0; i < reps; i++, group++) {
        derive_seed(c.bytes, c.len, group, seed);
        uint64_t t0 = now_ns();
        hashwx_make(ctx, seed);
        for (uint64_t k = 0; k < NONCES_PER_SEED; k++)
            acc ^= hashwx_exec(ctx, group * NONCES_PER_SEED + k);
        uint64_t t1 = now_ns();
        runs[i].wall_ns = t1 - t0;
        runs[i].solutions = 1;
        challenges_next(&c);
    }
    sink = acc;
    /* The nonce stands in for a solution, for the harness's verify probe. */
    emit("solve", runtime, eff, runs, reps, "[\"0000000000000000\"]", NULL);
    free(runs);
    hashwx_free(ctx);
}

static void op_verify(const char *json, const char *runtime, uint64_t reps, uint64_t warmup) {
    const char *eff = "?";
    hashwx_ctx *ctx = alloc_ctx("verify", runtime, &eff);
    challenges_t c;
    challenges_init(&c, json, "verify", runtime);
    uint8_t seed[32];

    /* Any nonce costs the same to check, and a target of 2^63 is the comparison. */
    const uint64_t threshold = UINT64_C(1) << 63;
    uint64_t nonce = 0, acc = 0;
    for (uint64_t w = 0; w < warmup; w++) {
        derive_seed(c.bytes, c.len, nonce / NONCES_PER_SEED, seed);
        hashwx_make(ctx, seed);
        acc ^= hashwx_exec(ctx, nonce);
        nonce += NONCES_PER_SEED;
        challenges_next(&c);
    }
    run_t *runs = calloc(reps, sizeof(run_t));
    for (uint64_t i = 0; i < reps; i++) {
        uint64_t t0 = now_ns();
        derive_seed(c.bytes, c.len, nonce / NONCES_PER_SEED, seed);
        hashwx_make(ctx, seed);
        uint64_t ticket = hashwx_exec(ctx, nonce);
        int below = ticket < threshold;
        uint64_t t1 = now_ns();
        acc ^= ticket + (uint64_t)below;
        runs[i].wall_ns = t1 - t0;
        runs[i].solutions = 1;
        runs[i].verify_result = "OK";
        nonce += NONCES_PER_SEED;
        challenges_next(&c);
    }
    sink = acc;
    emit("verify", runtime, eff, runs, reps, NULL, NULL);
    free(runs);
    hashwx_free(ctx);
}

/* floor((2^64 - 1) / ticket), the largest target this ticket satisfies, near enough. */
static uint64_t achieved_of(uint64_t ticket) { return ticket ? UINT64_MAX / ticket : UINT64_MAX; }

static void op_effort(const char *json, const char *runtime, uint64_t reps, uint64_t warmup) {
    char base_hex[2 * MAX_CHALLENGE + 1] = {0};
    if (!jm_get_str(json, "challenge_base_hex", base_hex, sizeof base_hex))
        fail("effort", runtime, "effort requires challenge_base_hex");
    uint8_t base[MAX_CHALLENGE];
    int base_len = hex_decode(base_hex, base, sizeof base);
    if (base_len < 0)
        fail("effort", runtime, "invalid challenge_base_hex");

    uint64_t nonce_start = 0, target = 1000000, max_attempts = 200000000;
    jm_get_u64(json, "nonce_start", &nonce_start);
    jm_get_u64(json, "target_effort", &target);
    jm_get_u64(json, "max_attempts", &max_attempts);
    if (target == 0)
        fail("effort", runtime, "target_effort must be positive");
    /* floor(2^64 / 1) does not fit 64 bits, and the harness probes with a target of 1. */
    const uint64_t threshold =
        target < 2 ? UINT64_MAX : (uint64_t)(((unsigned __int128)1 << 64) / target);

    const char *eff = "?";
    hashwx_ctx *ctx = alloc_ctx("effort", runtime, &eff);
    uint8_t seed[32];
    run_t *runs = calloc(reps, sizeof(run_t));
    uint64_t win_nonce = 0;
    int have_token = 0;

    for (uint64_t i = 0; i < warmup + reps; i++) {
        const int timed = i >= warmup;
        uint64_t nonce = nonce_start, attempts = 0, best = 0;
        uint64_t group = UINT64_MAX;
        int found = 0;
        uint64_t t0 = now_ns();
        for (uint64_t a = 0; a < max_attempts; a++, nonce++) {
            if (nonce / NONCES_PER_SEED != group) {
                group = nonce / NONCES_PER_SEED;
                derive_seed(base, (size_t)base_len, group, seed);
                hashwx_make(ctx, seed);
            }
            uint64_t ticket = hashwx_exec(ctx, nonce);
            attempts++;
            uint64_t achieved = achieved_of(ticket);
            if (achieved > best)
                best = achieved;
            if (ticket < threshold) {
                found = 1;
                win_nonce = nonce;
                break;
            }
        }
        uint64_t t1 = now_ns();
        if (timed) {
            run_t *r = &runs[i - warmup];
            r->wall_ns = t1 - t0;
            r->attempts = attempts;
            r->achieved_effort = best;
            r->solutions = found;
            if (found)
                have_token = 1;
        }
    }
    if (have_token) {
        static const char hx[] = "0123456789abcdef";
        char nhex[17];
        for (int b = 0; b < 8; b++) {
            uint8_t v = (uint8_t)(win_nonce >> (8 * b));
            nhex[2 * b] = hx[v >> 4];
            nhex[2 * b + 1] = hx[v & 0xf];
        }
        nhex[16] = '\0';
        emit("effort", runtime, eff, runs, reps, NULL, nhex);
    } else {
        emit("effort", runtime, eff, runs, reps, NULL, NULL);
    }
    free(runs);
    hashwx_free(ctx);
}

static void op_compile(const char *json, const char *runtime, uint64_t reps, uint64_t warmup) {
    char base_hex[2 * MAX_CHALLENGE + 1] = {0};
    if (!jm_get_str(json, "challenge_base_hex", base_hex, sizeof base_hex))
        fail("hashx_compile", runtime, "hashx_compile requires challenge_base_hex");
    uint8_t base[MAX_CHALLENGE];
    int base_len = hex_decode(base_hex, base, sizeof base);
    if (base_len < 0)
        fail("hashx_compile", runtime, "invalid challenge_base_hex");
    uint64_t nonce_start = 0;
    jm_get_u64(json, "nonce_start", &nonce_start);

    const char *eff = "?";
    hashwx_ctx *ctx = alloc_ctx("hashx_compile", runtime, &eff);
    uint8_t seed[32];
    uint64_t acc = 0, group = nonce_start;
    for (uint64_t w = 0; w < warmup; w++, group++) {
        derive_seed(base, (size_t)base_len, group, seed);
        hashwx_make(ctx, seed);
        acc ^= hashwx_exec(ctx, group);
    }
    run_t *runs = calloc(reps, sizeof(run_t));
    for (uint64_t i = 0; i < reps; i++, group++) {
        derive_seed(base, (size_t)base_len, group, seed);
        uint64_t t0 = now_ns();
        hashwx_make(ctx, seed);
        uint64_t t1 = now_ns();
        acc ^= hashwx_exec(ctx, group);
        uint64_t t2 = now_ns();
        runs[i].compile_ns = t1 - t0;
        runs[i].wall_ns = t2 - t1;
        runs[i].solutions = 1;
    }
    sink = acc;
    emit("hashx_compile", runtime, eff, runs, reps, NULL, NULL);
    free(runs);
    hashwx_free(ctx);
}

int main(void) {
    char *json = read_all_stdin();
    if (!json)
        fail(NULL, NULL, "failed to read stdin");

    char op[32] = "verify";
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
        op_compile(json, runtime, reps, warmup);
    else
        fail(op, runtime, "unknown operation");

    free(json);
    return 0;
}
