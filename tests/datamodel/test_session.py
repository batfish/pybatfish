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

import pytest

from pybatfish.client.session import _create_single_file_zip


def _files(dir):
    ret = []
    for root, _, filenames in os.walk(dir):
        for f in filenames:
            if f != '.lock':  # void pytest lock files
                ret.append(os.path.join(root, f))
    return ret


def test_create_single_file_zip_basic(tmp_path):
    """Creates the expected directory structure in default config."""
    text = "abcdefgh\n"
    path = str(tmp_path)
    _create_single_file_zip(path, text, 'config', None)

    filename = os.path.join(path, 'configs', 'config')
    assert _files(path) == [filename]
    with open(filename, 'r') as infile:
        assert infile.read() == text


def test_create_single_file_zip_platform(tmp_path):
    """Creates the expected file text with provided platform."""
    text = "abcdefgh\n"
    path = str(tmp_path)
    _create_single_file_zip(path, text, 'config', 'arista')

    filename = os.path.join(path, 'configs', 'config')
    assert _files(path) == [filename]
    with open(filename, 'r') as infile:
        assert infile.read() == '!RANCID-CONTENT-TYPE: arista\n' + text


def test_create_single_file_zip_custom_platform(tmp_path):
    """Creates the expected file text with provided poorly typed platform."""
    text = "abcdefgh\n"
    path = str(tmp_path)
    _create_single_file_zip(path, text, 'config', ' aRiStA \t')

    filename = os.path.join(path, 'configs', 'config')
    assert _files(path) == [filename]
    with open(filename, 'r') as infile:
        assert infile.read() == '!RANCID-CONTENT-TYPE: arista\n' + text


def test_create_single_file_zip_custom_filename(tmp_path):
    """Creates the expected file text in the expected filename."""
    text = "abcdefgh\n"
    path = str(tmp_path)
    _create_single_file_zip(path, text, 'somefile', None)

    filename = os.path.join(path, 'configs', 'somefile')
    assert _files(path) == [filename]
    with open(filename, 'r') as infile:
        assert infile.read() == text


if __name__ == "__main__":
    pytest.main()
