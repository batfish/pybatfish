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

from typing import Dict, List  # noqa: F401

from pybatfish.datamodel.traceevent import TraceEvent


class AclTrace(object):
    """The trace of a packet's life through an ACL."""

    def __init__(self, d):
        # type: (Dict) -> None
        """
        Create a new AclTrace.

        :param d: initialization dictionary
        """
        self.trace_events = [TraceEvent(event) for event in
                             d.get("events", [])]  # type: List[TraceEvent]

    def __str__(self):
        # type: () -> str
        return "\n".join(str(event) for event in self.trace_events)
