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

from __future__ import absolute_import, print_function

import pytest

# test if an acl trace is deserialized properly
from pybatfish.datamodel.primitives import FileLines


def test_filelines_multiple_lines():
    filelines = FileLines.from_dict({"filename": "myfile", "lines": [2, 3]})
    assert filelines.filename == "myfile"
    assert filelines.lines == [2, 3]


def test_filelines_no_lines():
    filelines = FileLines.from_dict({"filename": "myfile"})
    assert filelines.filename == "myfile"
    assert len(filelines.lines) == 0


def test_filelines_zero_lines():
    filelines = FileLines.from_dict({"filename": "myfile", "lines": []})
    assert filelines.filename == "myfile"
    assert len(filelines.lines) == 0


if __name__ == "__main__":
    pytest.main()
