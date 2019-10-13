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

from pybatfish.datamodel.answer.base import (
    _get_base_schema,
    _is_iterable_schema,
    _parse_json_with_schema,
)


def test_get_display_value_self_describing_object():
    """Check that SelfDescribingObject is displayed correctly."""
    json_object = json.loads('{"schema" : "Integer", "value": 23}')
    assert _parse_json_with_schema("SelfDescribing", json_object) == 23

    json_object = json.loads('{"schema" : "Integer"}')
    assert _parse_json_with_schema("SelfDescribing", json_object) is None


def test_get_display_value_integer():
    """Check that Integer values are extracted correctly."""
    assert _parse_json_with_schema("Integer", "0") == 0
    assert _parse_json_with_schema("Integer", 0) == 0
    assert _parse_json_with_schema("Integer", -1) == -1
    assert _parse_json_with_schema("Integer", "-1") == -1


def test_get_display_value_unknown_schema():
    """Check that Integer values are extracted correctly."""
    assert _parse_json_with_schema("bogus", None) is None
    json_object = json.loads('{"foo" : 23}')
    assert _parse_json_with_schema("bogus", json_object) == json_object


def test_is_iterable_schema():
    """Check detection of iterable schemas."""
    assert not _is_iterable_schema("x")
    assert not _is_iterable_schema("")
    assert not _is_iterable_schema("Integer")
    assert not _is_iterable_schema("None")
    assert _is_iterable_schema("List<Integer>")
    assert _is_iterable_schema("List<None>")
    assert _is_iterable_schema("Set<String>")
    assert _is_iterable_schema("set<String>")
    assert _is_iterable_schema("list<acltrace>")
    with pytest.raises(TypeError):
        assert not _is_iterable_schema(None)

    with pytest.raises(TypeError):
        assert not _is_iterable_schema(100)


def test_get_base_schema():
    """Test extraction of base schema."""
    assert _get_base_schema("List<Integer>") == "Integer"
    assert _get_base_schema("Set<Integer>") == "Integer"
    assert _get_base_schema("List<List<List<String>>>") == "List<List<String>>"
    assert _get_base_schema(_get_base_schema("List<Set<string>>")) == "string"

    # Invalid inputs don't crash, just return the original value
    assert _get_base_schema("invalid") == "invalid"
    assert _get_base_schema("Integer") == "Integer"


if __name__ == "__main__":
    pytest.main()
