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

from operator import attrgetter

import pytest

from pybatfish.datamodel import ListWrapper
from pybatfish.datamodel.answer.table import TableAnswer, is_table_ans


def test_table_answer_no_answer_elements():
    """Exception is raised when answer elements are empty or not present."""
    with pytest.raises(ValueError):
        TableAnswer({})
    with pytest.raises(ValueError):
        TableAnswer({"answerElements": []})


def test_table_answer_element_no_metadata():
    """Exception is raised when metadata field is not present."""
    answer = {"answerElements": [{"nometadata": {}}]}
    with pytest.raises(ValueError):
        TableAnswer(answer)

    answer = {"answerElements": [{}]}
    with pytest.raises(ValueError):
        TableAnswer(answer)


def test_table_answer_element_deser():
    """Check proper deserialization for a valid table answer."""
    answer = {
        "answerElements": [
            {
                "metadata": {
                    "columnMetadata": [
                        {"name": "col1", "schema": "String"},
                        {"name": "col2", "schema": "String"},
                    ]
                },
                "rows": [{"col1": "value1", "col2": "value2"}],
            }
        ]
    }
    table = TableAnswer(answer)

    assert len(table.metadata.column_metadata) == 2
    assert table.metadata.column_metadata[0].name == "col1"
    assert len(table.rows) == 1
    assert table.rows[0].get("col1") == "value1"
    assert table.rows[0].get("col2") == "value2"
    assert not table.frame().empty


def test_table_answer_element_deser_no_rows():
    """Check deserialization creates empty table when no rows are present."""
    answer = {
        "answerElements": [
            {"metadata": {"columnMetadata": [{"name": "col1", "schema": "Node"}]}}
        ]
    }
    table = TableAnswer(answer)

    assert len(table.metadata.column_metadata) == 1
    assert table.metadata.column_metadata[0].name == "col1"
    assert len(table.rows) == 0
    assert table.frame().empty
    assert table.frame().columns == list(
        map(attrgetter("name"), table.metadata.column_metadata)
    )


def test_table_answer_element_excluded_rows():
    """Check deserialization creates empty table when no rows are present."""
    answer = {
        "answerElements": [
            {
                "metadata": {"columnMetadata": [{"name": "col1", "schema": "String"}]},
                "excludedRows": [
                    {"exclusionName": "myEx", "rows": [{"col1": "stringValue"}]}
                ],
            }
        ]
    }
    table = TableAnswer(answer)

    assert len(table.excluded_rows) == 1
    assert len(table.excluded_rows["myEx"]) == 1
    assert table.excluded_frame("myEx").size == 1


def test_table_answer_immutable_lists():
    answer = {
        "answerElements": [
            {
                "metadata": {
                    "columnMetadata": [{"name": "col1", "schema": "List<String>"}]
                },
                "rows": [{"col1": ["e1", "e2", "e3"]}],
            }
        ]
    }

    table = TableAnswer(answer)
    assert isinstance(table.frame().loc[0]["col1"], ListWrapper)


def test_table_answer_dtype_object():
    """
    Ensure table answer frames have dtype of object.

    This also means converting missing values to None (and not ``numpy.nan``)
    """
    answer = {
        "answerElements": [
            {
                "metadata": {
                    "columnMetadata": [
                        {"name": "col1", "schema": "String"},
                        {"name": "col2", "schema": "Integer"},
                    ]
                },
                "rows": [
                    {"col1": "v1", "col2": 1},
                    {"col1": "v2", "col2": None},
                    {"col1": "v3", "col2": -1},
                    {"col1": "v4", "col2": "-1"},
                ],
            }
        ]
    }

    df = TableAnswer(answer).frame()
    assert df["col1"].dtype == "object"
    assert df["col2"].dtype == "object"
    assert df["col2"][1] is None
    assert str(df["col2"][1]) == "None"


def test_is_table_answer():
    answer = {
        "answerElements": [
            {
                "metadata": {
                    "columnMetadata": [{"name": "col1", "schema": "List<String>"}]
                },
                "rows": [{"col1": ["e1", "e2", "e3"]}],
            }
        ]
    }
    assert not is_table_ans(answer)
    # Fix up metadata
    answer["answerElements"][0][
        "class"
    ] = "org.batfish.datamodel.table.TableAnswerElement"
    assert is_table_ans(answer)


if __name__ == "__main__":
    pytest.main()
