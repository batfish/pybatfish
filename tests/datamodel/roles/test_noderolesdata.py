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
"""Tests for node roles data."""

from __future__ import absolute_import, print_function

from pybatfish.datamodel.roles.noderolesdata import NodeRolesData
import pytest


def test_noderolesdata():
    """Check proper deserialization for a node role data dict."""
    dict = {
        "defaultDimension": "dim1",
        "roleDimensions": [
            {
                "name": "dim1",
                "type": "CUSTOM",
                "roles": [
                    {
                        "name": "role1",
                        "regex": "regex",
                        "nodes": [
                            "a",
                            "b"
                        ]
                    },
                    {
                        "name": "role2",
                        "regex": "regex",
                        "nodes": [
                            "c",
                            "b"
                        ]
                    },
                ]
            },
        ]
    }
    nodeRoleData = NodeRolesData(dict)

    assert nodeRoleData.default_dimension == "dim1"
    assert len(nodeRoleData.roleDimensions) == 1
    assert len(nodeRoleData.roleDimensions[0].roles) == 2
    assert len(nodeRoleData.roleDimensions[0].roles[0].nodes) == 2


if __name__ == "__main__":
    pytest.main()
