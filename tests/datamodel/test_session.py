# coding=utf-8
#   Copyright 2019 The Batfish Open Source Project
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
"""Tests for Session."""

from __future__ import absolute_import, print_function

import os
import zipfile

import pytest

from pybatfish.client.session import _create_in_memory_zip, _text_with_platform


def _files(dir):
    ret = []
    for root, _, filenames in os.walk(dir):
        for f in filenames:
            if f != ".lock":  # void pytest lock files
                ret.append(os.path.join(root, f))
    return ret


def test_create_single_file_zip():
    """Creates the expected zip."""
    text = "abcdefgh\n"
    expected_filename = os.path.join("snapshot", "configs", "myfile")
    expected_text = "!RANCID-CONTENT-TYPE: arista\n" + text

    with zipfile.ZipFile(_create_in_memory_zip(text, "myfile", "arista"), "r") as zf:
        assert zf.namelist() == [expected_filename]
        assert expected_text == zf.read(expected_filename).decode("utf-8")


def test_text_with_platform():
    """Creates the expected file text with provided platform."""
    text = "abcdefgh\n"
    assert text == _text_with_platform(text, None)

    expected_arista = "!RANCID-CONTENT-TYPE: arista\n" + text
    assert expected_arista == _text_with_platform(text, "arista")
    assert expected_arista == _text_with_platform(text, " aRiStA \t")


if __name__ == "__main__":
    pytest.main()
