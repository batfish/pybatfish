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

from typing import Dict, List, Optional  # noqa: F401

import pandas

from pybatfish.datamodel.answer.base import Answer, _parse_json_with_schema

__all__ = ["ColumnMetadata", "TableAnswer", "Row", "TableMetadata"]


class ColumnMetadata(object):
    """Metadata for a single column."""

    def __init__(self, dictionary):
        if "name" not in dictionary:
            raise ValueError("Bad column metadata: 'name' not found")
        if "schema" not in dictionary:
            raise ValueError("Bad column metadata: 'schema' not found")
        self.name = dictionary["name"]  # type: str
        self.schema = dictionary["schema"]  # type: str
        self.description = dictionary.get(
            "description", "No description provided"
        )  # type: str
        self.isKey = dictionary.get("isKey", True)  # type: bool
        self.isValue = dictionary.get("isValue", True)  # type: bool


class TableAnswer(Answer):
    """Batfish answer in the form of a table."""

    def __init__(self, dictionary):
        if "answerElements" not in dictionary:
            raise ValueError("Answer elements not found in dictionary")
        if len(dictionary["answerElements"]) == 0:
            raise ValueError("Empty answer elements list in dictionary")
        if "metadata" not in dictionary["answerElements"][0]:
            raise ValueError("TableMetadata not found in dictionary")
        super(TableAnswer, self).__init__(dictionary)
        answer_element = dictionary["answerElements"][0]
        self.metadata = TableMetadata(answer_element["metadata"])
        self.rows = [Row(row) for row in answer_element.get("rows", [])]

        self.table_data = _rows_to_frame(self.metadata, self.rows)

        self.excluded_rows = {}
        for exclusion in answer_element.get("excludedRows", []):
            if "exclusionName" not in exclusion:
                raise ValueError("Exclusion does not have 'exclusionName'")
            self.excluded_rows[exclusion["exclusionName"]] = exclusion.get("rows", [])

    def excluded_frame(self, exclusion_name):
        # type: (str) -> pandas.DataFrame
        """Return the excluded data for exclusion_name as a :py:class:`pandas.DataFrame`."""
        if exclusion_name not in self.excluded_rows:
            raise ValueError("Exclusion name {} does not exist".format(exclusion_name))
        return _rows_to_frame(self.metadata, self.excluded_rows[exclusion_name])

    def frame(self):
        """Return answer data as a :py:class:`pandas.DataFrame`."""
        return self.table_data

    def __repr__(self):
        return repr(self.table_data)

    def _repr_html_(self):
        return self.table_data._repr_html_()

    def __str__(self):
        return str(self.table_data)

    def __len__(self):
        # type: () -> int
        return len(self.table_data)


class Row(dict):
    """Represents a table row."""


class TableMetadata:
    """Metadata for a Batfish table answer.

    (See :py:class:`~pybatfish.datamodel.answers.table.TableAnswer`)
    """

    def __init__(self, dictionary):
        self.column_metadata = [
            ColumnMetadata(column) for column in dictionary.get("columnMetadata", [])
        ]
        self.hints = dictionary.get("displayHints")  # type: Optional[Dict]

    def get_column_names(self):
        # type: () -> List[str]
        return [cm.name for cm in self.column_metadata]


def _rows_to_frame(table_metadata, rows):
    # type: (TableMetadata, List[Row]) -> pandas.DataFrame
    row_based = [
        [
            _parse_json_with_schema(cm.schema, row.get(cm.name))
            for cm in table_metadata.column_metadata
        ]
        for row in rows
    ]
    column_names = table_metadata.get_column_names()
    # convert data to column format and force dtype=object on Series
    # This gets us consistent `None` values across columns -- no columns
    # are treated as numeric.
    col_based = {
        column_names[i]: pandas.Series(column, dtype="object")
        for i, column in enumerate(zip(*row_based))
    }
    df = pandas.DataFrame.from_dict(col_based, orient="columns", dtype="object")
    # Re-index to:
    # 1. Force ordering of columns
    # 2. Set columns even if the dataframe is empty
    return df.reindex(labels=column_names, axis="columns")


def is_table_ans(d):
    # type: (Dict) -> bool
    """Check if a given dictionary represents a table answer."""
    return (
        "answerElements" in d
        and d["answerElements"][0].get("class")
        == "org.batfish.datamodel.table.TableAnswerElement"
    )
