#!bin/bash

set -euo pipefail

version=$1
pip install -e .[dev]
pytest tests 

# Codecov handled in GitHub Actions now
## Let codecov upload fail - codecov goes down not infrequently.
#set +o pipefail
#bash <(curl -s https://codecov.io/bash) -t 91216eec-ae5e-4836-8ee5-1d5a71d1b5bc -F unit${version//.}
