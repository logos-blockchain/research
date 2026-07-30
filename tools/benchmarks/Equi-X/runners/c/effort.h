/* Tor proposal-327 style effort computation for Equi-X solutions.
 *
 * The effort layer sits ABOVE Equi-X: given a solved (challenge, solution),
 * we hash them with standard BLAKE2b-256 and read the first 32 bits big-endian
 * as `hash32`. A solution is "valid at effort E" iff hash32 * E <= 2^32-1, so
 * the achieved effort of a solution is floor((2^32-1) / hash32).
 *
 * The preimage layout and byte order defined here MUST be identical to the Rust
 * runner (runners/rust/src/effort.rs) -- the Python cross-check asserts both
 * implementations produce the same effort for a fixed (challenge, solution).
 *
 * Preimage = challenge_bytes || solution_bytes
 *   solution_bytes = 8 x uint16 little-endian (equix_solution.idx[])
 */
#ifndef EQUIX_RUNNER_EFFORT_H
#define EQUIX_RUNNER_EFFORT_H

#include <stddef.h>
#include <stdint.h>

#include <equix.h>

/* Serialize an Equi-X solution to its canonical 16-byte little-endian form. */
void effort_solution_bytes(const equix_solution *sol, uint8_t out[16]);

/* Achieved effort of `sol` for `challenge`. Returns UINT32_MAX when hash32==0. */
uint32_t effort_of(const uint8_t *challenge, size_t challenge_len,
                   const equix_solution *sol);

#endif /* EQUIX_RUNNER_EFFORT_H */
