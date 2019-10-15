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
import json

from pybatfish.datamodel import Edge, Interface, IssueType
from pybatfish.util import BfJsonEncoder


def test_as_dict():
    assert Interface(hostname="host", interface="iface").dict() == {
        "hostname": "host",
        "interface": "iface",
    }
    assert IssueType(major="lazer", minor="coal").dict() == {
        "major": "lazer",
        "minor": "coal",
    }

    # Make sure Edge dict is right if either string or Interface is passed in
    assert Edge(
        node1="r1",
        node1interface="iface1",
        node2="r2",
        node2interface=Interface(hostname="r2", interface="iface2"),
    ).dict() == {
        "node1": "r1",
        "node1interface": "iface1",
        "node2": "r2",
        "node2interface": "iface2",
    }


def test_json_serialization():
    i = Interface(hostname="host", interface="iface")
    # Load into dict from json to ignore key ordering
    assert json.loads(BfJsonEncoder().encode(i)) == json.loads(json.dumps(i.dict()))
