#!/bin/bash

set -euo pipefail

apt update -qq && apt -qq install -y openjdk-11-jre-headless
tar -xzf workspace/questions.tgz
java -cp workspace/allinone.jar org.batfish.allinone.Main -runclient false -coordinatorargs '-templatedirs questions -periodassignworkms=5' 2>&1 > workspace/batfish.log &
pip install -r docs/requirements.txt
pip install -e .[dev] -q
pytest docs pybatfish --doctest-glob='docs/source/*.rst' --doctest-modules
