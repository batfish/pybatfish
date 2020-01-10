#!/bin/bash

set -euo pipefail

cd docs
apt update -qq && apt -qq install -y pandoc
pip install -e .[dev] -q
pip install -r requirements.txt
make html
