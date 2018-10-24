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
from typing import Dict, List  # noqa: F401

import attr

from .primitives import DataModelElement, Interface

__all__ = ['AddressGroup', 'InterfaceGroup', 'NodeRole', 'NodeRoleDimension',
           'NodeRolesData', 'ReferenceBook', 'ReferenceLibrary']


@attr.s(frozen=True)
class AddressGroup(DataModelElement):
    """
    Information about an address group.

    :ivar name: The name of the group
    :ivar addresses: a list of 'addresses' where each element is a string
        that represents an IP address (e.g., "1.1.1.1") or an address:mask
        (e.g., "1.1.1.1:0.0.0.8").
    """

    name = attr.ib(type=str)
    addresses = attr.ib(type=List[str], factory=list)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> AddressGroup
        return AddressGroup(json_dict["name"], json_dict.get("addresses", []))


@attr.s(frozen=True)
class InterfaceGroup(DataModelElement):
    """
    Information about an interface group.

    :ivar name: The name of the group
    :ivar interfaces: a list of interfaces, of type :py:class:`~Interface`.
    """

    name = attr.ib(type=str)
    interfaces = attr.ib(type=List[Interface], factory=list)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> InterfaceGroup
        return InterfaceGroup(json_dict["name"],
                              [Interface.from_dict(d) for d in
                               json_dict.get('interfaces', [])])


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


@attr.s(frozen=True)
class NodeRoleDimension(DataModelElement):
    """
    Information about a node role dimension.

    :ivar name: Name of the node role dimension.
    :ivar type: to capture if the dimension contains automatically inferred
        roles (``AUTO``) or user-defined roles (``CUSTOM``).
    :ivar roles: The list of :py:class:`NodeRole` objects in this dimension.
    """

    name = attr.ib(type=str)
    type = attr.ib(type=str, default="CUSTOM")
    roles = attr.ib(type=List[NodeRole], factory=list)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> NodeRoleDimension
        return NodeRoleDimension(json_dict["name"], json_dict["type"],
                                 [NodeRole.from_dict(d) for d in
                                  json_dict.get("roles", [])])


@attr.s(frozen=True)
class NodeRolesData(DataModelElement):
    """
    Information about a node roles data.

    :ivar roleDimensions: A list of :py:class:`NodeRoleDimension` objects
    """

    roleDimensions = attr.ib(type=List[NodeRoleDimension], factory=list)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> NodeRolesData
        return NodeRolesData([NodeRoleDimension.from_dict(d) for d in
                              json_dict.get("roleDimensions", [])])


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
    addressGroups = attr.ib(type=List[AddressGroup], factory=list)
    interfaceGroups = attr.ib(type=List[InterfaceGroup], factory=list)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> ReferenceBook
        return ReferenceBook(json_dict["name"],
                             [AddressGroup.from_dict(d) for d in
                              json_dict.get("addressGroups", [])],
                             [InterfaceGroup.from_dict(d) for d in
                              json_dict.get("interfaceGroups", [])])


@attr.s(frozen=True)
class ReferenceLibrary(DataModelElement):
    """
    Information about a reference library.

    :ivar books: A list of books of type :py:class:`~ReferenceBook`.
    """

    books = attr.ib(type=List[ReferenceBook], factory=list)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> ReferenceLibrary
        return ReferenceLibrary(
            [ReferenceBook.from_dict(d) for d in json_dict.get('books', [])])
