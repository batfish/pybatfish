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

from pybatfish.datamodel.interface import Interface
from typing import Dict  # noqa: F401


class Edge(object):
    """A network edge (i.e., a link between two node/interface pairs)."""

    def __init__(self, json_object):
        # type: (Dict) -> None
        self.interface1 = Interface({"hostname": json_object["node1"],
                                     "interface": json_object["node1interface"]})
        self.interface2 = Interface({"hostname": json_object["node2"],
                                     "interface": json_object["node2interface"]})

    def __repr__(self):
        return str(self.interface1) + " -> " + str(self.interface2)
