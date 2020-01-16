# coding: utf-8

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
import hashlib
import os
from os.path import abspath, dirname, realpath
from pathlib import Path

import pytest
import requests

# Note that notebooks are tested in test_notebook.py
_this_dir = Path(abspath(dirname(realpath(__file__))))
_root_dir = _this_dir.parent.parent


def test_specifiers_up_to_date():
    original = requests.get(
        "https://raw.githubusercontent.com/batfish/batfish/master/questions/Parameters.md"
    ).content
    doc_source_dir = Path(_root_dir) / "docs" / "source"
    checked_in = doc_source_dir / "specifiers.md"
    outfile = doc_source_dir / "specifiers.md.testout"
    if outfile.exists():
        os.remove(outfile)
    if (
        hashlib.sha256(original).hexdigest()
        != hashlib.sha256(checked_in.read_bytes()).hexdigest()
    ):
        with open(outfile, "wb") as f:
            f.write(original)
        raise AssertionError("Checked in specifiers.md file is outdated.")
