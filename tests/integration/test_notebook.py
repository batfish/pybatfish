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
import re
import sys
from copy import deepcopy
from os import remove, walk
from os.path import abspath, dirname, join, pardir, realpath

import nbformat
import pytest
from nbconvert.preprocessors import ExecutePreprocessor

from pybatfish.client.session import Session
from tests.common_util import get_bf_version, skip_old_version

_this_dir = abspath(dirname(realpath(__file__)))
_root_dir = abspath(join(_this_dir, pardir, pardir))
_jupyter_nb_dir = join(_root_dir, "jupyter_notebooks")

notebook_files = [
    join(root, filename)
    for root, dirs, files in walk(_jupyter_nb_dir)
    for filename in files
    if ".ipynb_checkpoints" not in root and filename.endswith(".ipynb")
]
# Map of notebook name (substring) to minimum Pybf/Bf version required to run it
# A special key of "*" means version requirement applies to all notebooks
ANY_NOTEBOOK = "*"
notebook_min_versions = {ANY_NOTEBOOK: "2020.11.12"}

for root, dirs, files in walk(_jupyter_nb_dir):
    for filename in files:
        if filename.endswith(".testout"):
            remove(join(root, filename))

assert len(notebook_files) > 0

_check_cell_types = ["execute_result", "display_data"]


@pytest.fixture(scope="module")
def bf_version():
    s = Session()
    return get_bf_version(s)


@pytest.fixture(scope="module", params=notebook_files)
def notebook(request):
    filepath = request.param
    return filepath, nbformat.read(filepath, as_version=nbformat.NO_CONVERT)


def skip_new_notebook_vs_old_code(bf_version, notebook_name):
    """Skip this pytest test if version of Pybf and Bf are too old to run it."""
    for key in notebook_min_versions:
        if key == ANY_NOTEBOOK or key in notebook_name:
            skip_old_version(bf_version, notebook_min_versions.get(key))


def _is_warning_output(o):
    WARN_STRING = "UserWarning: Pybatfish public API is being updated"
    return o.get("name", "") == "stderr" and WARN_STRING in o.get("text", "")


@pytest.fixture(scope="module")
def executed_notebook(notebook):
    filepath, orig_nb = notebook
    filepath, nb = notebook  # Make a deep copy of the original notebook.
    # - This is important or else the underlying object gets mutated!!
    nb = deepcopy(orig_nb)
    exec_path = dirname(filepath)
    # Run all cells in the notebook, with a time bound, continuing on errors
    ep = ExecutePreprocessor(timeout=60, allow_errors=True, kernel_name="python3")
    ep.preprocess(nb, resources={"metadata": {"path": exec_path}})

    for cell in nb["cells"]:
        # Filter out the deprecation warning, if it exists
        outputs = [o for o in cell.get("outputs", []) if not _is_warning_output(o)]
        if len(outputs) != len(cell.get("outputs", [])):
            cell["outputs"] = outputs

        # Clear metadata like execution timestamp
        for cell in nb.cells:
            cell["metadata"] = {}

    return nb


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


def test_notebook_version_matrix():
    """Meta test to confirm notebook version matrix is valid."""
    # Make sure each version matrix entry corresponds to a notebook filename
    for k in notebook_min_versions:
        assert k == ANY_NOTEBOOK or any(
            k in name for name in notebook_files
        ), "'{}' does not refer to any notebook filename".format(k)


def test_notebook_no_errors(bf_version, notebook, executed_notebook):
    """Asserts that the given notebook has no cells with error outputs."""
    filepath, _ = notebook
    skip_new_notebook_vs_old_code(bf_version, filepath)
    for c in executed_notebook["cells"]:
        _assert_cell_no_errors(c)


def test_notebook_output(bf_version, notebook, executed_notebook):
    filepath, nb = notebook
    skip_new_notebook_vs_old_code(bf_version, filepath)
    try:
        for cell, executed_cell in zip(nb["cells"], executed_notebook["cells"]):
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
        with io.open("{}.testout".format(filepath), "w", encoding="utf-8") as f:
            nbformat.write(executed_notebook, f)
            pytest.fail(
                "{} failed output validation:\n{}".format(filepath, e), pytrace=False
            )


def test_notebook_execution_count(notebook):
    _, nb = notebook
    code_cells = [cell for cell in nb["cells"] if cell["cell_type"] == "code"]
    for i, cell in enumerate(code_cells):
        assert (
            i + 1 == cell["execution_count"]
        ), "Expected cell {} to have execution count {}".format(cell, i + 1)


def test_absolute_links(notebook):
    """Test that all links in markdown cells are absolute links."""
    _, nb = notebook
    markdown_cells = [cell for cell in nb["cells"] if cell["cell_type"] == "markdown"]
    for cell in markdown_cells:
        assert not re.search(r"\[.*\]\((?!http).*", cell["source"])
