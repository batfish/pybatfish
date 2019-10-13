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
import os
import zipfile

import pytest

from pybatfish.datamodel import AclTrace, Interface
from pybatfish.exception import QuestionValidationException
from pybatfish.util import (
    BfJsonEncoder,
    conditional_str,
    escape_html,
    escape_name,
    get_html,
    validate_name,
    validate_question_name,
    zip_dir,
)


def test_conditional_str():
    prefix = "pre"
    suffix = "after"
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
    s = conditional_str(prefix, ["hey"], suffix)
    assert s == "pre ['hey'] after"


def test_validate_name():
    assert validate_name("goodname")
    for name in [
        42,
        "x" * 151,
        "/",
        "/etc",
        "seTTings",
        "settings",
        ".",
        "../../../../etc/",
    ]:
        with pytest.raises(ValueError):
            assert validate_name(name)

    for name in ["23", "___", "foo-bar"]:
        validate_name(name)


def test_validate_question_name():
    assert validate_name("goodname")
    for name in [42, "x" * 151, "/", "/etc"]:
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
    assert json.loads(json.dumps({"name": {"nested": "foo"}}, cls=BfJsonEncoder)) == {
        "name": {"nested": "foo"}
    }
    assert json.loads(json.dumps([{"name": "value"}], cls=BfJsonEncoder)) == [
        {"name": "value"}
    ]


def test_encoder_with_datamodel_element():
    encoder = BfJsonEncoder()

    iface = Interface(hostname="node", interface="iface")
    assert encoder.default(iface) == iface.dict()

    assert json.loads(json.dumps({"name": {"nested": iface}}, cls=BfJsonEncoder)) == {
        "name": {"nested": iface.dict()}
    }


def test_encoder_invalid_input():
    class NonSerializable(object):
        x = 100

    with pytest.raises(TypeError):
        assert json.dumps(NonSerializable())


def test_escape_html():
    assert escape_html("") == ""
    assert escape_html("a") == "a"
    assert escape_html('"a"') == "&quot;a&quot;"
    assert escape_html("a&b") == "a&amp;b"
    assert escape_html("a & b") == "a &amp; b"


def test_escape_name():
    assert escape_name("") == ""
    assert escape_name("a") == "a"
    assert escape_name("abc") == "abc"
    assert escape_name('"a') == '""a"'
    assert escape_name("/a") == '"/a"'
    assert escape_name("0a") == '"0a"'
    assert escape_name("a#") == '"a#"'


def test_get_html():
    assert get_html("astring") == "astring"
    assert get_html(1.2) == "1.2"
    assert get_html(100) == "100"
    # Complex object without __str__ implementation, expect repr-like
    assert get_html(AclTrace()) == "AclTrace(events=[])"


def _make_config(directory, filename, file_contents):
    """Write config in specified dir."""
    file_contents = file_contents
    with open(os.path.join(directory, filename), "w+") as f:
        f.write(file_contents)
        f.flush()


def _assert_zip_contents(zip_file, file_sub_path, contents, tmpdir):
    """Assert the specified zip contains the specified subfile and its contents match the specified contents."""
    out_dir_path = str(tmpdir.mkdir("unzipped"))
    with zipfile.ZipFile(zip_file, "r") as f:
        f.extractall(out_dir_path)

    file_path = os.path.join(out_dir_path, file_sub_path)

    assert os.path.exists(file_path)

    with open(file_path, "r") as f:
        assert f.read() == contents


def test_zip_dir(tmpdir):
    """Make sure zipping dir works."""
    dirname = "dirname"
    filename = "filename"
    contents = "file contents"
    in_dir_path = str(tmpdir.mkdir(dirname))
    _make_config(in_dir_path, filename, contents)
    zip_file = str(tmpdir.join("file.zip"))

    zip_dir(in_dir_path, zip_file)

    # Make sure the zip contains the file with the correct contents
    _assert_zip_contents(zip_file, os.path.join(dirname, filename), contents, tmpdir)


def test_zip_dir_bad_file_time(tmpdir):
    """
    Make sure zipping pre-1980 file works - even though zip format doesn't support files that old.

    See issue here https://bugs.python.org/issue34097
    """
    dirname = "dirname"
    filename = "filename"
    contents = "file contents"
    in_dir_path = str(tmpdir.mkdir(dirname))
    _make_config(in_dir_path, filename, contents)
    in_file_path = os.path.join(in_dir_path, filename)
    zip_file = str(tmpdir.join("file.zip"))

    # Set accessed and modified time of file we're about to zip to some time pre-1980
    _1960_01_01 = -315590400.0
    os.utime(in_file_path, (_1960_01_01, _1960_01_01))

    zip_dir(in_dir_path, zip_file)

    # Make sure the zip contains the file with the correct contents
    _assert_zip_contents(zip_file, os.path.join(dirname, filename), contents, tmpdir)
