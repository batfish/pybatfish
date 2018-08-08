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
from pybatfish.datamodel.answer.base import Answer, _get_display_value

__all__ = [
    "ColumnMetadata",
    "TableAnswerElement",
    "Row",
    "TableMetadata"
]


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
            "description", "No description provided")  # type: str
        self.isKey = dictionary.get("isKey", True)  # type: bool
        self.isValue = dictionary.get("isValue", True)  # type: bool


# TODO: better docstrings for accessible fields
class TableAnswerElement(Answer):
    """Batfish answer represented as a table."""

    def __init__(self, dictionary):
        if "metadata" not in dictionary:
            raise ValueError("TableMetadata not found in dictionary")
        super(TableAnswerElement, self).__init__(dictionary)
        self.metadata = TableMetadata(dictionary["metadata"]) \
            # type: TableMetadata
        self.rows = [Row(row) for row in dictionary.get("rows", [])] \
            # type: List[Row]
        # TODO: row exclusions
        # (https://github.com/batfish/pybatfish/issues/5)

        self.table_headers = self.metadata.get_column_names()  # type: List[str]
        self.table_data = pandas.DataFrame.from_records(
            [[_get_display_value(cm.schema, row.get(cm.name)) for
              cm in self.metadata.column_metadata]
             for row in self.rows], columns=self.table_headers)

    def frame(self):
        """Return answer data as a :py:class:`pandas.DataFrame`."""
        return self.table_data

    def __repr__(self):
        return repr(self.table_data)

    def __str__(self):
        return str(self.table_data)


class Row(dict):
    """Represents a table row."""

    pass


class TableMetadata:
    """Metadata for a Batfish table answer.

    (See :py:class:`~pybatfish.datamodel.answers.table.TableAnswerElement`)
    """

    def __init__(self, dictionary):
        self.column_metadata = [ColumnMetadata(column) for column in
                                dictionary.get("columnMetadata", [])] \
            # type: List[ColumnMetadata]
        # TODO: parse displayHints, only storing for now
        self.hints = dictionary.get("displayHints")  # type: Optional[Dict]

    def get_column_names(self):
        # type: () -> List[str]
        return [cm.name for cm in self.column_metadata]
