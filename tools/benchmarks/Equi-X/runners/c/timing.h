/* Monotonic timing + peak-RSS helpers for the Equi-X C runner. */
#ifndef EQUIX_RUNNER_TIMING_H
#define EQUIX_RUNNER_TIMING_H

#include <stdint.h>
#include <time.h>
#include <sys/resource.h>

/* Monotonic wall-clock nanoseconds (immune to wall-clock adjustments).
 * macOS: clock_gettime(CLOCK_MONOTONIC) only has microsecond granularity, which
 * quantizes ~16 us operations (verify) by +/-3-6%; CLOCK_UPTIME_RAW via
 * clock_gettime_nsec_np gives true nanosecond resolution. */
static inline uint64_t now_ns(void) {
#if defined(__APPLE__)
    return clock_gettime_nsec_np(CLOCK_UPTIME_RAW);
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000000ull + (uint64_t)ts.tv_nsec;
#endif
}

/* Whole-process peak resident set size, in KILOBYTES.
 * ru_maxrss units differ by OS: Linux reports kilobytes, macOS/BSD report bytes. */
static inline long peak_rss_kb(void) {
    struct rusage ru;
    getrusage(RUSAGE_SELF, &ru);
#if defined(__APPLE__)
    return ru.ru_maxrss / 1024; /* macOS: bytes -> KB */
#else
    return ru.ru_maxrss;        /* Linux: already KB */
#endif
}

#endif /* EQUIX_RUNNER_TIMING_H */
