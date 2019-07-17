#!bin/bash

set -euo pipefail

version=$1
pip install -e .[dev]
pytest tests 
bash <(curl -s https://codecov.io/bash) -t 91216eec-ae5e-4836-8ee5-1d5a71d1b5bc -F unit${version//.}
