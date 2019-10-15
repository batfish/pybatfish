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

from __future__ import absolute_import, print_function

import pytest

from pybatfish.datamodel.answer.table import ColumnMetadata


# correct deserialization
def testColumnMetadataDeserialization():
    columnMetadata = {
        "name": "col1",
        "schema": "Node",
        "description": "itsme",
        "isKey": False,
        "isValue": False,
    }
    column = ColumnMetadata(columnMetadata)

    assert column.name == "col1"
    assert column.schema == "Node"
    assert column.description == "itsme"
    assert not column.isKey
    assert not column.isValue


# exception is thrown if name is missing
def testColumnMetadataNoName():
    columnMetadata = {"noName": "col1", "schema": "Node"}
    with pytest.raises(ValueError):
        ColumnMetadata(columnMetadata)


# exception is thrown is schema is missing
def testColumnMetadataNoSchema():
    columnMetadata = {"name": "col1", "noSchema": "Node"}
    with pytest.raises(ValueError):
        ColumnMetadata(columnMetadata)


# optional fields are populated
def testColumnMetadataOptionalFields():
    columnMetadata = {"name": "col1", "schema": "Node"}
    column = ColumnMetadata(columnMetadata)

    assert column.description
    assert column.isKey
    assert column.isValue
