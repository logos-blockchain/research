/* Print HashWX outputs in both modes, for test vectors.
 *
 *   hashwx_vectors seed <seed_hex> <nonce>       hashwx_exec(hashwx_make(seed), nonce)
 *   hashwx_vectors ticket <challenge_hex> <nonce>
 *       the same with seed = BLAKE2b-256(challenge || LE64(nonce // 463))
 *
 * Exits non-zero if the two modes disagree.
 */
#include <inttypes.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <hashwx.h>

#include "blake2b.h"

#define NONCES_PER_SEED 463u
#define MAX_CHALLENGE 256

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

static uint64_t run_mode(hashwx_type type, const uint8_t seed[32], uint64_t nonce, int *supported) {
    hashwx_ctx *ctx = hashwx_alloc(type);
    if (ctx == HASHWX_NOTSUPP || ctx == NULL) {
        *supported = 0;
        return 0;
    }
    *supported = 1;
    hashwx_make(ctx, seed);
    uint64_t ticket = hashwx_exec(ctx, nonce);
    hashwx_free(ctx);
    return ticket;
}

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "usage: %s seed|ticket <hex> <nonce>\n", argv[0]);
        return 2;
    }
    uint64_t nonce = strtoull(argv[3], NULL, 10);
    uint8_t seed[32];
    uint8_t bytes[MAX_CHALLENGE + 8];
    int n = hex_decode(argv[2], bytes, MAX_CHALLENGE);
    if (n < 0) {
        fprintf(stderr, "invalid hex\n");
        return 2;
    }
    if (strcmp(argv[1], "seed") == 0) {
        if (n != 32) {
            fprintf(stderr, "a seed is 32 bytes\n");
            return 2;
        }
        memcpy(seed, bytes, 32);
    } else if (strcmp(argv[1], "ticket") == 0) {
        uint64_t group = nonce / NONCES_PER_SEED;
        for (int i = 0; i < 8; i++)
            bytes[n + i] = (uint8_t)(group >> (8 * i));
        blake2b_256(bytes, (size_t)n + 8, seed);
    } else {
        fprintf(stderr, "unknown mode %s\n", argv[1]);
        return 2;
    }

    int have_i, have_c;
    uint64_t interpreted = run_mode(HASHWX_INTERPRETED, seed, nonce, &have_i);
    uint64_t compiled = run_mode(HASHWX_COMPILED, seed, nonce, &have_c);

    printf("seed ");
    for (int i = 0; i < 32; i++)
        printf("%02x", seed[i]);
    printf("\nnonce %" PRIu64 "\n", nonce);
    if (have_i)
        printf("interpreted %016" PRIx64 "\n", interpreted);
    if (have_c)
        printf("compiled %016" PRIx64 "\n", compiled);
    if (!have_i || !have_c)
        printf("note: one mode is not supported here\n");
    return (have_i && have_c && interpreted != compiled) ? 1 : 0;
}
