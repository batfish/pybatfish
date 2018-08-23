from os import walk
from os.path import abspath, dirname, join, realpath

from nbconvert.preprocessors import ExecutePreprocessor
import nbformat
from six import PY3

_this_dir = abspath(dirname(realpath(__file__)))

notebook_files = [
    join(root, filename)
    for root, dirs, files in walk(_this_dir)
    for filename in files
    if '.ipynb_checkpoints' not in root and filename.endswith('.ipynb')
]

for notebook_file in notebook_files:
    with open(notebook_file) as f:
        nb = nbformat.read(f, as_version=4)
        ep = ExecutePreprocessor(timeout=60, allow_errors=True,
                                 kernel_name="python3" if PY3 else "python2")
        ep.preprocess(nb,
                      resources={'metadata': {'path': dirname(notebook_file)}})
        with open('{}.testout'.format(notebook_file), 'w') as f:
            nbformat.write(nb, f)
