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

from pybatfish.datamodel.acltrace import AclTrace
import pytest


# test if an acl trace is deserialized properly
def test_acl_trace_deserialization():
    trace_dict = {"events": [
        {"description": "aa"},
        {"description": "bb"}
    ]}

    # check deserialization
    acl_trace = AclTrace(trace_dict)
    assert len(acl_trace.trace_events) == 2

    # check stringification works
    str(acl_trace)


if __name__ == "__main__":
    pytest.main()
