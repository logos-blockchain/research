#!/usr/bin/env bash
# =============================================================================
# Publish the dashboard to this repo's GitHub Pages (gh-pages branch).
#
# Serves at https://logos-blockchain.github.io/research/pqc/ — the root
# index.html is a small landing page for the repo's published artifacts and is
# regenerated here too, so keep it in sync if other artifacts join it.
#
# The gh-pages branch is generated OUTPUT (like a build artifact): it is
# rebuilt from scratch and force-pushed on every publish. Never commit to it
# by hand. Requires push access to logos-blockchain/research; Pages must be
# enabled once by an admin (Settings -> Pages -> deploy from gh-pages, /).
# =============================================================================
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHA="$(git -C "$HERE" rev-parse --short HEAD)"
[ -f "$HERE/dashboard/data/merged.json" ] || {
  echo "no dashboard/data/merged.json — run 'make merge' first" >&2; exit 1; }

T="$(mktemp -d)"
mkdir -p "$T/pqc/data"
cp "$HERE/dashboard/index.html" "$HERE/dashboard/app.js" "$HERE/dashboard/style.css" "$T/pqc/"
cp "$HERE/dashboard/data/merged.json" "$T/pqc/data/"
cat > "$T/index.html" <<'HTML'
<!doctype html>
<meta charset="utf-8">
<title>Logos Research — published artifacts</title>
<style>body{font:16px/1.6 system-ui;margin:4rem auto;max-width:42rem;padding:0 1rem;color:#222}
a{color:#0b62d6} h1{font-size:1.4rem} li{margin:.4rem 0}</style>
<h1>Logos Research — published artifacts</h1>
<ul>
  <li><a href="pqc/">pqc — post-quantum cryptography benchmark dashboard</a><br>
      <small>Migration cost from X25519/Ed25519 to PQ candidates: primitives, TLS 1.3 phase matrix,
      four platforms (reference: Raspberry Pi 5). Tool: <code>tools/benchmarks/pqc</code>.</small></li>
</ul>
HTML
( cd "$T" && git init -q && git checkout -qb gh-pages && git add -A \
  && git commit -qm "pages: pqc dashboard @ $SHA" \
  && git push -q --force git@github.com:logos-blockchain/research.git gh-pages )
rm -rf "$T"
echo "published gh-pages @ $SHA"
echo "URL: https://logos-blockchain.github.io/research/pqc/ (allow ~1 min for Pages deploy)"
