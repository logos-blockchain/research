#include "effort.h"

#include <string.h>

/* blake2.h is an internal hashx header (not installed); referenced by include
 * path into the vendored submodule. We use the full (12-round) standard
 * BLAKE2b via init_param/update/final -- NOT the reduced hashx_blake2b_4r. */
#include <blake2.h>

void effort_solution_bytes(const equix_solution *sol, uint8_t out[16]) {
    for (int i = 0; i < EQUIX_NUM_IDX; i++) {
        out[2 * i] = (uint8_t)(sol->idx[i] & 0xff);
        out[2 * i + 1] = (uint8_t)((sol->idx[i] >> 8) & 0xff);
    }
}

/* Standard unkeyed BLAKE2b-256 (digest 32, fanout 1, depth 1, all else zero). */
static void blake2b256(const uint8_t *in1, size_t len1, const uint8_t *in2,
                       size_t len2, uint8_t out[32]) {
    blake2b_param p;
    memset(&p, 0, sizeof p);
    p.digest_length = 32;
    p.fanout = 1;
    p.depth = 1;

    blake2b_state s;
    hashx_blake2b_init_param(&s, &p);
    hashx_blake2b_update(&s, in1, len1);
    hashx_blake2b_update(&s, in2, len2);
    hashx_blake2b_final(&s, out, 32);
}

uint32_t effort_of(const uint8_t *challenge, size_t challenge_len,
                   const equix_solution *sol) {
    uint8_t sol_bytes[16];
    effort_solution_bytes(sol, sol_bytes);

    uint8_t h[32];
    blake2b256(challenge, challenge_len, sol_bytes, sizeof sol_bytes, h);

    uint32_t hash32 = ((uint32_t)h[0] << 24) | ((uint32_t)h[1] << 16) |
                      ((uint32_t)h[2] << 8) | (uint32_t)h[3];
    if (hash32 == 0)
        return 0xFFFFFFFFu;
    return 0xFFFFFFFFu / hash32;
}
