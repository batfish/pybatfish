#!/bin/bash

set -euo pipefail

version=$1

apt update -qq && apt -qq install -y openjdk-11-jre-headless
tar -xzf workspace/questions.tgz
java -cp workspace/allinone.jar org.batfish.allinone.Main -runclient false -coordinatorargs '-templatedirs questions -periodassignworkms=5' 2>&1 > workspace/batfish.log &
pip install -e .[dev] -q
pytest tests/integration
if [[ $version != "3.5" ]]; then
  pip install -r docs/requirements.txt
  pytest docs pybatfish --doctest-glob='docs/source/*.rst' --doctest-modules
fi
bash <(curl -s https://codecov.io/bash) -t 91216eec-ae5e-4836-8ee5-1d5a71d1b5bc -F integration${version//.}
