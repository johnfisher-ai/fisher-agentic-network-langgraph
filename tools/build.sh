#!/usr/bin/env bash
# Rebuild every generated page and both social cards.
#
#   bash tools/build.sh
#
# Pages in public/ are GENERATED. Editing them by hand loses the change on the next
# build; edit the builder in tools/ instead.
#
# tools/capture_runs.py is the ONE stage needing an API key. Its output is committed
# to tools/derived/runs.json, so this build never needs a key or a network.
#
# TWO PASSES, deliberately. Pages link to each other only once the target exists, so
# a link is never offered as a 404. Those references are circular (the code page
# points at Running It and back again), which no single ordering can satisfy on a
# clean tree. The first pass creates the files; the second resolves the links.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON:-python3}

run () { echo; echo "==> $1"; shift; "$@"; }

pages () {
  $PY tools/build_architecture.py
  $PY tools/build_code.py
  $PY tools/build_run.py
  $PY tools/build_index.py
}

run "check the configs still load"  $PY -m tests.test_network
echo; echo "==> pages, pass 1 of 2"; pages
echo; echo "==> pages, pass 2 of 2 (resolves cross-links)"; pages
run "social cards"                  $PY tools/build_cards.py

echo
echo "==> done."
