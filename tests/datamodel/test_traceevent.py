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

from pybatfish.datamodel.acl import AclTrace, AclTraceEvent


# test if a trace event with description is deserialized and string-ified properly
def test_trace_event_with_description():
    dict = {"description": "aa"}

    # check deserialization
    trace_event = AclTraceEvent.from_dict(dict)
    assert trace_event.description == "aa"

    # check str
    event_str = str(trace_event)
    assert "aa" in event_str


def test_trace_str():
    event1 = {"description": "event1"}
    event2 = {}
    event3 = {"description": "event3"}
    events = [event1, event2, event3]
    trace = AclTrace.from_dict({"events": events})

    assert str(trace) == "event1\nevent3"


if __name__ == "__main__":
    pytest.main()
