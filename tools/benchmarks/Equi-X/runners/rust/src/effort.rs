//! Tor proposal-327 style effort computation.
//!
//! MUST be byte-identical to the C runner (runners/c/effort.c): standard
//! BLAKE2b-256 over `challenge || solution_bytes`, first 32 bits big-endian as
//! `hash32`, achieved effort = floor((2^32-1) / hash32). The Python cross-check
//! asserts both runners agree on a fixed (challenge, solution).

use blake2::digest::consts::U32;
use blake2::{Blake2b, Digest};

type Blake2b256 = Blake2b<U32>;

/// Achieved effort of `solution_bytes` (16-byte packed form) for `challenge`.
pub fn effort_of(challenge: &[u8], solution_bytes: &[u8]) -> u32 {
    let mut h = Blake2b256::new();
    h.update(challenge);
    h.update(solution_bytes);
    let out = h.finalize();
    let hash32 = u32::from_be_bytes([out[0], out[1], out[2], out[3]]);
    if hash32 == 0 {
        u32::MAX
    } else {
        u32::MAX / hash32
    }
}
