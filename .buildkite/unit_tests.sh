#!bin/bash

set -euo pipefail

version=$1
pip install -e .[dev]
pytest tests 
