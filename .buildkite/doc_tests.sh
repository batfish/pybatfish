#!/bin/bash

set -euo pipefail

pip install -r docs/requirements.txt
pytest docs pybatfish --doctest-glob='docs/source/*.rst' --doctest-modules
