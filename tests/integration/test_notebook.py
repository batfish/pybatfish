from os.path import abspath, join, realpath, pardir, dirname
from os import walk

import nbformat
import pytest
from nbconvert.preprocessors import ExecutePreprocessor
from six import PY3

_this_dir = abspath(dirname(realpath(__file__)))
_root_dir = abspath(join(_this_dir, pardir, pardir))
_jupyter_nb_dir = join(_root_dir, 'jupyter_notebooks')


@pytest.fixture(scope='module')
def notebook():
    for root, dirs, files in walk(_jupyter_nb_dir):
        for f in files:
            if f.endswith(".ipynb"):
                yield nbformat.read(join(root, f), as_version=4)


@pytest.fixture(scope='module')
def executed_notebook(notebook):
    # Run all cells in the notebook, with a time bound, continuing on errors
    ep = ExecutePreprocessor(timeout=60, allow_errors=True, kernel_name="python3" if PY3 else "python2")
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
    for cell, executed_cell in zip(notebook['cells'], executed_notebook['cells']):
        assert cell['cell_type'] == executed_cell['cell_type']
        if cell['cell_type'] == 'code':
            # Collecting all outputs of type "execute_result" as other output type may be undeterministic (like timestamps)
            original_outputs = [o['data'] for o in cell['outputs'] if o['output_type'] == 'execute_result']
            executed_outputs = [o['data'] for o in executed_cell['outputs'] if o['output_type'] == 'execute_result']
            assert original_outputs == executed_outputs
