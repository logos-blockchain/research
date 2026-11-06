/* BLAKE2b (RFC 7693) with a 32-byte digest and no key. */
#include "blake2b.h"

#include <string.h>

static const uint64_t IV[8] = {
    0x6a09e667f3bcc908ULL, 0xbb67ae8584caa73bULL, 0x3c6ef372fe94f82bULL, 0xa54ff53a5f1d36f1ULL,
    0x510e527fade682d1ULL, 0x9b05688c2b3e6c1fULL, 0x1f83d9abfb41bd6bULL, 0x5be0cd19137e2179ULL,
};

static const uint8_t SIGMA[12][16] = {
    {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15},
    {14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3},
    {11, 8, 12, 0, 5, 2, 15, 13, 10, 14, 3, 6, 7, 1, 9, 4},
    {7, 9, 3, 1, 13, 12, 11, 14, 2, 6, 5, 10, 4, 0, 15, 8},
    {9, 0, 5, 7, 2, 4, 10, 15, 14, 1, 11, 12, 6, 8, 3, 13},
    {2, 12, 6, 10, 0, 11, 8, 3, 4, 13, 7, 5, 15, 14, 1, 9},
    {12, 5, 1, 15, 14, 13, 4, 10, 0, 7, 6, 3, 9, 2, 8, 11},
    {13, 11, 7, 14, 12, 1, 3, 9, 5, 0, 15, 4, 8, 6, 2, 10},
    {6, 15, 14, 9, 11, 3, 0, 8, 12, 2, 13, 7, 1, 4, 10, 5},
    {10, 2, 8, 4, 7, 6, 1, 5, 15, 11, 9, 14, 3, 12, 13, 0},
    {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15},
    {14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3},
};

static uint64_t rotr64(uint64_t x, int n) { return (x >> n) | (x << (64 - n)); }

static uint64_t load64_le(const uint8_t *p) {
    uint64_t v = 0;
    for (int i = 7; i >= 0; i--)
        v = (v << 8) | p[i];
    return v;
}

#define G(a, b, c, d, x, y)                                                                        \
    do {                                                                                           \
        v[a] += v[b] + (x);                                                                        \
        v[d] = rotr64(v[d] ^ v[a], 32);                                                            \
        v[c] += v[d];                                                                              \
        v[b] = rotr64(v[b] ^ v[c], 24);                                                            \
        v[a] += v[b] + (y);                                                                        \
        v[d] = rotr64(v[d] ^ v[a], 16);                                                            \
        v[c] += v[d];                                                                              \
        v[b] = rotr64(v[b] ^ v[c], 63);                                                            \
    } while (0)

static void compress(uint64_t h[8], const uint8_t block[128], uint64_t total, int last) {
    uint64_t m[16], v[16];
    for (int i = 0; i < 16; i++)
        m[i] = load64_le(block + 8 * i);
    for (int i = 0; i < 8; i++) {
        v[i] = h[i];
        v[i + 8] = IV[i];
    }
    v[12] ^= total; /* inputs here are far below 2^64 bytes, so the high word stays 0 */
    if (last)
        v[14] = ~v[14];
    for (int r = 0; r < 12; r++) {
        const uint8_t *s = SIGMA[r];
        G(0, 4, 8, 12, m[s[0]], m[s[1]]);
        G(1, 5, 9, 13, m[s[2]], m[s[3]]);
        G(2, 6, 10, 14, m[s[4]], m[s[5]]);
        G(3, 7, 11, 15, m[s[6]], m[s[7]]);
        G(0, 5, 10, 15, m[s[8]], m[s[9]]);
        G(1, 6, 11, 12, m[s[10]], m[s[11]]);
        G(2, 7, 8, 13, m[s[12]], m[s[13]]);
        G(3, 4, 9, 14, m[s[14]], m[s[15]]);
    }
    for (int i = 0; i < 8; i++)
        h[i] ^= v[i] ^ v[i + 8];
}

void blake2b_256(const uint8_t *in, size_t len, uint8_t out[32]) {
    uint64_t h[8];
    memcpy(h, IV, sizeof h);
    h[0] ^= 0x01010000ULL ^ 32u; /* depth 1, fanout 1, no key, 32-byte digest */

    uint64_t total = 0;
    while (len > 128) {
        total += 128;
        compress(h, in, total, 0);
        in += 128;
        len -= 128;
    }
    uint8_t block[128] = {0};
    if (len)
        memcpy(block, in, len);
    total += len;
    compress(h, block, total, 1);

    for (int i = 0; i < 4; i++)
        for (int b = 0; b < 8; b++)
            out[8 * i + b] = (uint8_t)(h[i] >> (8 * b));
}
