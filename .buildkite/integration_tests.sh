#!/bin/bash

set -euo pipefail

version=$1

apt update -qq && apt -qq install -y openjdk-11-jre-headless
tar -xzf workspace/questions.tgz

shift
# remaining args are extra coordinator args
coordinator_args=(\
  -templatedirs=questions \
  -periodassignworkms=5 \
  "$@" \
)

allinone_args=(\
  -runclient=false
  -coordinatorargs="$(echo -n "${coordinator_args[@]}")" \
)

java -cp workspace/allinone.jar org.batfish.allinone.Main "${allinone_args[@]}" 2>&1 > workspace/batfish.log &
pip install -e .[dev] -q
pytest tests/integration
