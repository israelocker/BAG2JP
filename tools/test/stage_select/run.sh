#!/usr/bin/env bash
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "$0")/../../.." && pwd)
test_root="$repo_root/tools/test/stage_select"
test_output=$(mktemp -d /tmp/bag2jp-stage-test.XXXXXX)
trap 'rm -rf -- "$test_output"' EXIT
cc -std=c11 -Wall -Wextra -Wno-unused-function -Wno-address -I"$test_root/stubs" -I"$repo_root/mods-src/bag2jp.feature.bag1-content" "$test_root/test_stage_version.c" -o "$test_output/test_stage_version"
"$test_output/test_stage_version"
python3 "$test_root/test_native_menu.py"
