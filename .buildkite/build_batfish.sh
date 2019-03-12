#!/usr/bin/env bash

set -euxo pipefail

BF_DIR=$(mktemp -d)
git clone --depth=1 --branch=${BATFISH_GITHUB_BATFISH_REF} ${BATFISH_GITHUB_BATFISH_REPO} ${BF_DIR}
mvn -f ${BF_DIR}/projects package
cp ${BF_DIR}/projects/allinone/target/allinone-bundle-*.jar workspace/allinone.jar
tar -czf workspace/questions.tgz -C ${BF_DIR} questions
