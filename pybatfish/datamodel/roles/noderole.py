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

from typing import Dict  # noqa: F401

from pybatfish.util import obj_to_str

__all__ = ['NodeRole']


class NodeRole(object):
    """Information about a node role."""

    def __init__(self, d):
        # type: (Dict) -> None
        """
        Create a new node role object.

        :param d: initialization dictionary
        """
        if "name" not in d:
            raise ValueError("'name' not present in the NodeRole object")
        if "regex" not in d:
            raise ValueError("'regex' not present in the NodeRole object")
        self.name = d["name"]
        self.regex = d["regex"]
        self.nodes = d.get("nodes", [])

    def __str__(self):
        # type: () -> str
        return obj_to_str(self)
