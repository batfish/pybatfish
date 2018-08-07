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

from typing import Any, Dict, List, Optional  # noqa: F401

from pybatfish.datamodel.roles.noderole import NodeRole
from pybatfish.util import obj_to_str

__all__ = ['NodeRoleDimension']


class NodeRoleDimension(object):
    """Information about a node role dimension."""

    def __init__(self, name, type, snapshot, roles):
        # type: (str, str, Optional[str], List[NodeRole]) -> None
        """Create a new node role dimension object."""
        if not "name":
            raise ValueError(
                "'name' not present in the NodeRoleDimension object")
        if not "type":
            raise ValueError(
                "'type' not present in the NodeRoleDimension object")
        self.name = name
        self.type = type
        self.snapshot = snapshot
        self.roles = roles

    @classmethod
    def create_custom(cls, name, roles=None):
        # type: (str, Optional[List[NodeRole]]) -> NodeRoleDimension
        if roles is None:
            roles = []
        return cls(name, "CUSTOM", None, roles)

    @classmethod
    def from_dict(cls, d):
        # type: (Dict) -> NodeRoleDimension
        """
        Create a new node role dimension object.

        :param d: initialization dictionary
        """
        return cls(d.get("name", None),
                   d.get("type", None),
                   d.get("snapshot", None),
                   [NodeRole(role) for role in d.get("roles", [])])

    def to_dict(self):
        # type: () -> Dict
        """
        Creates a dictionary from the NodeRoleDimension object.

        :return: A dictionary that represents this object
        """
        dict = {}  # type: Dict[str, Any]
        dict["name"] = self.name
        if self.snapshot:
            dict["snapshot"] = self.snapshot
        dict["type"] = self.type
        dict["roles"] = [role.__dict__ for role in self.roles]
        return dict

    def __str__(self):
        # type: () -> str
        return obj_to_str(self)
