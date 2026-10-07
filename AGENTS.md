# AGENTS.md

Guidance for coding agents working in this repository.

## Before starting a task

1. Read `DEVELOPMENT.md` for setup, testing, and formatting; read
   `docs/README.md` when changing documentation.
2. Look for similar existing code and tests and follow their patterns.

## Repository layout

- `pybatfish/client/` - `Session` and REST client for the Batfish service
- `pybatfish/question/` - Question template loading and parameter
  validation
- `pybatfish/datamodel/` - Answer and primitive data types
- `pybatfish/mcp/` - MCP server exposing Batfish as tools
- `tests/` - Unit tests; `tests/integration/` needs a running service
- `docs/` - Sphinx user docs (`docs/source`) and question doc
  generation (`docs/nb_gen`)
- `jupyter_notebooks/` - Public example notebooks, executed in tests

## Commands

- `pip install -e .[dev]`
- `pytest tests` - unit tests (excludes `tests/integration`)
- `pytest tests/integration` - integration tests (needs Batfish service)
- `ruff check --fix . && ruff format .`
- `mypy pybatfish tests`

## Rules

- Integration tests that depend on new Batfish or Pybatfish functionality
  must be gated with `@requires_bf("<release date>")`. See "Adding
  tests" in `DEVELOPMENT.md`.
- Questions and new variable types often need matching changes in the
  Batfish repo (`questions/` and the Java question classes).
