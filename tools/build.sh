#!/usr/bin/env bash
# Rebuild every generated page.
#
#   bash tools/build.sh
#
# Pages in public/ are GENERATED. Editing them by hand loses the change on the next
# build; edit the builder in tools/ instead. Nothing here needs an API key or a
# network: the page numbers are read from the config files in config/.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PYTHON:-python3}

run () { echo; echo "==> $1"; shift; "$@"; }

run "check the configs still load"   $PY -m tests.test_network
run "page: overview (index.html)"    $PY tools/build_index.py

echo
echo "==> done."
