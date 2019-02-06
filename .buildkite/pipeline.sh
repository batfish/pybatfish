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
      - "python3 -m pip install flake8"
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
  - label: "Build pybatfish wheel"
    command:
      - "python3 -m virtualenv .venv"
      - ". .venv/bin/activate"
      - "python3 setup.py sdist bdist_wheel"
      - "ls dist"
    artifact_paths:
      - dist/pybatfish-*-py2.py3-none-any.whl
    plugins:
      - docker#${BATFISH_DOCKER_PLUGIN_VERSION}:
          image: ${BATFISH_DOCKER_CI_BASE_IMAGE}
          always-pull: true
EOF

###### WAIT for wheel and jar to be built and format checks to pass before heavier tests
cat <<EOF
  - wait
EOF

for version in "2.7 3.5 3.6 3.7"; do
cat <<EOF
  - label: "Python ${version}"
    command:
      - "python${version} -m virtualenv .venv"
      - ". .venv/bin/activate"
      - "python -m pip install dist/pybatfish-*.whl"
      - "python -m pip install pytest"
      - "pytest tests"
    plugins:
      - docker#${BATFISH_DOCKER_PLUGIN_VERSION}:
          image: ${BATFISH_DOCKER_CI_BASE_IMAGE}
          always-pull: true
      - artifacts#${BATFISH_ARTIFACTS_PLUGIN_VERSION}:
          download: dist/pybatfish-*.whl
EOF
done
