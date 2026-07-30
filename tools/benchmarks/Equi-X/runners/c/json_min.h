/* Minimal JSON reader for the Equi-X runner protocol.
 *
 * The job-spec is a FLAT object of scalar fields (no nested objects/arrays on
 * the input side), so a tiny key->value scanner is sufficient and avoids any
 * external dependency. Result JSON is emitted by hand in equix_runner.c.
 *
 * Each getter searches for the exact quoted key ("key") which makes prefix
 * collisions impossible (e.g. searching "nonce" never matches "nonce_bytes",
 * because the char after the opening key is '_' not '"').
 */
#ifndef EQUIX_RUNNER_JSON_MIN_H
#define EQUIX_RUNNER_JSON_MIN_H

#include <stddef.h>
#include <stdint.h>

/* All return 1 if the key was found (and, for typed getters, parsed), else 0. */
int jm_get_str(const char *json, const char *key, char *out, size_t outsz);
int jm_get_u64(const char *json, const char *key, uint64_t *out);
int jm_get_i64(const char *json, const char *key, int64_t *out);
int jm_get_bool(const char *json, const char *key, int *out);

#endif /* EQUIX_RUNNER_JSON_MIN_H */
