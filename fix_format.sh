#!/usr/bin/env bash
set -euo pipefail

# Black will crash if we use ASCII:
# https://click.palletsprojects.com/en/8.0.x/unicode-support/
# TODO: is there a better place to do this?
export LC_ALL=C.UTF-8
export LANG=C.UTF-8

args=""
if [[ ${1-} == '-c' ]] || [[ ${1-} == '--check' ]]; then
  args="${args} --check"
fi

files="pybatfish tests setup.py"
black ${args} ${files}
black_exit_code=$?
if [[ ${black_exit_code} != 0 ]]; then
  echo "Some files are not formatted correctly. Use $0 to fix these issues."
fi
