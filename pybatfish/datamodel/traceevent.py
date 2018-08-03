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

from typing import Dict, Optional  # noqa: F401


class TraceEvent(object):
    """One event corresponding to a packet's life through an ACL."""

    def __init__(self, d):
        # type: (Dict) -> None
        """
        Create a new TraceEvent.

        :param d: initialization dictionary
        """
        self.classname = d.get("class")  # type: Optional[str]
        self.description = d.get("description")  # type: Optional[str]
        self.lineDescription = d.get("lineDescription")  # type: Optional[str]

    def __str__(self):
        # type: () -> str
        if hasattr(self, "description") and self.description:
            return self.description
        if hasattr(self, "lineDescription") and self.lineDescription:
            return self.lineDescription
        return str(self.__dict__)
