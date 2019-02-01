## Developer info

### First steps

#### Setup a virtual environment
For this purpose, you will likely want [virtualenv](https://virtualenv.pypa.io/en/stable/) or [Anaconda](https://www.anaconda.com/download/)

#### Installing in development mode 
Run `pip install -e .[dev]`

This installs all the development and test dependencies.

### Running tests

- To run unit tests execute `python setup.py test`
- To run end-to-end tests, start up an instance of batfish, 
  make it point to `<stable_questions_dir>` (as described above).

  Run `py.test tests/integration`

### Building documentation

1. Ensure pybatfish is installed
2. Ensure sphinx (the RTD theme) is installed by running `pip install sphinx sphinx_rtd_theme`

Run:
- `cd docs`
- `python generate_questions_doc.py`
- `make html` (or other format, such as `make pdf`)

Read (for html format):
- Open `docs/build/html/index.html`

### Creating a distribution

Run `python setup.py bdist_wheel`. This will create a wheel package inside the `dist` 
folder. The wheel can be distributed and later installed using `pip`. 
For example:

`pip install ./pybatfish-<version>-py3-none-any.whl`


