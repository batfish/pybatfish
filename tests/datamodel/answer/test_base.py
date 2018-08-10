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
"""Tests for Table answers."""

from __future__ import absolute_import, print_function

import json

import pytest

from pybatfish.datamodel.answer.base import _get_display_value


def test_get_display_value_self_describing_object():
    """Check that SelfDescribingObject is displayed correctly."""
    json_object = json.loads("{\"schema\" : \"Integer\", \"value\": 23}")
    assert _get_display_value('SelfDescribingObject', json_object) == 23


def test_get_display_value_integer():
    """Check that Integer values are extracted correctly."""
    assert _get_display_value('Integer', "0") == 0
    assert _get_display_value('Integer', 0) == 0
    assert _get_display_value('Integer', -1) == -1
    assert _get_display_value('Integer', "-1") == -1


def test_get_display_value_unknown_schema():
    """Check that Integer values are extracted correctly."""
    assert _get_display_value('bogus', None) is None
    json_object = json.loads("{\"foo\" : 23}")
    assert _get_display_value('bogus', json_object) == json_object


if __name__ == "__main__":
    pytest.main()
