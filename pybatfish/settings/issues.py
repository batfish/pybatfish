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

from typing import Dict, Optional  # noqa: F401

import attr

__all__ = ["IssueConfig"]


@attr.s(frozen=True)
class IssueConfig(object):
    """Configuration for an Issue.

    The issue is identified using its major and minor types. Its configuration
    includes its severity and an URL that explains what the issue means.

    :ivar major: The major issue type (see `:py:class:~pybatfish.datamodel.IssueType`)
    :ivar minor: The minor issue type (see `:py:class:~pybatfish.datamodel.IssueType`)
    :ivar severity: Issue severity (see `:py:class:~pybatfish.datamodel.Issue`)
    :ivar url: URL that explains what the issue means.
    """

    major = attr.ib(type=str)
    minor = attr.ib(type=str)
    severity = attr.ib(type=Optional[int])
    url = attr.ib(type=Optional[int])

    def dict(self):
        """Return this issue config as a dictionary."""
        return attr.asdict(self, recurse=True)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> IssueConfig
        return IssueConfig(
            json_dict["major"],
            json_dict["minor"],
            json_dict.get("severity"),
            json_dict.get("url"),
        )
