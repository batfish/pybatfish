#!bin/bash

set -euo pipefail

version=$1
pip install -e .[dev]
pytest tests --cov=pybatfish
bash <(curl -s https://codecov.io/bash) -t 91216eec-ae5e-4836-8ee5-1d5a71d1b5bc -cF unit-${version//.}
