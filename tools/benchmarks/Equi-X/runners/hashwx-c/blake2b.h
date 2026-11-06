/* BLAKE2b with a 32-byte digest and no key, for deriving HashWX seeds. */
#ifndef HASHWX_RUNNER_BLAKE2B_H
#define HASHWX_RUNNER_BLAKE2B_H

#include <stddef.h>
#include <stdint.h>

void blake2b_256(const uint8_t *in, size_t len, uint8_t out[32]);

#endif /* HASHWX_RUNNER_BLAKE2B_H */
