#include "json_min.h"

#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* Return a pointer to the first non-space char of the value for `key`, or NULL
 * if the key is absent / malformed. */
static const char *find_val(const char *json, const char *key) {
    char pat[128];
    int n = snprintf(pat, sizeof pat, "\"%s\"", key);
    if (n <= 0 || (size_t)n >= sizeof pat)
        return NULL;
    const char *p = strstr(json, pat);
    if (!p)
        return NULL;
    p += (size_t)n;
    while (*p && *p != ':')
        p++;
    if (*p != ':')
        return NULL;
    p++;
    while (*p == ' ' || *p == '\t' || *p == '\n' || *p == '\r')
        p++;
    return p;
}

int jm_get_str(const char *json, const char *key, char *out, size_t outsz) {
    const char *p = find_val(json, key);
    if (!p || *p != '"')
        return 0; /* absent or null/non-string */
    p++;
    size_t i = 0;
    while (*p && *p != '"') {
        char c = *p++;
        if (c == '\\' && *p) {
            char e = *p++;
            switch (e) {
            case 'n': c = '\n'; break;
            case 't': c = '\t'; break;
            case 'r': c = '\r'; break;
            case '"': c = '"'; break;
            case '\\': c = '\\'; break;
            case '/': c = '/'; break;
            default: c = e; break;
            }
        }
        if (i + 1 < outsz)
            out[i++] = c;
    }
    if (i < outsz)
        out[i] = '\0';
    else if (outsz)
        out[outsz - 1] = '\0';
    return 1;
}

int jm_get_u64(const char *json, const char *key, uint64_t *out) {
    const char *p = find_val(json, key);
    if (!p || (!isdigit((unsigned char)*p) && *p != '+'))
        return 0;
    *out = strtoull(p, NULL, 10);
    return 1;
}

int jm_get_i64(const char *json, const char *key, int64_t *out) {
    const char *p = find_val(json, key);
    if (!p || (!isdigit((unsigned char)*p) && *p != '-' && *p != '+'))
        return 0;
    *out = strtoll(p, NULL, 10);
    return 1;
}

int jm_get_bool(const char *json, const char *key, int *out) {
    const char *p = find_val(json, key);
    if (!p)
        return 0;
    if (strncmp(p, "true", 4) == 0) {
        *out = 1;
        return 1;
    }
    if (strncmp(p, "false", 5) == 0) {
        *out = 0;
        return 1;
    }
    return 0;
}
