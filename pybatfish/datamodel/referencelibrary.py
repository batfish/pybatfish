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

__all__ = ['AddressGroup', 'ReferenceBook', 'ReferenceLibrary']


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
