#!/bin/sh
# Regenerate web/app-wp10.js from web/app.js for Windows Phone 10 / EdgeHTML.
#
# EdgeHTML (the Windows 10 Mobile Edge engine) cannot even *parse* the modern
# app.js: optional chaining, optional catch bindings and a few newer DOM APIs
# are syntax/feature errors there (see docs/WP10.md). The WP10 build is the
# same application, transpiled to ES2017 as a classic IIFE script with a small
# polyfill prelude (web/polyfills-wp10.js) prepended.
#
# Run this whenever web/app.js changes, then re-verify on the emulator.
# The committed web/app-wp10.js is the build of the app.js noted in
# docs/WP10.md; this script is the recipe, not a CI step.
set -eu
cd "$(dirname "$0")/.."

ESBUILD="${ESBUILD:-esbuild}"
if ! command -v "$ESBUILD" >/dev/null 2>&1; then
    for candidate in \
        "$HOME/workspace/zero-cloud-documentation/playground/node_modules/.bin/esbuild" \
        ./node_modules/.bin/esbuild; do
        if [ -x "$candidate" ]; then ESBUILD="$candidate"; break; fi
    done
fi
if ! command -v "$ESBUILD" >/dev/null 2>&1; then
    echo "esbuild not found — install it (npm install --save-dev esbuild) or set ESBUILD=/path/to/esbuild" >&2
    exit 1
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT
"$ESBUILD" web/app.js --target=es2017 --format=iife --outfile="$tmp"
cat web/polyfills-wp10.js "$tmp" > web/app-wp10.js
echo "Wrote web/app-wp10.js ($(wc -c < web/app-wp10.js) bytes): web/app.js @ es2017/iife, polyfills prepended."
