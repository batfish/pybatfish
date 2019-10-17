#!/usr/bin/env bash
set -euo pipefail

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
