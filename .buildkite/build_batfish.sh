#!/usr/bin/env bash

set -euxo pipefail

BF_DIR=$(mktemp -d)
git clone --depth=1 --branch=master https://github.com/batfish/batfish ${BF_DIR}
mvn -f ${BF_DIR}/projects package
cp ${BF_DIR}/projects/allinone/target/allinone-bundle-*.jar workspace/allinone.jar
cp -r ${BF_DIR}/questions workspace/questions
