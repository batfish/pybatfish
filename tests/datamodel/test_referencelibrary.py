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
"""Tests for reference library."""

from __future__ import absolute_import, print_function

import pytest

from pybatfish.datamodel.referencelibrary import NodeRolesData, \
    ReferenceLibrary, AddressGroup


def test_addressgroup_both_subfields():
    """Test deserialization for a reference library with address groups."""
    dict = {
        "name": "ag1",
        "addresses": [
            "1.1.1.1/24",
            "2.2.2.2"
        ],
        "childGroupNames": [
            "child1",
            "child2"
        ]
    }

    address_group = AddressGroup.from_dict(dict)

    assert len(address_group.addresses) == 2
    assert len(address_group.childGroupNames) == 2


def test_addressgroup_none_subfields():
    """Test deserialization for a reference library with address groups."""
    dict = {
        "name": "ag1"
    }

    address_group = AddressGroup.from_dict(dict)

    assert len(address_group.addresses) == 0
    assert len(address_group.childGroupNames) == 0


def test_addressgroup_only_addresses():
    """Test deserialization for a reference library with address groups."""
    dict = {
        "name": "ag1",
        "addresses": [
            "1.1.1.1/24",
            "2.2.2.2"
        ]
    }

    address_group = AddressGroup.from_dict(dict)

    assert len(address_group.addresses) == 2
    assert len(address_group.childGroupNames) == 0


def test_addressgroup_only_child_groups():
    """Test deserialization for a reference library with address groups."""
    dict = {
        "name": "ag1",
        "childGroupNames": [
            "child1",
            "child2"
        ]
    }

    address_group = AddressGroup.from_dict(dict)

    assert len(address_group.addresses) == 0
    assert len(address_group.childGroupNames) == 2


def test_empty_referencelibrary():
    """Check proper deserialization for a reference library dict."""
    dict = {}
    reference_library = ReferenceLibrary(**dict)
    assert len(reference_library.books) == 0

    dict = {
        "books": []
    }
    reference_library = ReferenceLibrary(**dict)
    assert len(reference_library.books) == 0


def test_referencelibrary_addressgroups():
    """Test deserialization for a reference library with address groups."""
    dict = {
        "books": [
            {
                "name": "book1",
                "addressGroups": [
                    {
                        "name": "ag1",
                        "addresses": [
                            "1.1.1.1/24",
                            "2.2.2.2",
                            "3.3.3.3:0.0.0.8"
                        ]
                    },
                    {
                        "name": "ag2"
                    }
                ]
            },
            {
                "name": "book2",
            }
        ]
    }
    reference_library = ReferenceLibrary.from_dict(dict)

    assert len(reference_library.books) == 2
    assert reference_library.books[0].name == "book1"
    assert len(reference_library.books[0].addressGroups) == 2
    assert reference_library.books[0].addressGroups[0].name == "ag1"
    assert len(reference_library.books[0].addressGroups[0].addresses) == 3


def test_referencelibrary_interfacegroups():
    """Test deserialization for a reference library with interface groups."""
    dict = {
        "books": [
            {
                "name": "book1",
                "interfaceGroups": [
                    {
                        "name": "g1",
                        "interfaces": [
                            {
                                "hostname": "h1",
                                "interface": "i1"
                            },
                            {
                                "hostname": "h2",
                                "interface": "i2"
                            }
                        ]
                    },
                    {
                        "name": "g2"
                    }
                ]
            },
            {
                "name": "book2",
            }
        ]
    }
    reference_library = ReferenceLibrary.from_dict(dict)

    assert len(reference_library.books) == 2
    assert reference_library.books[0].name == "book1"
    assert len(reference_library.books[0].interfaceGroups) == 2
    assert reference_library.books[0].interfaceGroups[0].name == "g1"
    assert len(reference_library.books[0].interfaceGroups[0].interfaces) == 2


def test_noderolesdata():
    """Check proper deserialization for a node roles data."""
    dict = {
        "roleDimensions": [
            {
                "name": "dim1",
                "type": "CUSTOM",
                "roles": [
                    {
                        "name": "role1",
                        "regex": "regex",
                    },
                    {
                        "name": "role2",
                        "regex": "regex",
                    },
                ]
            },
        ]
    }
    nodeRoleData = NodeRolesData.from_dict(dict)

    assert len(nodeRoleData.roleDimensions) == 1
    assert len(nodeRoleData.roleDimensions[0].roles) == 2
    assert nodeRoleData.roleDimensions[0].roles[0].name == "role1"


if __name__ == "__main__":
    pytest.main()
