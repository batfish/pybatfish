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


### Adding tests
Adding integration tests exercising new functionality requires using special annotations to indicate what version of `Batfish` and `Pybatfish` are required in order for pre-deployment cross-version testing to work.

For example, if a new feature is added that is not supported by `Batfish` / `Pybatfish` until 2019/11/05, then `Pybatfish` integration tests exercising this functionality should be annotated like this:
```
@requires_bf('2019.11.05')
def test_something_new(session):
    ...
```
This annotation causes the test to run only if `Pybatfish` and `Batfish` versions are greater than or equal to `2019.11.05` or are dev versions (starting with `0`, e.g. `0.36.0`).

Also make sure that `Pybatfish` imports that did not exist in older versions of `Pybatfish` must be imported locally to avoid import errors when run against older versions, e.g.
```
@requires_bf('2019.11.05')
def test_something_new(session):
    # Import locally to avoid import errors versus older Pybatfish
    from pybatfish.client.session import new_thing
    # Use new_thing
    ...
```

### Code formatting

Non-ambiguous automatic formatting using [black](https://github.com/psf/black#installation).

Run `./fix-format.sh` to format everything automatically.

Instructions for [editor integration](https://black.readthedocs.io/en/stable/editor_integration.html)


#### Pre-commit hooks

Optionally, you can install a pre-commit hook that will help with code formatting as well.

1. `pip install pre-commit`
2. `pre-commit install`

This will allow execution of formatting/validation/cleanup before committing code.
Commit will fail if you have badly formatted files. They will be fixed automatically. Add them, commit again.

[More docs on pre-commit](https://pre-commit.com/#usage)

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
