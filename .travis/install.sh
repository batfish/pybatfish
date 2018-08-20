#!/usr/bin/env bash

set -x -e

#### Before we begin, install Z3 for Ubuntu 14.04
Z3_INSTALL_URL="https://raw.githubusercontent.com/batfish/batfish/master/tools/install_z3_ubuntu.sh"
Z3_CMD_NAME=$(basename ${Z3_INSTALL_URL})
wget ${Z3_INSTALL_URL}
sudo bash ${Z3_CMD_NAME} /usr

#### Next, install the correct version of Batfish -- either from a branch or TAG
if [[ ${TRAVIS_BRANCH} =~ ^release.* ]]; then
   BATFISH_BRANCH="$(echo ${TRAVIS_BRANCH} | sed -E 's/(release-[0-9]+\.[0-9]+).*/\1/')"
else
   BATFISH_BRANCH=master
fi
 
#### Checkout and install batfish
git clone --depth=1 --branch=${BATFISH_BRANCH} https://github.com/batfish/batfish $TRAVIS_BUILD_DIR/batfish
pushd "$TRAVIS_BUILD_DIR/batfish/projects"
mvn clean install
popd 

# Symlink batfish testrigs to make them available to pybatfish
ln -s "$TRAVIS_BUILD_DIR/batfish/networks" $TRAVIS_BUILD_DIR


if [[ $TRAVIS_OS_NAME == 'linux' ]]; then
   ### install python packages
   echo -e "\n   ............. Installing pip"
   sudo -H apt-get -y install python-pip || exit 1
   pip --version || exit 1
elif [[ $TRAVIS_OS_NAME == 'osx' ]]; then
   brew update || exit 1
   which gfind || brew install findutils || exit 1
   gfind --version || exit 1
   echo $PATH
   export PATH=/usr/local/share/python:$PATH
   java -version || exit 1
   javac -version || exit 1
   which pip || easy_install pip || exit 1
   pip --version || exit 1
else
   echo "Unsupported TRAVIS_OS_NAME: $TRAVIS_OS_NAME"
   exit 1 # CI not supported in this case
fi

#### create symbolic links to stable and experimental questions
ln -s $TRAVIS_BUILD_DIR/batfish/questions .
