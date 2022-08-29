#!/bin/bash

set -euo pipefail

apt update -qq && apt -qq install -y pandoc
pip install -e .[dev] -q
pushd docs
ls -la
pip install -r requirements.txt
make html
popd
