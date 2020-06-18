# Doc generation

This folder contains sources needed to generate pybatfish docs.
Documentation is generated from multiple sources using sphinx (and its extensions):

* Markdown/RST files
* Scripts + notebooks that document pybf questions (by generating more notebooks)
* Inlining public jupyter notebooks

## For developers

### Documenting questions

1. Add the new question to an appropriate category in `docs/nb_gen/questions.yaml`

    1. If the question needs a special snapshot or special parameters, set them.
       See `searchFilters` question as an example.
    2. Put any required snapshots in `docs/networks`

2. If you are adding a new question category, make sure to include it in `docs/source/questions.rst`

### Generating documentation

1. Start batfish service
2. If you haven't done this before, make sure you have all requirements installed.
   From root of the repo:

   * `pip install -r requirements.txt`
   * `pip install -r docs/requirements.txt`
   * `brew install pandoc`

3. From `docs` folder, run:

   `python -m nb_gen`

### Running tests, updating docs

1. Run `pytest docs`
2. Some test failures will tell you what to do
   (e.g., what symlinks to commit or will generate `*.testout` file to update the notebooks)
