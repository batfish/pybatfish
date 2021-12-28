#!/usr/bin/env bash
set -euo pipefail

BATFISH_ARTIFACTS_PLUGIN_VERSION="${BATFISH_ARTIFACTS_PLUGIN_VERSION:-v1.4.0}"
BATFISH_DOCKER_PLUGIN_VERSION="${BATFISH_DOCKER_PLUGIN_VERSION:-v3.9.0}"
BATFISH_DOCKER_CI_BASE_IMAGE="${BATFISH_DOCKER_CI_BASE_IMAGE:-batfish/ci-base:1a171db-7eeaf7f00b}"
BATFISH_GITHUB_BATFISH_REF="${BATFISH_GITHUB_BATFISH_REF:-master}"
BATFISH_GITHUB_BATFISH_REPO="${BATFISH_GITHUB_BATFISH_REPO:-https://github.com/batfish/batfish}"
PYBATFISH_PYTHON_TEST_VERSIONS=(3.7 3.8 3.9)

cat <<EOF
steps:
EOF

###### WAIT before starting any of the jobs.
cat <<EOF
  - wait
EOF

###### Initial checks plus building the wheel and jar
cat <<EOF
  - label: ":python-black: Format checking"
    command:
      - "python3 -m virtualenv .venv"
      - ". .venv/bin/activate"
      # https://github.com/pypa/virtualenv/issues/2257
      - "python3 -m pip install pre-commit 'virtualenv<20.11.0'"
      - "pre-commit run --all-files"
    plugins:
      - docker#${BATFISH_DOCKER_PLUGIN_VERSION}:
          image: ${BATFISH_DOCKER_CI_BASE_IMAGE}
          always-pull: true
  - label: "Type checking with mypy"
    command:
      - "python3 -m virtualenv .venv"
      - ". .venv/bin/activate"
      - "python3 -m pip install 'mypy<0.800'"
      - "mypy pybatfish tests"
    plugins:
      - docker#${BATFISH_DOCKER_PLUGIN_VERSION}:
          image: ${BATFISH_DOCKER_CI_BASE_IMAGE}
          always-pull: true
EOF

###### WAIT for simple checks before starting heavier ones.
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
          environment:
            - "BATFISH_GITHUB_BATFISH_REF=${BATFISH_GITHUB_BATFISH_REF}"
            - "BATFISH_GITHUB_BATFISH_REPO=${BATFISH_GITHUB_BATFISH_REPO}"
EOF

for version in ${PYBATFISH_PYTHON_TEST_VERSIONS[@]}; do
  cat <<EOF
  - label: "Python ${version} unit tests"
    command:
      - bash .buildkite/unit_tests.sh ${version}
    plugins:
      - docker#${BATFISH_DOCKER_PLUGIN_VERSION}:
          image: "python:${version}"
          always-pull: true
          propagate-environment: true
EOF
done

###### After unit tests pass, run integration tests
cat <<EOF
  - wait
EOF

###### Integration tests and doctests
for version in ${PYBATFISH_PYTHON_TEST_VERSIONS[@]}; do
  cat <<EOF
  - label: "Python ${version} integration tests"
    command:
      - bash .buildkite/integration_tests.sh ${version}
    artifact_paths:
      - workspace/batfish.log
    plugins:
      - docker#${BATFISH_DOCKER_PLUGIN_VERSION}:
          image: "python:${version}"
          always-pull: true
          propagate-environment: true
      - artifacts#${BATFISH_ARTIFACTS_PLUGIN_VERSION}:
          download:
            - workspace/allinone.jar
            - workspace/questions.tgz
EOF
done

###### Doc tests
cat <<EOF
  - label: "Testing documentation"
    command:
      - bash .buildkite/doc_tests.sh
    plugins:
      - docker#${BATFISH_DOCKER_PLUGIN_VERSION}:
          image: "python:3.7"
          always-pull: true
          propagate-environment: true
      - artifacts#${BATFISH_ARTIFACTS_PLUGIN_VERSION}:
          download:
            - workspace/allinone.jar
            - workspace/questions.tgz
EOF


###### Test building of documentation
cat <<EOF
  - label: "Sphinx: building documentation"
    command:
      - bash .buildkite/build_docs.sh
    plugins:
      - docker#${BATFISH_DOCKER_PLUGIN_VERSION}:
          image: "python:3.7"
          always-pull: true
          propagate-environment: true
      - artifacts#${BATFISH_ARTIFACTS_PLUGIN_VERSION}:
          download:
            - workspace/allinone.jar
            - workspace/questions.tgz
EOF
