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

# test if an acl trace is deserialized properly
from pybatfish.datamodel.primitives import AutoCompleteSuggestion


def test_auto_complete_suggestion_all_fields():
    suggestion = AutoCompleteSuggestion.from_dict(
        {
            "description": "desc",
            "hint": "hint",
            "insertionIndex": 16,
            "isPartial": True,
            "rank": 42,
            "text": "suggestion",
        }
    )
    assert suggestion.description == "desc"
    assert suggestion.hint == "hint"
    assert suggestion.insertion_index == 16
    assert suggestion.is_partial
    assert suggestion.rank == 42
    assert suggestion.text == "suggestion"


def test_auto_complete_suggestion_no_optionals():
    suggestion = AutoCompleteSuggestion.from_dict(
        {"isPartial": True, "rank": 42, "text": "suggestion"}
    )
    assert suggestion.description is None
    assert suggestion.hint is None
    assert suggestion.insertion_index == 0
    assert suggestion.is_partial
    assert suggestion.rank == 42
    assert suggestion.text == "suggestion"


if __name__ == "__main__":
    pytest.main()
