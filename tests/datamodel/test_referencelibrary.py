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

from pybatfish.datamodel import Interface
from pybatfish.datamodel.referencelibrary import (
    AddressGroup,
    InterfaceGroup,
    NodeRole,
    NodeRoleDimension,
    NodeRolesData,
    ReferenceBook,
    ReferenceLibrary,
    RoleDimensionMapping,
    RoleMapping,
)


def test_addressgroup_construction_empty():
    """Check that we construct empty address groups properly."""
    empty_group = AddressGroup("g1", addresses=[], childGroupNames=[])

    assert AddressGroup("g1") == empty_group
    assert AddressGroup("g1", addresses=None, childGroupNames=None) == empty_group


def test_addressgroup_construction_badtype():
    """Check that we throw an error when address group is built with wrong type."""
    with pytest.raises(ValueError):
        AddressGroup("g1", addresses=AddressGroup("g1"))
    with pytest.raises(ValueError):
        AddressGroup("g1", childGroupNames=AddressGroup("g1"))
    with pytest.raises(ValueError):
        AddressGroup("book1", addresses=["ag", AddressGroup("ag1")])
    with pytest.raises(ValueError):
        AddressGroup("book1", childGroupNames=["ag", AddressGroup("ag1")])


def test_addressgroup_construction_item():
    """Check that we construct address groups when sub-props are not a list."""
    assert AddressGroup("g1", addresses="ag") == AddressGroup("g1", addresses=["ag"])
    assert AddressGroup("g1", childGroupNames="ag") == AddressGroup(
        "g1", childGroupNames=["ag"]
    )


def test_addressgroup_construction_list():
    """Check that we construct address groups where sub-props are lists."""
    group = AddressGroup("g1", addresses=["ag"], childGroupNames=["cg"])

    assert group.name == "g1"
    assert group.addresses == ["ag"]
    assert group.childGroupNames == ["cg"]


def test_addressgroup_deser_both_subfields():
    """Test deserialization for a reference library with address groups."""
    dict = {
        "name": "ag1",
        "addresses": ["1.1.1.1/24", "2.2.2.2"],
        "childGroupNames": ["child1", "child2"],
    }

    address_group = AddressGroup.from_dict(dict)

    assert len(address_group.addresses) == 2
    assert len(address_group.childGroupNames) == 2


def test_addressgroup_deser_none_subfields():
    """Test deserialization for a reference library with address groups."""
    dict = {"name": "ag1"}

    address_group = AddressGroup.from_dict(dict)

    assert len(address_group.addresses) == 0
    assert len(address_group.childGroupNames) == 0


def test_addressgroup_deser_only_addresses():
    """Test deserialization for a reference library with address groups."""
    dict = {"name": "ag1", "addresses": ["1.1.1.1/24", "2.2.2.2"]}

    address_group = AddressGroup.from_dict(dict)

    assert len(address_group.addresses) == 2
    assert len(address_group.childGroupNames) == 0


def test_addressgroup_deser_only_child_groups():
    """Test deserialization for a reference library with address groups."""
    dict = {"name": "ag1", "childGroupNames": ["child1", "child2"]}

    address_group = AddressGroup.from_dict(dict)

    assert len(address_group.addresses) == 0
    assert len(address_group.childGroupNames) == 2


def test_interfacegroup_construction_empty():
    """Check that we construct empty interface groups properly."""
    empty_group = InterfaceGroup("g1", interfaces=[])

    assert InterfaceGroup("g1") == empty_group
    assert InterfaceGroup("g1", interfaces=None) == empty_group


def test_interfacegroup_construction_badtype():
    """Check that we throw an error when interface group is built with wrong type."""
    with pytest.raises(ValueError):
        InterfaceGroup("g1", interfaces="i1")
    with pytest.raises(ValueError):
        InterfaceGroup(
            "book1", interfaces=["ag", Interface(hostname="h1", interface="i1")]
        )


def test_interfacegroup_construction_item():
    """Check that we construct address groups when sub-props are not a list."""
    interface = Interface(hostname="h1", interface="i1")
    interface_group = InterfaceGroup("g1", interfaces=[interface])
    assert InterfaceGroup("g1", interfaces=interface) == interface_group


def test_interfacegroup_construction_list():
    """Check that we construct interface groups where sub-props are lists."""
    interface = Interface(hostname="h1", interface="i1")
    group = InterfaceGroup("g1", interfaces=[interface])

    assert group.name == "g1"
    assert group.interfaces == [interface]


def test_noderoledimension_construction_empty():
    """Check that we construct empty node role dimension properly."""
    empty = NodeRoleDimension("g1", roleDimensionMappings=[])

    assert NodeRoleDimension("g1") == empty
    assert NodeRoleDimension("g1", roles=None) == empty
    assert NodeRoleDimension("g1", roleDimensionMappings=None) == empty


def test_noderoledimension_construction():
    """Check that we throw an error when node role dimension is built with wrong type."""
    with pytest.raises(ValueError):
        NodeRoleDimension("g1", roles="i1")
    with pytest.raises(ValueError):
        NodeRoleDimension("book1", roles=["ag", NodeRole("a", "b")])
    with pytest.raises(ValueError):
        NodeRoleDimension("g1", roleDimensionMappings="i1")
    with pytest.raises(ValueError):
        NodeRoleDimension(
            "book1", roleDimensionMappings=["ag", RoleDimensionMapping("a", "b", "c")]
        )


def test_noderoledimension_construction_item():
    """Check that we construct node role dimension when sub-props are not a list."""
    role = NodeRole("a", "b")
    dimension1 = NodeRoleDimension("g1", roles=[role])
    assert NodeRoleDimension("g1", roles=role) == dimension1

    rdMap = RoleDimensionMapping("a", [], {})
    dimension2 = NodeRoleDimension("g1", roleDimensionMappings=[rdMap])
    assert NodeRoleDimension("g1", roleDimensionMappings=rdMap) == dimension2


def test_noderoledimension_construction_list():
    """Check that we construct interface groups where sub-props are lists."""
    role = NodeRole("a", "b")
    dimension1 = NodeRoleDimension("g1", roles=[role])
    assert dimension1.name == "g1"
    assert dimension1.roles == [role]

    rdMap = RoleDimensionMapping("a", [], {})
    dimension2 = NodeRoleDimension("g1", roleDimensionMappings=[rdMap])
    assert dimension2.name == "g1"
    assert dimension2.roleDimensionMappings == [rdMap]

    dimension3 = NodeRoleDimension("g1", roles=[role], roleDimensionMappings=[rdMap])
    assert dimension3.name == "g1"
    assert dimension3.roles == [role]
    assert dimension3.roleDimensionMappings == [rdMap]


def test_noderolesdata_construction_empty():
    """Check that we construct empty node role data properly."""
    empty = NodeRolesData(defaultDimension=None, roleDimensionOrder=[], roleMappings=[])

    assert NodeRolesData() == empty
    assert NodeRolesData(None) == empty
    assert NodeRolesData(None, []) == empty
    assert NodeRolesData(None, [], []) == empty


def test_noderolesdata_construction_badtype():
    """Check that we throw an error when node role data is built with wrong type."""
    with pytest.raises(ValueError):
        NodeRolesData("", [1], [])
    with pytest.raises(ValueError):
        NodeRolesData("", [], [1])


def test_noderolesdata_construction_item():
    """Check that we construct node role data when sub-props are not a list."""
    dimension = "dim"
    expected = NodeRolesData(
        defaultDimension=None, roleDimensionOrder=[dimension], roleMappings=[]
    )
    actual = NodeRolesData(
        defaultDimension=None, roleDimensionOrder=dimension, roleMappings=[]
    )
    assert actual == expected

    mapping = RoleMapping(None, "", {}, {})
    expected = NodeRolesData(
        defaultDimension=None, roleDimensionOrder=[], roleMappings=[mapping]
    )
    actual = NodeRolesData(
        defaultDimension=None, roleDimensionOrder=[], roleMappings=mapping
    )
    assert actual == expected


def test_noderolesdata_construction_list():
    """Check that we construct node role data where sub-props are lists."""
    dimension = "dim"
    data = NodeRolesData(
        defaultDimension=None, roleDimensionOrder=[dimension], roleMappings=[]
    )

    assert data.roleDimensionOrder == [dimension]

    mapping = RoleMapping(None, "", {}, {})
    data = NodeRolesData(
        defaultDimension=None, roleDimensionOrder=[], roleMappings=[mapping]
    )

    assert data.roleMappings == [mapping]


def test_referencebook_construction_empty():
    """Check that we construct empty reference books properly."""
    empty_book = ReferenceBook("b1", addressGroups=[], interfaceGroups=[])

    assert ReferenceBook("b1") == empty_book
    assert ReferenceBook("b1", addressGroups=None, interfaceGroups=None) == empty_book


def test_referencebook_construction_addressgroup_badtype():
    """Check that we throw an error when address group is wrong type."""
    with pytest.raises(ValueError):
        ReferenceBook("book1", addressGroups="ag")
    with pytest.raises(ValueError):
        ReferenceBook("book1", addressGroups=["ag"])
    with pytest.raises(ValueError):
        ReferenceBook("book1", addressGroups=["ag", AddressGroup("ag1")])


def test_referencebook_construction_addressgroup_item():
    """Check that we construct reference books where address group is not a list."""
    ref_book = ReferenceBook("book1", addressGroups=AddressGroup("ag"))

    assert ref_book.name == "book1"
    assert ref_book.addressGroups == [AddressGroup("ag")]


def test_referencebook_construction_addressgroup_list():
    """Check that we construct reference books where address group is a list."""
    ref_book = ReferenceBook("book1", addressGroups=[AddressGroup("ag")])

    assert ref_book.name == "book1"
    assert ref_book.addressGroups == [AddressGroup("ag")]


def test_referencebook_construction_interfacegroup_badtype():
    """Check that we throw an error when interface group is wrong type."""
    with pytest.raises(ValueError):
        ReferenceBook("book1", interfaceGroups="g")
    with pytest.raises(ValueError):
        ReferenceBook("book1", interfaceGroups=["g"])
    with pytest.raises(ValueError):
        ReferenceBook("book1", interfaceGroups=["g", InterfaceGroup("g1")])


def test_referencebook_construction_interfacegroup_item():
    """Check that we construct reference books where interface group is not a list."""
    ref_book = ReferenceBook("book1", interfaceGroups=InterfaceGroup("g"))

    assert ref_book.name == "book1"
    assert ref_book.interfaceGroups == [InterfaceGroup("g")]


def test_referencebook_construction_interfacegroup_list():
    """Check that we construct reference books where interface group is a list."""
    ref_book = ReferenceBook("book1", interfaceGroups=[InterfaceGroup("g")])

    assert ref_book.name == "book1"
    assert ref_book.interfaceGroups == [InterfaceGroup("g")]


def test_referencelibrary_construction_empty():
    """Check that we construct empty reference library properly."""
    empty = ReferenceLibrary(books=[])

    assert ReferenceLibrary() == empty
    assert ReferenceLibrary(None) == empty


def test_referencelibrary_construction_badtype():
    """Check that we throw an error when reference library is built with wrong type."""
    with pytest.raises(ValueError):
        ReferenceLibrary(books="i1")
    with pytest.raises(ValueError):
        ReferenceLibrary(books=["ag", ReferenceBook("a")])


def test_referencelibrary_construction_item():
    """Check that we construct reference library when sub-props are not a list."""
    book = ReferenceBook("a")
    library = ReferenceLibrary(books=[book])
    assert ReferenceLibrary(books=book) == library


def test_referencelibrary_construction_list():
    """Check that we construct reference library where sub-props are lists."""
    book = ReferenceBook("a")
    library = ReferenceLibrary(books=[book])

    assert library.books == [book]


def test_referencelibrary_deser_empty():
    """Check proper deserialization for a reference library dict."""
    dict = {}
    reference_library = ReferenceLibrary(**dict)
    assert len(reference_library.books) == 0

    dict = {"books": []}
    reference_library = ReferenceLibrary(**dict)
    assert len(reference_library.books) == 0


def test_referencelibrary_deser_addressgroups():
    """Test deserialization for a reference library with address groups."""
    dict = {
        "books": [
            {
                "name": "book1",
                "addressGroups": [
                    {
                        "name": "ag1",
                        "addresses": ["1.1.1.1/24", "2.2.2.2", "3.3.3.3:0.0.0.8"],
                    },
                    {"name": "ag2"},
                ],
            },
            {"name": "book2"},
        ]
    }
    reference_library = ReferenceLibrary.from_dict(dict)

    assert len(reference_library.books) == 2
    assert reference_library.books[0].name == "book1"
    assert len(reference_library.books[0].addressGroups) == 2
    assert reference_library.books[0].addressGroups[0].name == "ag1"
    assert len(reference_library.books[0].addressGroups[0].addresses) == 3


def test_referencelibrary_deser_interfacegroups():
    """Test deserialization for a reference library with interface groups."""
    dict = {
        "books": [
            {
                "name": "book1",
                "interfaceGroups": [
                    {
                        "name": "g1",
                        "interfaces": [
                            {"hostname": "h1", "interface": "i1"},
                            {"hostname": "h2", "interface": "i2"},
                        ],
                    },
                    {"name": "g2"},
                ],
            },
            {"name": "book2"},
        ]
    }
    reference_library = ReferenceLibrary.from_dict(dict)

    assert len(reference_library.books) == 2
    assert reference_library.books[0].name == "book1"
    assert len(reference_library.books[0].interfaceGroups) == 2
    assert reference_library.books[0].interfaceGroups[0].name == "g1"
    assert len(reference_library.books[0].interfaceGroups[0].interfaces) == 2


def test_roledimensionmapping_default_values():
    """Check the default values for role dimension mappings."""
    rdMap = RoleDimensionMapping("a")
    assert rdMap.groups == [1]
    assert rdMap.canonicalRoleNames == {}


def test_noderolesdata():
    """Check proper deserialization for a node roles data."""
    dict = {"roleDimensionOrder": ["dim1", "dim2"], "roleMappings": []}
    nodeRoleData = NodeRolesData.from_dict(dict)

    assert nodeRoleData.defaultDimension is None
    assert nodeRoleData.roleDimensionOrder == ["dim1", "dim2"]
    assert nodeRoleData.roleMappings == []


def test_rolemapping():
    """Test deserialization of RoleMapping."""
    regex = "re"
    roleDimensionGroups = {"dim1": [1], "dim2": [1, 2]}
    canonicalRoleNames = {"dim1": {"a": "A"}, "dim2": {"a-b": "AB"}}
    dict = {
        "regex": regex,
        "roleDimensionGroups": roleDimensionGroups,
        "canonicalRoleNames": canonicalRoleNames,
    }
    roleMapping = RoleMapping.from_dict(dict)
    assert roleMapping.name is None
    assert roleMapping.roleDimensionGroups == roleDimensionGroups
    assert roleMapping.canonicalRoleNames == canonicalRoleNames

    dict["name"] = "name"
    roleMapping = roleMapping.from_dict(dict)
    assert roleMapping.name == "name"


if __name__ == "__main__":
    pytest.main()
