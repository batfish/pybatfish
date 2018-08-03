## Developer info

## Installing in dev mode 
Run `pip install -e .[dev,test]`

This installs all the development and test dependencies

### Running tests

- To run unit tests execute `python setup.py test`
- To run end-to-end tests, start up an instance of batfish, 
  make it point to `<stable_questions_dir>` (as described above). 
  Make sure there is a symlink to `<batfish_repository_root>/test_rigs` 
  folder under root of the pybatfish repository.

  Run `py.test tests/integration`

### Creating a distribution

Run `python setup.py bdist_wheel`. This will create a wheel package inside the `dist` 
folder suitable for your version of python.
The wheel can be distributed and later installed using `pip`. 
For example:

`pip install ./pybatfish-<version>-py3-none-any.whl`

### Building documentation

1. Ensure pybatfish is installed
2. Ensure sphinx is installed sphinx 
   by running `pip install sphinx sphinx_rtd_theme`

Run:
- `cd docs`
- `make html` (or other format, such as `make pdf`)

Read (for html format):
- Open `docs/build/html/index.html`