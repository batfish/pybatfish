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

cat <<EOF
  - label: "Build batfish jar"
    command:
      - "mkdir workspace"
      - "BF_DIR=$$(mktemp -d)"
      - "git clone https://github.com/batfish/batfish $${BF_DIR}"
      - "mvn -f $${BF_DIR}/batfish/projects package"
      - "cp $${BF_DIR}/batfish/projects/allinone/target/allinone-bundle-*.jar workspace/allinone.jar"
    artifact_paths:
      - workspace/allinone.jar
    plugins:
      - docker#${BATFISH_DOCKER_PLUGIN_VERSION}:
          image: ${BATFISH_DOCKER_CI_BASE_IMAGE}
          always-pull: true
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

for version in 2.7 3.5 3.6 3.7; do
cat <<EOF
  - label: "Python ${version}"
    command:
      - "pip install -e .[dev]"
      - "pytest tests"
    plugins:
      - docker#${BATFISH_DOCKER_PLUGIN_VERSION}:
          image: "python:${version}"
          always-pull: true
EOF
done

cat <<EOF
  - label: "Build batfish jar"
    command:
      - "mkdir workspace"
      - "BF_DIR=$$(mktemp -d)"
      - "git clone https://github.com/batfish/batfish $${BF_DIR}"
      - "mvn -f $${BF_DIR}/batfish/projects package"
      - "cp $${BF_DIR}/batfish/projects/allinone/target/allinone-bundle-*.jar workspace/allinone.jar"
    artifact_paths:
      - workspace/allinone.jar
    plugins:
      - docker#${BATFISH_DOCKER_PLUGIN_VERSION}:
          image: "python:${version}"
          always-pull: true
EOF

###### After unit tests pass, run integration tests
cat <<EOF
  - wait
EOF

