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

import pytest

from pybatfish.datamodel.answer.table import TableAnswerElement


def test_table_answer_element_no_metadata():
    """Exception is raised when metadata field is not present."""
    answer_element = {
        "noMetadata": {
        }
    }
    with pytest.raises(ValueError):
        TableAnswerElement(answer_element)
    with pytest.raises(ValueError):
        TableAnswerElement({})


def test_table_answer_element_deser():
    """Check proper deserialization for a valid table answer."""
    answer_element = {
        "metadata": {
            "columnMetadata":
                [
                    {
                        "name": "col1",
                        "schema": "String"
                    },
                    {
                        "name": "col2",
                        "schema": "String"
                    }
                ]
        },
        "rows": [{
            "col1": "value1",
            "col2": "value2"
        }]
    }
    table = TableAnswerElement(answer_element)

    assert len(table.metadata.column_metadata) == 2
    assert table.metadata.column_metadata[0].name == "col1"
    assert len(table.rows) == 1
    assert table.rows[0].get("col1") == "value1"
    assert table.rows[0].get("col2") == "value2"
    assert not table.frame().empty


def test_table_answer_element_deser_no_rows():
    """Check deserialization creates empty table when no rows are present."""
    answer_element = {
        "metadata": {
            "columnMetadata":
                [
                    {
                        "name": "col1",
                        "schema": "Node"
                    }
                ]
        }
    }
    table = TableAnswerElement(answer_element)

    assert len(table.metadata.column_metadata) == 1
    assert table.metadata.column_metadata[0].name == "col1"
    assert len(table.rows) == 0
    assert table.frame().empty


if __name__ == "__main__":
    pytest.main()
