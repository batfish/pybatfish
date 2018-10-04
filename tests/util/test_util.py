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
import json

import pytest

from pybatfish.datamodel import Interface
from pybatfish.exception import QuestionValidationException
from pybatfish.util import (BfJsonEncoder, conditional_str, escape_html,
                            validate_name, validate_question_name)


def test_conditional_str():
    prefix = 'pre'
    suffix = 'after'
    s = conditional_str(prefix, [], suffix)
    assert s == ""
    s = conditional_str(prefix, {}, suffix)
    assert s == ""
    s = conditional_str(prefix, set(), suffix)
    assert s == ""
    s = conditional_str(prefix, None, suffix)
    assert s == ""
    s = conditional_str(prefix, [{}], suffix)
    assert s == "pre [{}] after"
    s = conditional_str(prefix, ['hey'], suffix)
    assert s == "pre ['hey'] after"


def test_validate_name():
    assert validate_name('goodname')
    for name in [42, 'x' * 151, '/', '/etc', 'seTTings', 'settings', ".",
                 "../../../../etc/"]:
        with pytest.raises(ValueError):
            assert validate_name(name)

    for name in ["23", '___', 'foo-bar']:
        validate_name(name)


def test_validate_question_name():
    assert validate_name('goodname')
    for name in [42, 'x' * 151, '/', '/etc']:
        with pytest.raises(QuestionValidationException):
            assert validate_question_name(name)


def test_encoder_with_primitives():
    encoder = BfJsonEncoder()
    assert encoder.default(1) == 1
    assert encoder.default(3.14) == 3.14
    assert encoder.default("some_string") == "some_string"
    assert encoder.default([1, 2, "some_string"]) == [1, 2, "some_string"]
    assert encoder.default({1})
    assert encoder.default(None) is None
    assert json.dumps(
        {"name": {"nested": "foo"}}, cls=BfJsonEncoder) == json.dumps(
        {"name": {"nested": "foo"}})
    assert json.dumps([{'name': 'value'}], cls=BfJsonEncoder) == json.dumps(
        [{'name': 'value'}])


def test_encoder_with_datamodel_element():
    encoder = BfJsonEncoder()

    iface = Interface(hostname='node', interface="iface")
    assert encoder.default(iface) == iface.dict()

    assert json.dumps(
        {"name": {"nested": iface}}, cls=BfJsonEncoder) == json.dumps(
        {"name": {"nested": iface.dict()}})


def test_encoder_invalid_input():
    class NonSerializable(object):
        x = 100

    with pytest.raises(TypeError):
        assert json.dumps(NonSerializable())


def test_escape_html():
    assert escape_html('') == ''
    assert escape_html('a') == 'a'
    assert escape_html('"a"') == '&quot;a&quot;'
    assert escape_html('a&b') == 'a&amp;b'
    assert escape_html('a & b') == 'a &amp; b'
