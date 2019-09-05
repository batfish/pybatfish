#!/usr/bin/env bash

set -eou pipefail
files=$(find pybatfish tests -name '*.py')
echo "Formatting files"
autopep8 -ia ${files}
autoflake -i --remove-all-unused-imports --remove-unused-variables ${files}
