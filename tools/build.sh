#!/usr/bin/env bash
# Rebuild every generated page and both social cards.
#
#   bash tools/build.sh
#
# Pages in public/ are GENERATED. Editing them by hand loses the change on the next
# build; edit the builder in tools/ instead. Nothing here needs an API key or a
# network: page numbers come from config/, and code excerpts from the package itself.
#
# ORDER MATTERS. The nav, and some in-page links, emit a link only once the target
# page exists, so the overview is built last: by then every other page is on disk.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON:-python3}

run () { echo; echo "==> $1"; shift; "$@"; }

run "check the configs still load"  $PY -m tests.test_network
run "page: architecture"            $PY tools/build_architecture.py
run "page: overview"                $PY tools/build_index.py
run "social cards"                  $PY tools/build_cards.py

echo
echo "==> done."
