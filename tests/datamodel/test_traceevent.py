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

from pybatfish.datamodel.acl import AclTraceEvent


# test if a trace event with description is deserialized and string-ified properly
def test_trace_event_with_description():
    dict = {"description": "aa", "class": "Permitted"}

    # check deserialization
    trace_event = AclTraceEvent.from_dict(dict)
    assert trace_event.class_name == "Permitted"
    assert trace_event.description == "aa"

    # check str
    event_str = str(trace_event)
    assert "aa" in event_str
    assert "PermittedDenied" not in event_str


# test if a trace event without description is deserialized and string-ified properly
def test_trace_event_without_description():
    dict = {"class": "Permitted"}

    # check deserialization
    trace_event = AclTraceEvent.from_dict(dict)
    assert trace_event.class_name == "Permitted"
    assert trace_event.description is None

    # check str
    event_str = str(trace_event)
    assert "Permitted" in event_str


if __name__ == "__main__":
    pytest.main()
