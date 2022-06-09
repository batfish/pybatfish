# coding=utf-8
#   Copyright 2018 The Batfish Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
import io
import logging
import os
import re
import sys
from copy import deepcopy
from os import remove, walk
from os.path import abspath, dirname, join, realpath
from pathlib import Path
from typing import Any, List, Mapping, NamedTuple

import nbformat
import pytest
from nb_gen.gen_question_notebooks import (
    NETWORK_NAME,
    generate_notebook,
    get_name_to_qclass,
    init_snapshots,
)
from nbconvert.preprocessors import ExecutePreprocessor
from nbformat import NotebookNode

from pybatfish.client.session import Session

logging.getLogger("pybatfish").setLevel(logging.WARN)

_this_dir = Path(abspath(dirname(realpath(__file__))))
_repo_root = _this_dir.parent.parent
_jupyter_nb_dir = _this_dir.parent / "source" / "notebooks"
_linked_nb_dir = _jupyter_nb_dir / "linked"
_public_nb_dir = _repo_root / "jupyter_notebooks"


def cleanup_testout_files(top_dirs):
    for top_dir in top_dirs:
        for root, dirs, files in walk(top_dir):
            for filename in files:
                if filename.endswith(".testout"):
                    remove(join(root, filename))


cleanup_testout_files([_jupyter_nb_dir])
_check_cell_types = ["execute_result", "display_data"]


class NotebookInfo(NamedTuple):
    path: Path
    generated: bool


class RenderedNotebook(NamedTuple):
    path: Path
    original: NotebookNode
    rendered: NotebookNode


def find_notebooks() -> List[NotebookInfo]:
    """Find Jupyter notebooks that are documented.

    Only some notebooks are auto-generated by gen_question_notebooks."""
    notebooks: List[NotebookInfo] = []
    not_generated = {"interacting", "references"}
    for root, dirs, files in walk(_jupyter_nb_dir, topdown=True):
        if ".ipynb_checkpoints" in dirs:
            dirs.remove(".ipynb_checkpoints")  # do not walk checkpoint dirs
        # do not test linked notebooks. Tested in main code tests.
        if "linked" in dirs:
            dirs.remove("linked")
        for filename in files:
            if not filename.endswith(".ipynb"):
                continue
            path = Path(join(root, filename))
            generated = path.stem not in not_generated
            notebooks.append(NotebookInfo(path=path, generated=generated))
    if not notebooks:
        pytest.fail("No notebook files collected")
    return notebooks


DISCOVERED_NOTEBOOKS = find_notebooks()


@pytest.fixture(scope="module")
def snapshots(session: Session, categories: Mapping[str, Any]) -> None:
    """Initializes all snapshots needed for generating doc notebooks."""
    session.set_network(NETWORK_NAME)
    init_snapshots(categories, session)


@pytest.fixture(scope="module", params=DISCOVERED_NOTEBOOKS)
def rendered_nb(
    request: Any, categories: Mapping[str, Any], session: Session, snapshots: None
) -> RenderedNotebook:
    """
    Reads in the notebook and renders its new form.

    A generated notebook is generated before execution.
    """
    nb_info: NotebookInfo = request.param

    with nb_info.path.open() as f:
        original_nb = nbformat.read(f, as_version=4)

    if nb_info.generated:
        # We will not execute the original notebook; instead we re-generate
        # it and then execute it.
        category_matches = [
            c for c in categories["categories"] if c["name"] == nb_info.path.stem
        ]
        assert len(category_matches) == 1
        category = category_matches[0]
        nb_to_execute = generate_notebook(
            category, get_name_to_qclass(session), session
        )
    else:
        # Make a deep copy of the original notebook.
        # - This is important or else the underlying object gets mutated!!
        nb_to_execute = deepcopy(original_nb)

    # Run all cells in the notebook, with a time bound, continuing on errors
    exec_path = nb_info.path.parent
    ep = ExecutePreprocessor(timeout=60, allow_errors=True, kernel_name="python3")
    ep.preprocess(nb_to_execute, resources={"metadata": {"path": exec_path}})

    # Clear undesirable metadata from cells
    keep_metadata = {"nbsphinx"}
    for cell in nb_to_execute.cells:
        if "metadata" not in cell:
            continue
        meta = cell["metadata"]
        cell["metadata"] = {k: v for k, v in meta.items() if k in keep_metadata}

    return RenderedNotebook(
        path=nb_info.path, original=original_nb, rendered=nb_to_execute
    )


def _assert_cell_no_errors(c):
    """Asserts that the given cell has no error outputs."""
    if c["cell_type"] != "code":
        return
    errors = [
        "Error name: {}, Error Value: {}, trace: {}".format(
            o["ename"], o["evalue"], "\n".join(o.get("traceback"))
        )
        for o in c["outputs"]
        if o["output_type"] == "error"
    ]

    if errors:
        pytest.fail("Found notebook errors: {}".format("\n".join(errors)))


def _compare_data_str(text1, text2):
    assert text1.splitlines() == text2.splitlines()


def _compare_data(original_data, executed_data):
    assert ("text/plain" in original_data) == ("text/plain" in executed_data)
    assert ("text/html" in original_data) == ("text/html" in executed_data)

    if sys.version_info[:2] < (3, 6):
        # Output is inconsistent across versions, so only test latest.
        # (We still test the notebook runs without errors on all versions)
        return
    if "text/plain" in original_data:
        _compare_data_str(original_data["text/plain"], executed_data["text/plain"])
    if "text/html" in original_data and "text/html" in executed_data:
        _compare_data_str(original_data["text/html"], executed_data["text/html"])


def test_notebook_no_errors(rendered_nb: RenderedNotebook):
    """Asserts that the given notebook has no cells with error outputs."""
    for c in rendered_nb.rendered["cells"]:
        _assert_cell_no_errors(c)


def test_notebook_code_output(rendered_nb: RenderedNotebook):
    """Test the output code cells have not changed."""
    try:
        for cell, executed_cell in zip(
            rendered_nb.original["cells"], rendered_nb.rendered["cells"]
        ):
            assert cell["cell_type"] == executed_cell["cell_type"]
            if cell["cell_type"] == "code":
                # Collecting all outputs of type "execute_result" as other output type may be undeterministic (like timestamps)
                original_outputs = [
                    o["data"]
                    for o in cell["outputs"]
                    if o["output_type"] in _check_cell_types
                ]
                executed_outputs = [
                    o["data"]
                    for o in executed_cell["outputs"]
                    if o["output_type"] in _check_cell_types
                ]
                assert len(original_outputs) == len(executed_outputs)
                for original_data, executed_data in zip(
                    original_outputs, executed_outputs
                ):
                    _compare_data(original_data, executed_data)
    except AssertionError as e:
        with io.open("{}.testout".format(rendered_nb.path), "w", encoding="utf-8") as f:
            nbformat.write(rendered_nb.rendered, f)
            pytest.fail(
                "{} failed output validation:\n{}".format(rendered_nb.path, e),
                pytrace=False,
            )


def test_notebook_execution_count(rendered_nb: RenderedNotebook):
    """Test the notebook has been executed in order"""
    nb = rendered_nb.rendered
    code_cells = [cell for cell in nb["cells"] if cell["cell_type"] == "code"]
    for (i, cell) in enumerate(code_cells):
        assert (
            i + 1 == cell["execution_count"]
        ), "Expected cell {} to have execution count {}".format(cell, i + 1)


def test_markdown_up_to_date(rendered_nb: RenderedNotebook):
    """Test that markdown cells are up-to-date."""
    checked_in = rendered_nb.original
    fresh = rendered_nb.rendered
    try:
        for fresh_cell, checked_in_cell in zip(fresh["cells"], checked_in["cells"]):
            assert fresh_cell["cell_type"] == checked_in_cell["cell_type"]
            if fresh_cell["cell_type"] != "markdown":
                continue
            _compare_data_str(fresh_cell["source"], checked_in_cell["source"])
    except AssertionError as e:
        with io.open("{}.testout".format(rendered_nb.path), "w", encoding="utf-8") as f:
            nbformat.write(fresh, f)
            pytest.fail(
                "{} failed output validation:\n{}".format(rendered_nb.path, e),
                pytrace=False,
            )


def test_all_notebooks_linked():
    """Ensure that all public notebooks are linked into docs."""
    assert _public_nb_dir.is_dir()
    assert _linked_nb_dir.is_dir()
    linked_nbs = {f.name for f in _linked_nb_dir.glob("*.ipynb")}
    new_links = []
    for f in _public_nb_dir.glob("*.ipynb"):
        linked_name = get_symlink_name(f)
        if linked_name not in linked_nbs:
            cwd = os.getcwd()
            os.chdir(str(_linked_nb_dir))
            os.symlink(
                f"../../../../jupyter_notebooks/{f}",
                linked_name,
                target_is_directory=False,
            )
            os.chdir(cwd)
            new_links.append(str(_linked_nb_dir / linked_name))
    if new_links:
        ll = "\n".join(new_links)
        pytest.fail(f"Please commit the following notebook symlinks:\n{ll}")


def get_symlink_name(f: Path) -> str:
    stripped = (_public_nb_dir / f).stem.lower().replace("(", "").replace(")", "")
    linked_name = re.sub(r"\s+", "-", stripped) + ".ipynb"
    return linked_name
