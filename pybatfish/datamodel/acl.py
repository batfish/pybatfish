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

import attr

from .primitives import DataModelElement

__all__ = ['AclTrace', 'AclTraceEvent']


@attr.s(frozen=True)
class AclTraceEvent(DataModelElement):
    """One event corresponding to a packet's life through an ACL.

    :ivar class_name: The type of the event that occurred while tracing.
    :ivar description: The description of the event
    :ivar lineDescription: ACL line that caused the event (if applicable)
    """

    class_name = attr.ib(type=Optional[str], default=None)
    description = attr.ib(type=Optional[str], default=None)
    lineDescription = attr.ib(type=Optional[str], default=None)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> AclTraceEvent
        return AclTraceEvent(
            json_dict.get("class"),
            json_dict.get("description"),
            json_dict.get("lineDescription"))

    def __str__(self):
        # type: () -> str
        if self.description is not None:
            return self.description
        if self.lineDescription is not None:
            return self.lineDescription
        return repr(self)


@attr.s(frozen=True)
class AclTrace(DataModelElement):
    """The trace of a packet's life through an ACL.

    :ivar events: A list of :py:class:`AclTraceEvent`
    """

    events = attr.ib(type=List[AclTraceEvent], factory=list)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> AclTrace
        return AclTrace(
            [AclTraceEvent.from_dict(event) for event in
             json_dict.get("events", [])])

    def __str__(self):
        # type: () -> str
        return "\n".join(str(event) for event in self.events)
