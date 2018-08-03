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

from pybatfish.datamodel.roles.noderoledimension import NodeRoleDimension
from pybatfish.util import obj_to_str

__all__ = ['NodeRolesData']


class NodeRolesData(object):
    """Information about node roles."""

    def __init__(self, d):
        # type: (Dict) -> None
        """
        Create a new node roles object.

        :param d: initialization dictionary
        """
        self.default_dimension = d.get("defaultDimension", None)
        self.roleDimensions = [NodeRoleDimension.from_dict(dim) for dim in
                               d.get("roleDimensions", [])]

    def __str__(self):
        # type: () -> str
        return obj_to_str(self)
