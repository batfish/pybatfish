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

import attr
from deprecated import deprecated

from .primitives import DataModelElement, Interface

__all__ = [
    "AddressGroup",
    "InterfaceGroup",
    "NodeRole",
    "NodeRoleDimension",
    "NodeRolesData",
    "ReferenceBook",
    "ReferenceLibrary",
    "RoleDimensionMapping",
    "RoleMapping",
]


def _check_type(value, expected_type):
    if not isinstance(value, expected_type):
        raise ValueError(
            "Invalid value '{}' of type {}. Expected type '{}'".format(
                value, type(value), expected_type
            )
        )


def _make_typed_list(value, item_type):
    # type: (Any, Any) -> List[Any]
    if value is None:
        return []
    if isinstance(value, list):
        for item in value:
            _check_type(item, item_type)
        return value
    _check_type(value, item_type)
    return [value]


def _make_string_list(value):
    # type: (Any) -> List[str]
    return _make_typed_list(value, str)


@attr.s(frozen=True)
class AddressGroup(DataModelElement):
    """
    Information about an address group.

    :ivar name: The name of the group
    :ivar addresses: a list of 'addresses' where each element is a string
        that represents an IP address (e.g., "1.1.1.1"), prefix
        (e.g., 1.1.1.0/24), or an address:mask (e.g., "1.1.1.1:0.0.0.8").
    :ivar childGroupNames: a list of names of child groups in this address
        group. The child groups must exist in the same reference book. Circular
        descendant relationships between address groups are allowed. The
        address group is considered to contain all addresses that are directly
        in it or in any of its descendants.
    """

    name = attr.ib(type=str)
    addresses = attr.ib(type=List[str], factory=list, converter=_make_string_list)
    childGroupNames = attr.ib(type=List[str], factory=list, converter=_make_string_list)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> AddressGroup
        return AddressGroup(
            json_dict["name"],
            json_dict.get("addresses", []),
            json_dict.get("childGroupNames", []),
        )


def _make_interface_list(value):
    # type: (Any) -> List[Interface]
    return _make_typed_list(value, Interface)


@attr.s(frozen=True)
class InterfaceGroup(DataModelElement):
    """
    Information about an interface group.

    :ivar name: The name of the group
    :ivar interfaces: a list of interfaces, of type :py:class:`~Interface`.
    """

    name = attr.ib(type=str)
    interfaces = attr.ib(
        type=List[Interface], factory=list, converter=_make_interface_list
    )

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> InterfaceGroup
        return InterfaceGroup(
            json_dict["name"],
            [Interface.from_dict(d) for d in json_dict.get("interfaces", [])],
        )


@deprecated(reason="Use the new RoleDimensionMapping class instead")
@attr.s(frozen=True)
class NodeRole(DataModelElement):
    """
    Information about a node role.

    :ivar name: Name of the node role.
    :ivar regex: A regular expression over node names to describe nodes that
        belong to this role. The regular expression must be a
        valid **Java** regex.
    """

    name = attr.ib(type=str)
    regex = attr.ib(type=str)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> NodeRole
        return NodeRole(json_dict["name"], json_dict["regex"])


def _make_node_roles(value):
    # type: (Any) -> List[NodeRole]
    return _make_typed_list(value, NodeRole)


@deprecated
@attr.s(frozen=True)
class RoleDimensionMapping(DataModelElement):
    """
    Information about a role dimension mapping.

    :ivar regex: A regular expression over node names to describe nodes that
        belong to this role. The regular expression must be a valid **Java**
        regex.
    :ivar groups: A list of group numbers (integers) that identify the role
        name for a given node name (default value is [1]).
    :ivar canonicalRoleNames: A map from Java regexes over role names determined
        from the groups to a canonical set of role names for this dimension
        (default value is {}).
    """

    regex = attr.ib(type=str)
    groups = attr.ib(type=List[int], default=[1])
    canonicalRoleNames = attr.ib(type=Dict[str, str], default={})

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> RoleDimensionMapping
        return RoleDimensionMapping(
            json_dict["regex"],
            json_dict.get("groups", [1]),
            json_dict.get("canonicalRoleNames", {}),
        )


def _make_role_dimension_mappings(value):
    # type: (Any) -> List[RoleDimensionMapping]
    return _make_typed_list(value, RoleDimensionMapping)


@deprecated
@attr.s(frozen=True)
class NodeRoleDimension(DataModelElement):
    """
    Information about a node role dimension.

    :ivar name: Name of the node role dimension.
    :ivar roles: The list of :py:class:`NodeRole` objects in this dimension (deprecated).
    :ivar roleDimensionMappings: The list of :py:class:`RoleDimensionMapping` objects
        in this dimension.
    """

    name = attr.ib(type=str)
    roles = attr.ib(type=List[NodeRole], factory=list, converter=_make_node_roles)
    roleDimensionMappings = attr.ib(
        type=List[RoleDimensionMapping],
        factory=list,
        converter=_make_role_dimension_mappings,
    )

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> NodeRoleDimension
        return NodeRoleDimension(
            json_dict["name"],
            [NodeRole.from_dict(d) for d in json_dict.get("roles", [])],
            [
                RoleDimensionMapping.from_dict(d)
                for d in json_dict.get("roleDimensionMappings", [])
            ],
        )


def _make_node_role_dimensions(value):
    # type: (Any) -> List[NodeRoleDimension]
    return _make_typed_list(value, NodeRoleDimension)


@attr.s(frozen=True)
class RoleMapping(DataModelElement):
    """
    A mapping from node name to role dimensions.

    :ivar name: (Optional) the name of the role mapping
    :ivar regex: A java regex over hostnames, with groups to extract role data
    :ivar roleDimensionGroups: a map from each role dimension name to the list
        of regex groups that signify the role name for that dimension.
    :ivar canonicalRoleNames: for each role dimension, a map from the default
        role name that was obtained from the node name to a canonical role name
    """

    name = attr.ib(type=str)
    regex = attr.ib(type=str)
    roleDimensionGroups = attr.ib(type=Dict[str, int])
    canonicalRoleNames = attr.ib(type=Dict[str, Dict[str, str]], factory=dict)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> RoleMapping
        return RoleMapping(
            json_dict.get("name", None),
            json_dict["regex"],
            json_dict.get("roleDimensionGroups", {}),
            json_dict.get("canonicalRoleNames", {}),
        )


def _make_role_mappings(value):
    # type: (Any) -> List[RoleMapping]
    return _make_typed_list(value, RoleMapping)


@attr.s(frozen=True)
class NodeRolesData(DataModelElement):
    """
    Information about a node roles data.

    :ivar defaultDimension
    :ivar roleDimensionOrder: The precedence order of role dimensions.
    :ivar roleMappings: A list of :py:class:`RoleMapping` objects
    """

    defaultDimension = attr.ib(type=Optional[str], default=None)
    roleDimensionOrder = attr.ib(
        type=List[str], factory=list, converter=_make_string_list
    )
    roleMappings = attr.ib(
        type=List[RoleMapping], factory=list, converter=_make_role_mappings
    )

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> NodeRolesData
        return NodeRolesData(
            json_dict.get("defaultDimension"),
            json_dict.get("roleDimensionOrder", []),
            [RoleMapping.from_dict(d) for d in json_dict.get("roleMappings", [])],
        )


def _make_address_groups(value):
    # type: (Any) -> List[AddressGroup]
    return _make_typed_list(value, AddressGroup)


def _make_interface_groups(value):
    # type: (Any) -> List[InterfaceGroup]
    return _make_typed_list(value, InterfaceGroup)


# TODO: Extend ReferenceBook other types of references beyond address groups


@attr.s(frozen=True)
class ReferenceBook(DataModelElement):
    """
    Information about a reference book.

    :ivar name: Name of the reference book.
    :ivar addressGroups: A list of groups, of type :py:class:`~AddressGroup`.
    :ivar interfaceGroups: A list of groups, of type :py:class:`~InterfaceGroup`.
    """

    name = attr.ib(type=str)
    addressGroups = attr.ib(
        type=List[AddressGroup], factory=list, converter=_make_address_groups
    )
    interfaceGroups = attr.ib(
        type=List[InterfaceGroup], factory=list, converter=_make_interface_groups
    )

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> ReferenceBook
        return ReferenceBook(
            json_dict["name"],
            [AddressGroup.from_dict(d) for d in json_dict.get("addressGroups", [])],
            [InterfaceGroup.from_dict(d) for d in json_dict.get("interfaceGroups", [])],
        )


def _make_reference_books(value):
    # type: (Any) -> List[ReferenceBook]
    return _make_typed_list(value, ReferenceBook)


@attr.s(frozen=True)
class ReferenceLibrary(DataModelElement):
    """
    Information about a reference library.

    :ivar books: A list of books of type :py:class:`~ReferenceBook`.
    """

    books = attr.ib(
        type=List[ReferenceBook], factory=list, converter=_make_reference_books
    )

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> ReferenceLibrary
        return ReferenceLibrary(
            [ReferenceBook.from_dict(d) for d in json_dict.get("books", [])]
        )
