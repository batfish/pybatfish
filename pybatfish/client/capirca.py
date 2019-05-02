# coding=utf-8
#   Copyright 2019 The Batfish Open Source Project
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
"""Contains Batfish commands that integrate with the Google Capirca library (https://github.com/google/capirca)."""

from __future__ import absolute_import, print_function

import logging
from typing import Union  # noqa: F401

import ipaddr
import six
try:
    from capirca.lib import naming
except ImportError:
    logging.exception(
        'Capirca must be installed to use the Pybatfish Capirca extensions')
    raise

from pybatfish.datamodel import AddressGroup, ReferenceBook

__all__ = ["create_reference_book"]


def _load_definitions(definition_dir):
    """Loads the Capirca definitions from the given directory."""
    return naming.Naming(definition_dir)


def _item_to_python_repr(item, definitions):
    """Converts the given Capirca item into a typed Python object."""
    # Capirca comments are just appended to item strings
    s = item.split('#')[0].strip()

    # A reference to another network
    if s in definitions.networks:
        return s

    # IPv4 address / network
    try:
        return ipaddr.IPv4Address(s)
    except ValueError:
        pass
    try:
        return ipaddr.IPv4Network(s)
    except ValueError:
        pass

    # IPv6 address / network
    try:
        return ipaddr.IPv6Address(s)
    except ValueError:
        pass
    try:
        return ipaddr.IPv6Network(s)
    except ValueError:
        pass

    raise ValueError('Unknown how to convert {s}'.format(s=s))


def _entry_to_group(name, items, definitions):
    """Converts one network definition into a Batfish AddressGroup."""
    logger = logging.getLogger(__name__)
    try:
        converted = [_item_to_python_repr(i, definitions) for i in
                     items]
    except ValueError:
        logger.exception('error converting %s, creating empty group', name)
        return AddressGroup(name)

    if any(isinstance(c, (ipaddr.IPv6Address, ipaddr.IPv6Network))
           for c in converted):
        logger.warning('Skipping IPv6 addresses in %s', name)

    converted_v4 = [str(c) for c in converted if
                    isinstance(c, (ipaddr.IPv4Address, ipaddr.IPv4Network))]

    converted_group = [c for c in converted if
                       isinstance(c, six.string_types)]

    return AddressGroup(
        '{name}'.format(name=name), addresses=converted_v4,
        childGroupNames=converted_group)


def create_reference_book(definitions, book_name='capirca'):
    # type: (Union[str, naming.Naming], str) -> ReferenceBook
    """
    Create a :py:class:~pybatfish.datamodel.referencelibrary.ReferenceBook containing the given Capirca network definitions.

    :param definitions: a Capirca Naming definitions object, or the path to the Capirca definitions folder.
    :type definitions: capirca.lib.naming.Naming or str
    :param book_name: the name of the created ReferenceBook. Defaults to 'capirca'.
    :type book_name: str, optional
    """
    if not isinstance(definitions, naming.Naming):
        definitions = naming.Naming(naming_dir=definitions)

    groups = [_entry_to_group(network.name, network.items, definitions)
              for network in definitions.networks.values()]

    return ReferenceBook(name=book_name, addressGroups=groups)
