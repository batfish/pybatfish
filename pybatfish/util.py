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
"""Generic utility functions for pybatfish."""

from __future__ import absolute_import

import os
import string
import tempfile
import uuid
import zipfile
from collections.abc import Iterable, Mapping
from typing import Any, IO, Sized, Union  # noqa: F401

import simplejson

from pybatfish.exception import QuestionValidationException

# Max length of snapshot/question names.
# Not 255 to accommodate potential folders/extensions, etc.
_MAX_FILENAME_LEN = 150

# Minimum timestamp supported by ZIP format
# See issue https://bugs.python.org/issue34097
_MIN_ZIP_TIMESTAMP = 315561600.0

# Characters that must be escaped in name
# Should be in sync with SPECIAL_CHARS in CommonParser.java
_NAME_SPECIAL_CHARS_ = " \t,\\&()[]@" + "!#$%^;?<>={}"

__all__ = [
    "BfJsonEncoder",
    "conditional_str",
    "escape_html",
    "escape_name",
    "get_html",
    "get_uuid",
    "validate_name",
    "validate_question_name",
    "zip_dir",
]


class BfJsonEncoder(simplejson.JSONEncoder):
    """A default encoder for Batfish question and datamodel objects."""

    def default(self, obj):
        if isinstance(obj, (int, float, bool, str)) or obj is None:
            return obj
        elif isinstance(obj, Mapping):
            return {k: self.default(v) for k, v in obj.items()}
        elif isinstance(obj, Iterable):
            return list(map(self.default, obj))
        else:
            try:
                # Return the dictionary representation, which is supported by
                # questions and datamodel elements
                return self.default(obj.dict())
            except AttributeError:
                # Raise
                super(BfJsonEncoder, self).default(obj)


def conditional_str(prefix, obj, suffix):
    # type: (str, Union[Sized, None], str) -> str
    """
    Return a concatenation of prefix, object and suffix.

    Returns empty string if obj is not "truthy" (i.e., not None or empty
    container)
    """
    return (
        " ".join([prefix, str(obj), suffix]) if obj is not None and len(obj) > 0 else ""
    )


def get_uuid():
    # type: () -> str
    """Generate and return a UUID as a string."""
    return str(uuid.uuid4())


def validate_name(name, entity_type="snapshot"):
    # type: (str, str) -> bool
    """Check if a given snapshot name is valid.

    :param name: name to check
    :type name: str
    :param entity_type: type of name (e.g., network, snapshot, etc.)
    :type name: str
    :return: True if the name is valid
    :raises ValueError if the name is deemed not valid
    """
    _reserved_words = ["settings"]
    _valid_chars = set(string.ascii_letters).union(string.digits).union(["-", "_"])
    try:
        if "/" in name:
            raise ValueError(
                "{} name cannot contain slashes ('/')".format(entity_type.capitalize())
            )
        if len(name) > _MAX_FILENAME_LEN:
            raise ValueError(
                "{} names cannot be longer than {} characters".format(
                    entity_type.capitalize(), _MAX_FILENAME_LEN
                )
            )
        if name.lower() in _reserved_words:
            raise ValueError(
                "'{}' is a reserved word. Please rename the {}".format(
                    name, entity_type
                )
            )
        # Catch all:
        if set(str(name)).difference(_valid_chars):
            raise ValueError("{} is not a valid name for {}".format(name, entity_type))
    except (TypeError, AttributeError):
        raise ValueError(
            "{} name has the wrong type ({}), a string is expected".format(
                entity_type.capitalize(), type(name)
            )
        )
    return True


def validate_question_name(name):
    # type: (str) -> bool
    """Check if a question name is valid.

    :param name: question name
    :type name: str
    :returns True if the question name is valid
    :raises QuestionValidationException if the name is not valid
    """
    try:
        if "/" in name:
            raise QuestionValidationException(
                "Question name cannot contain slashes ('/')"
            )
        if len(name) > _MAX_FILENAME_LEN:
            raise QuestionValidationException(
                "Question name cannot be longer than {} characters".format(
                    _MAX_FILENAME_LEN
                )
            )
    except (TypeError, AttributeError):
        raise QuestionValidationException(
            "Question name has the wrong type ({}), a string is expected".format(
                type(name)
            )
        )
    return True


def zip_dir(dir_path, out_file):
    # type: (str, Union[str, IO[Any]]) -> None
    """
    ZIP a specified directory and write it to the given output file path.

    :param dir_path: path to the directory to be zipped up
    :type dir_path: str
    :param out_file: path to the resulting zipfile
    :type out_file: str
    """
    with zipfile.ZipFile(out_file, "w", zipfile.ZIP_DEFLATED) as zipWriter:
        rel_root = os.path.abspath(os.path.join(dir_path, os.path.pardir))

        for root, _dirs, files in os.walk(dir_path):
            zipWriter.write(root, os.path.relpath(root, rel_root), zipfile.ZIP_STORED)
            for f in files:
                filename = os.path.join(root, f)
                arcname = os.path.join(os.path.relpath(root, rel_root), f)

                # Zipped files must be from 1980 or later
                # So copy any file older than that to a tempfile to bump the timestamp
                if os.path.getmtime(filename) < _MIN_ZIP_TIMESTAMP:
                    with tempfile.NamedTemporaryFile("w+b") as temp_file, open(
                        filename, "rb"
                    ) as file_src:
                        temp_file.write(file_src.read())
                        temp_file.flush()
                        zipWriter.write(temp_file.name, arcname)
                else:
                    zipWriter.write(filename, arcname)


def escape_html(s: str) -> str:
    from html import escape

    return escape(s)


def escape_name(s: str) -> str:
    """
    Escapes the given name string with double quotes if needed.

    A name should be quoted if it begins with '"', '/', or digit, or if it
    contains a special character (_NAME_SPECIAL_CHARS_).
    """
    return (
        '"{}"'.format(s)
        if len(s) != 0
        and (
            s.startswith('"')
            or s.startswith("/")
            or s[0].isdigit()
            or any(s.find(c) > 0 for c in _NAME_SPECIAL_CHARS_)
        )
        else s
    )


def get_html(element):
    """Attempts to call `_repr_html_()` to get HTML representation of object."""
    try:
        return element._repr_html_()
    except AttributeError:
        return escape_html(str(element))
