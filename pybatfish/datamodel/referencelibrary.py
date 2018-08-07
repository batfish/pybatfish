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
from typing import List, Union, Dict, Any  # noqa: F401

from collections import namedtuple

__all__ = ['AddressGroup', 'NodeRole', 'NodeRoleDimension', 'NodeRolesData', 'ReferenceBook', 'ReferenceLibrary']


class AddressGroup(namedtuple("AddressGroup", ["name", "addresses"])):
    """
    Information about an address group.

    An address group has a 'name' and a list of 'addresses' where each element is a string that represents an
    IP address (e.g., "1.1.1.1") or an address:mask (e.g., "1.1.1.1:0.0.0.8").
    """

    def __new__(cls, name, addresses=[], **kwargs):
        # type: (str, List[str], Dict[str, Any]) -> AddressGroup
        """Create a new AddressGroup object."""
        return super(AddressGroup, cls).__new__(cls, name, addresses)


class NodeRole(namedtuple("NodeRole", ["name", "regex"])):
    """
    Information about a node role.

    A node role has a 'name' and a regular expression 'regex' over node names to describe nodes that belong to this
    role. The regular expression must be a valid JAVA regex.

    TODO: Support Python regular expressions.
    """

    def __new__(cls, name, regex, **kwargs):
        # type: (str, str, Dict[str, Any]) -> NodeRole
        """Create a new NodeRole object."""
        return super(NodeRole, cls).__new__(cls, name, regex)


class NodeRoleDimension(namedtuple("NodeRoleDimension", ["name", "type", "roles"])):
    """
    Information about a node role dimension.

    A node role dimension has a 'name' and a 'type' to capture if the dimension contains automatically inferred
    roles ('AUTO') or user-defined roles ('CUSTOM'). The 'roles' field has the list of NodeRoles in this dimension.
    """

    def __new__(cls, name, type="CUSTOM", roles=[], **kwargs):
        # type: (str, str, List[Union[NodeRole, Dict[str, Any]]], Dict[str, Any]) -> NodeRoleDimension
        """Create a new node role dimension object."""
        return super(NodeRoleDimension, cls).__new__(cls, name, type,
                                                     [role if isinstance(role, NodeRole) else NodeRole(**role) for role
                                                      in roles])


class NodeRolesData(namedtuple("NodeRolesData", ["roleDimensions"])):
    """
    Information about a node roles data.

    The 'roleDimensions' is a list of NodeRoleDimensions
    """

    def __new__(cls, roleDimensions=[], **kwargs):
        # type: (List[Union[NodeRoleDimension, Dict[str, Any]]], Dict[str, Any]) -> NodeRolesData
        """Create a new node role dimension object."""
        return super(NodeRolesData, cls).__new__(cls,
                                                 [dim if isinstance(dim, NodeRoleDimension) else NodeRoleDimension(
                                                     **dim) for dim in roleDimensions])


# TODO: Extend ReferenceBook other types of references beyond address groups

class ReferenceBook(namedtuple("ReferenceBook", ["name", "addressGroups"])):
    """
    Information about a reference book.

    A reference book has a 'name' and a list of 'addressGroups' of type AddressGroup.
    """

    def __new__(cls, name, addressGroups=[], **kwargs):
        # type: (str, List[Union[AddressGroup, Dict[str, Any]]], Dict[str, Any]) -> ReferenceBook
        """Create a new reference book object."""
        return super(ReferenceBook, cls).__new__(cls, name,
                                                 [ag if isinstance(ag, AddressGroup) else AddressGroup(**ag) for ag in
                                                  addressGroups])


class ReferenceLibrary(namedtuple("ReferenceLibrary", ["books"])):
    """
    Information about reference library.

    A reference library has a list of 'books' of type ReferenceBook.
    """

    def __new__(cls, books=[], **kwargs):
        # type: (List[Union[ReferenceBook, Dict[str, Any]]], Dict[str, Any]) -> ReferenceLibrary
        """Create a new reference library."""
        return super(ReferenceLibrary, cls).__new__(cls,
                                                    [book if isinstance(book, ReferenceBook) else ReferenceBook(**book)
                                                     for book in books])
