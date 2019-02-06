#!/usr/bin/env bash
### Build and quick lint
set -euo pipefail

BATFISH_ARTIFACTS_PLUGIN_VERSION="${BATFISH_ARTIFACTS_PLUGIN_VERSION:-v1.2.0}"
BATFISH_DOCKER_PLUGIN_VERSION="${BATFISH_DOCKER_PLUGIN_VERSION:-v2.2.0}"
BATFISH_DOCKER_CI_BASE_IMAGE="${BATFISH_DOCKER_CI_BASE_IMAGE:-batfish/ci-base:latest}"

cat <<EOF
steps:
EOF

###### WAIT before starting any of the jobs.
cat <<EOF
  - wait
EOF

###### Initial checks plus building the wheel and jar
cat <<EOF
  - label: "Format detection with flake8"
    command:
      - "python3 -m virtualenv .venv"
      - ". .venv/bin/activate"
      - "python3 -m pip install flake8 flake8-docstrings flake8-import-order"
      - "flake8 pybatfish tests"
    plugins:
      - docker#${BATFISH_DOCKER_PLUGIN_VERSION}:
          image: ${BATFISH_DOCKER_CI_BASE_IMAGE}
          always-pull: true
  - label: "Type checking with mypy"
    command:
      - "python3 -m virtualenv .venv"
      - ". .venv/bin/activate"
      - "python3 -m pip install mypy"
      - "mypy pybatfish"
      - "mypy --py2 pybatfish"
    plugins:
      - docker#${BATFISH_DOCKER_PLUGIN_VERSION}:
          image: ${BATFISH_DOCKER_CI_BASE_IMAGE}
          always-pull: true
EOF

###### WAIT for simole checks before starting heavier ones.
cat <<EOF
  - wait
EOF

cat <<EOF
  - label: "Build batfish jar"
    command:
      - "mkdir workspace"
      - ".buildkite/build_batfish.sh"
    artifact_paths:
      - workspace/allinone.jar
      - workspace/questions.tgz
    plugins:
      - docker#${BATFISH_DOCKER_PLUGIN_VERSION}:
          image: ${BATFISH_DOCKER_CI_BASE_IMAGE}
          always-pull: true
EOF

for version in 2.7 3.5 3.6 3.7; do
cat <<EOF
  - label: "Python ${version} unit tests"
    command:
      - "pip install -e .[dev]"
      - "pytest tests"
    plugins:
      - docker#${BATFISH_DOCKER_PLUGIN_VERSION}:
          image: "python:${version}"
          always-pull: true
EOF
done

###### After unit tests pass, run integration tests
cat <<EOF
  - wait
EOF

###### Integration tests
for version in 2.7 3.5 3.6 3.7; do
cat <<EOF
  - label: "Python ${version} integration tests"
    command:
      - "apt update -qq && apt -qq install -y openjdk-8-jre-headless"
      - "tar -xzf workspace/questions.tgz -C workspace"
      - "java -cp workspace/allinone.jar org.batfish.allinone.Main -runclient false -coordinatorargs '-templatedirs workspace/questions -periodassignworkms=5' &"
      - "pip install -e .[dev] -q"
      - "pytest tests/integration"
    plugins:
      - docker#${BATFISH_DOCKER_PLUGIN_VERSION}:
          image: "python:${version}"
          always-pull: true
      - artifacts#${BATFISH_ARTIFACTS_PLUGIN_VERSION}:
          download:
            - workspace/allinone.jar
            - workspace/questions.tgz
EOF
done

