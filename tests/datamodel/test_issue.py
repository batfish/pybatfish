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

from pybatfish.datamodel.primitives import Issue


def test_issue_deserialization():
    """Test correct deserialization."""
    issue_dict = {
        "severity": 100,
        "explanation": "itsme",
        "type": {"major": "maj", "minor": "min"},
    }
    issue = Issue.from_dict(issue_dict)

    assert issue.severity == 100
    assert issue.explanation == "itsme"
    assert issue.type.major == "maj"
    assert issue.type.minor == "min"


def test_column_metadata_bad_severity():
    """Throw exception if severity is not an integer or cannot be converted."""
    issue = {"severity": "100"}
    assert Issue.from_dict(issue).severity == 100

    issue["severity"] = "i_am_string"
    with pytest.raises(ValueError):
        Issue.from_dict(issue)


def test_column_metadata_no_severity():
    """Exception is thrown if severity is missing."""
    with pytest.raises(ValueError):
        Issue.from_dict({"noSeverity": 100})
    with pytest.raises(ValueError):
        Issue.from_dict({})
    with pytest.raises(TypeError):
        Issue.from_dict({"severity": None})


def test_column_metadata_optional_fields():
    """Ensure that optional fields are populated if missing."""
    issue_dict = {"severity": 100}
    issue = Issue.from_dict(issue_dict)

    assert issue.explanation
    assert issue.type
    assert issue.type.major
    assert issue.type.minor
