## Developer info

### First steps

#### Setup a virtual environment
For this purpose, you will likely want [virtualenv](https://virtualenv.pypa.io/en/stable/) or [Anaconda](https://www.anaconda.com/download/)

#### Installing in development mode
Run `pip install -e .[dev]`

This installs all the development and test dependencies.

### Repository layout

- `pybatfish/client/` - `Session` and REST client for the Batfish service
- `pybatfish/question/` - Question template loading and parameter
  validation
- `pybatfish/datamodel/` - Answer and primitive data types
- `pybatfish/mcp/` - MCP server exposing Batfish as tools
- `tests/` - Unit tests; `tests/integration/` needs a running service
- `docs/` - Sphinx user docs (`docs/source`) and question doc
  generation (`docs/nb_gen`)
- `jupyter_notebooks/` - Public example notebooks, executed in tests

New questions and question variable types usually need matching changes in
the Batfish repo (`questions/` and the Java question classes).

### Running tests

| Command | Needs Batfish service | What it covers |
| --- | --- | --- |
| `pytest tests` | No | Unit tests (`tests/integration` is excluded by `addopts` in `pyproject.toml`) |
| `pytest tests/integration` | Yes | End-to-end tests against a running service |
| `pytest docs` | Yes | Generated question docs and public notebooks |
| `pytest pybatfish --doctest-modules` | Yes | Docstring examples |

CI builds the Batfish allinone JAR from Batfish HEAD and runs the service with:

```
java -cp allinone.jar org.batfish.allinone.Main -runclient false \
  -coordinatorargs '-templatedirs questions -periodassignworkms=5'
```

where `questions` is the `questions/` directory of the Batfish repo.

`pytest docs` and `tests/integration/test_notebook.py` execute notebooks and
compare outputs. On mismatch they write `*.testout` files next to the source;
review the diff and copy the `.testout` over the original when the change in
Batfish output is expected.

### Adding tests

The `batfish/docker` repo runs `tests/integration` against combinations of
released Batfish and Pybatfish versions, not only HEAD. An integration test
that needs functionality added to either Batfish or Pybatfish must be gated on
the first release that will contain it, or release tests fail against older
versions.

Release versions are dates (`2026.10.6`). Dev versions start with `0` (e.g.,
`0.36.0`) and are treated as newer than any release.

Gate a test with `requires_bf` from `tests/common_util.py`, using the date the
required change merged (or later):

```python
from tests.common_util import requires_bf


@requires_bf("2026.10.6")
def test_something_new(bf: Session) -> None:
    ...
```

The test is skipped if either the Batfish or the Pybatfish version is older
than the given version. The Batfish version comes from the `bf_version`
environment variable or from the `Session` fixture passed to the test; the
Pybatfish version comes from `pybf_version` or `pybatfish.__version__`.

Pybatfish names that do not exist in older releases must be imported inside
the gated test, not at module level, so the module still imports when run with
an older Pybatfish:

```python
@requires_bf("2026.10.6")
def test_something_new(bf: Session) -> None:
    # Import locally to avoid import errors versus older Pybatfish
    from pybatfish.client.session import new_thing
    ...
```

For a whole module, call `skip_old_version` from a fixture instead (see
`tests/integration/test_mcp_server.py`). Notebook tests use
`notebook_min_versions` in `tests/integration/test_notebook.py`.

### Code formatting and type checking

Formatting and linting use [ruff](https://docs.astral.sh/ruff/):

- `ruff check --fix .`
- `ruff format .`

Type checking: `mypy pybatfish tests`

CI runs `pre-commit run --all-files` and `mypy pybatfish tests`; see
`.github/workflows/reusable-precommit.yml`.

#### Pre-commit hooks

Optionally, you can install a pre-commit hook that will help with code formatting as well.

1. `pip install pre-commit`
2. `pre-commit install`

This will allow execution of formatting/validation/cleanup before committing code.
Commit will fail if you have badly formatted files. They will be fixed automatically. Add them, commit again.

[More docs on pre-commit](https://pre-commit.com/#usage)

### Building documentation

See [docs/README.md](docs/README.md).

### Creating a distribution

Run `python -m build`. This will create both a wheel package and a source
distribution inside the `dist` folder. These artifacts can be used for releases
or the wheel can be distributed and then installed later using `pip`.
For example:

`pip install ./dist/pybatfish-<version>-py3-none-any.whl`
