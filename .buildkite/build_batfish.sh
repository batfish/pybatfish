#!/usr/bin/env bash

set -euxo pipefail

BF_DIR=$(mktemp -d)
git clone --depth=1 --branch=master https://github.com/batfish/batfish ${BF_DIR}
mvn -f ${BF_DIR}/batfish/projects package
cp ${BF_DIR}/batfish/projects/allinone/target/allinone-bundle-*.jar workspace/allinone.jar
