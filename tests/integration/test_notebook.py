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
from os.path import abspath, dirname, join, pardir, realpath

from nbconvert.preprocessors import ExecutePreprocessor
import nbformat
import pytest
from six import PY3

_this_dir = abspath(dirname(realpath(__file__)))
_root_dir = abspath(join(_this_dir, pardir, pardir))
_jupyter_nb_dir = join(_root_dir, 'jupyter_notebooks')


@pytest.fixture(scope='module')
def notebook():
    # TODO need to figure out a way to cleanup initialized snapshot(s)
    return nbformat.read(
        join(_jupyter_nb_dir, 'Getting started with Batfish.ipynb'),
        as_version=4)


@pytest.fixture(scope='module')
def executed_notebook():
    notebook = nbformat.read(
        join(_jupyter_nb_dir, 'Getting started with Batfish.ipynb'),
        as_version=4)
    # Run all cells in the notebook, with a time bound, continuing on errors
    ep = ExecutePreprocessor(timeout=60, allow_errors=True,
                             kernel_name="python3" if PY3 else "python2")
    ep.preprocess(notebook, resources={})
    return notebook


def _assert_cell_no_errors(c):
    """Asserts that the given cell has no error outputs."""
    if c['cell_type'] != 'code':
        return
    errors = ["Error name: {}, Error Value: {}".format(o["ename"], o["evalue"])
              for o in c['outputs'] if o['output_type'] == 'error']

    assert not errors, errors


def test_notebook_no_errors(executed_notebook):
    """Asserts that the given notebook has no cells with error outputs."""
    for c in executed_notebook['cells']:
        _assert_cell_no_errors(c)


def test_notebook_output(notebook, executed_notebook):
    for cell, executed_cell in zip(notebook['cells'],
                                   executed_notebook['cells']):
        assert cell['cell_type'] == executed_cell['cell_type']
        if cell['cell_type'] == 'code':
            # Collecting all outputs of type "execute_result" as other output type may be undeterministic (like timestamps)
            original_outputs = [o['data'] for o in cell['outputs'] if
                                o['output_type'] == 'execute_result']
            executed_outputs = [o['data'] for o in executed_cell['outputs'] if
                                o['output_type'] == 'execute_result']
            assert original_outputs == executed_outputs
