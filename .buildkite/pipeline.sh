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

###### Initial checks plus building the jar
cat <<EOF
  - label: "Flake8"
    command: "flake8 pybatfish tests"
    plugins:
      - docker#${BATFISH_DOCKER_PLUGIN_VERSION}:
          image: ${BATFISH_DOCKER_CI_BASE_IMAGE}
          always-pull: true
EOF

###### WAIT for jar to be built and format checks to pass before heavier tests
cat <<EOF
  - wait
EOF
