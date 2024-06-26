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

from .primitives import DataModelElement, Interface

__all__ = [
    "AddressGroup",
    "InterfaceGroup",
    "NodeRolesData",
    "ReferenceBook",
    "ReferenceLibrary",
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

    name = attr.ib(
        type=Optional[str],
        validator=attr.validators.optional(attr.validators.instance_of(str)),
    )
    regex = attr.ib(type=str)
    roleDimensionGroups = attr.ib(type=Dict[str, List[int]])
    canonicalRoleNames = attr.ib(type=Dict[str, Dict[str, str]], factory=dict)

    @classmethod
    def from_dict(cls, json_dict: Dict) -> "RoleMapping":
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
