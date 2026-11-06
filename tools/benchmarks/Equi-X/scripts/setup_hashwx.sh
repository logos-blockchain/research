#!/usr/bin/env bash
# Fetch HashWX at its pinned tag and build the benchmark runner. Idempotent.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

TAG="v1.0.0"
COMMIT="74b567a31276a4c5d7cb232a5b7639467f49f961"
DIR="vendored/hashwx"

if [ ! -d "$DIR/.git" ]; then
  mkdir -p vendored
  git -c advice.detachedHead=false clone --quiet --depth 1 --branch "$TAG" \
    https://github.com/tevador/hashwx.git "$DIR"
fi

HAVE="$(git -C "$DIR" rev-parse HEAD)"
if [ "$HAVE" != "$COMMIT" ]; then
  echo "error: $DIR is at $HAVE, expected $COMMIT ($TAG)" >&2
  exit 1
fi

cmake -S runners/hashwx-c -B build/runners/hashwx-c \
  -DCMAKE_BUILD_TYPE=Release \
  -DHASHWX_C_COMMIT="$COMMIT" \
  -DHASHWX_C_VERSION="${TAG#v}" >/dev/null
cmake --build build/runners/hashwx-c --parallel >/dev/null

build/runners/hashwx-c/hashwx_ext/hashwx-tests | tail -1
echo "built build/runners/hashwx-c/hashwx_runner at $TAG"
