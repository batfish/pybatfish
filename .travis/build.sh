#!/usr/bin/env bash
set -xe

BATFISH_VERSION="$(grep -1 batfish-parent ${TRAVIS_BUILD_DIR}/batfish/projects/pom.xml | grep version | sed -E 's/.*<version>(.*)<\/version>.*/\1/g')"
echo "Using Batfish version ${BATFISH_VERSION}"

if [[ $(uname) == 'Darwin' && $(which gfind) ]]; then
   GNU_FIND=gfind
else
   GNU_FIND=find
fi

if [ -n "$TRAVIS_BUILD_DIR" ]; then
   # Build and install pybatfish
   pip install -e .[dev,test]
   export QUESTIONS_DIR=questions
else
   export QUESTIONS_DIR=../batfish/questions
fi

ALLINONE_JAR=${TRAVIS_BUILD_DIR}/batfish/projects/allinone/target/allinone-bundle-${BATFISH_VERSION}.jar

# Start this as early as possible so that batfish has time to start up.
if [ -n "$TRAVIS_BUILD_DIR" ]; then
  # Only run allinone during Travis build. For local testing it should be running in background.
  java -cp "$ALLINONE_JAR" org.batfish.allinone.Main -runclient false -coordinatorargs "-templatedirs questions" &
fi

# We can only run mypy using python 3. That's ok.
# Our type annotations are py2-compliant and will be checked by mypy.
if [[ $TRAVIS_PYTHON_VERSION != 2.7 ]]; then
    echo -e "\n  ..... Running mypy typechecker on pybatfish"
    mypy pybatfish
    mypy --py2 pybatfish
fi

echo -e "\n  ..... Running flake8 on pybatfish to check style and docstrings"
# Additional configuration in setup.cfg
flake8 pybatfish,tests

echo -e "\n  ..... Running flake8 on jupyter notebooks"
# Running flake test on generated python script from jupyter notebook(s)
for file in jupyter_notebooks/*.ipynb; do
    jupyter nbconvert "$file" --to python --stdout --TemplateExporter.exclude_markdown=True | flake8 - --ignore=E501,W391,D100,F403,F405,F821
done


### Run unit tests that don't require running instance of batfish
echo -e "\n  ..... Running unit tests with pytest"
python setup.py test

#### Running integration tests (require batfish)
echo -e "\n  ..... Running python ref tests with batfish"
retcode=0
py.test tests/integration || retcode=$?

exit ${retcode}
