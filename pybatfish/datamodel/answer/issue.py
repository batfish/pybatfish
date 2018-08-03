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

from collections import namedtuple
from typing import Dict  # noqa: F401

__all__ = ['Issue', 'IssueType']

IssueType = namedtuple('IssueType', ['major', 'minor'])


class Issue(object):
    """Information about a bug/issue that Batfish has discovered."""

    def __init__(self, d):
        # type: (Dict) -> None
        """
        Create a new Issue.

        :param d: initialization dictionary
        """
        if "severity" not in d:
            raise ValueError("'severity' not present in the Issue object")
        self.severity = int(d["severity"])  # type: int
        self.explanation = d.get("explanation",
                                 "No explanation provided")  # type: str
        self.type = IssueType(
            **d.get("type", {"major": "unknown",
                             "minor": "unknown"}))  # type: IssueType

    def __str__(self):
        # type: () -> str
        return "[{}] {}".format(self.severity, self.explanation)
