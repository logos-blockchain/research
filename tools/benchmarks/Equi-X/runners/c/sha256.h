/* Minimal standalone SHA-256 (FIPS 180-4) for deriving per-rep challenges from
 * a seed. Not on any hot path — used only to generate challenges between timed
 * measurements, so plain portable C is fine. */
#ifndef EQUIX_RUNNER_SHA256_H
#define EQUIX_RUNNER_SHA256_H

#include <stddef.h>
#include <stdint.h>

/* One-shot: hash `len` bytes of `data` into the 32-byte `out`. */
void sha256(const uint8_t *data, size_t len, uint8_t out[32]);

#endif /* EQUIX_RUNNER_SHA256_H */
