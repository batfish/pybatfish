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
import re
from os import walk
from os.path import abspath, dirname, join, pardir, realpath

import nbformat
import pytest

_this_dir = abspath(dirname(realpath(__file__)))
_root_dir = abspath(join(_this_dir, pardir))
_jupyter_nb_dir = join(_root_dir, "jupyter_notebooks")

notebook_files = [
    join(root, filename)
    for root, dirs, files in walk(_jupyter_nb_dir)
    for filename in files
    if ".ipynb_checkpoints" not in root and filename.endswith(".ipynb")
]

assert len(notebook_files) > 0


@pytest.fixture(scope="module", params=notebook_files)
def notebook(request):
    """Fixture that provides notebook file paths and parsed notebooks for metadata tests."""
    filepath = request.param
    return filepath, nbformat.read(filepath, as_version=nbformat.NO_CONVERT)


def test_absolute_links(notebook):
    """Test that all links in markdown cells are absolute links."""
    _, nb = notebook
    markdown_cells = [cell for cell in nb["cells"] if cell["cell_type"] == "markdown"]
    for cell in markdown_cells:
        assert not re.search(r"\[.*\]\((?!http).*", cell["source"])
