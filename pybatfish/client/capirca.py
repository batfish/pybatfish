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

import ipaddress
import logging
import os
from typing import Any, Dict, Optional, TYPE_CHECKING, Union  # noqa: F401

try:
    from capirca.lib import naming, policy
except ImportError:
    logging.exception(
        "Capirca must be installed to use the Pybatfish Capirca extensions"
    )
    raise

from pybatfish.datamodel import AddressGroup, ReferenceBook

if TYPE_CHECKING:
    from pybatfish.client.session import Session  # noqa: F401

__all__ = ["create_reference_book", "init_snapshot_from_acl"]


def _item_to_python_repr(item, definitions):
    """Converts the given Capirca item into a typed Python object."""
    # Capirca comments are just appended to item strings
    s = item.split("#")[0].strip()

    # A reference to another network
    if s in definitions.networks:
        return s

    # IPv4 address / network
    try:
        return ipaddress.IPv4Address(s)
    except ValueError:
        pass
    try:
        return ipaddress.IPv4Network(s, strict=False)
    except ValueError:
        pass

    # IPv6 address / network
    try:
        return ipaddress.IPv6Address(s)
    except ValueError:
        pass
    try:
        return ipaddress.IPv6Network(s, strict=False)
    except ValueError:
        pass

    raise ValueError("Unknown how to convert {s}".format(s=s))


def _entry_to_group(name, items, definitions):
    """Converts one network definition into a Batfish AddressGroup."""
    logger = logging.getLogger(__name__)
    try:
        converted = [_item_to_python_repr(i, definitions) for i in items]
    except ValueError:
        logger.exception("error converting %s, creating empty group", name)
        return AddressGroup(name)

    if any(
        isinstance(c, (ipaddress.IPv6Address, ipaddress.IPv6Network)) for c in converted
    ):
        logger.warning("Skipping IPv6 addresses in %s", name)

    converted_v4 = [
        str(c)
        for c in converted
        if isinstance(c, (ipaddress.IPv4Address, ipaddress.IPv4Network))
    ]

    converted_group = [c for c in converted if isinstance(c, str)]

    return AddressGroup(
        "{name}".format(name=name),
        addresses=converted_v4,
        childGroupNames=converted_group,
    )


def _get_acl_text(pol, platform):
    # type: (policy.Policy, str) -> str
    # Capirca policy terms can have expiration dates, and Capirca warns if any
    # of the terms expire before this future date. Just set to a large number to
    # prevent warning - Capirca already warns itself if terms are expired.
    exp_info_weeks = 52 * 100  # ~100 years

    platform = platform.strip().lower()

    if platform == "arista":
        from capirca.lib import arista

        return str(arista.Arista(pol, exp_info_weeks))
    elif platform == "cisco" or platform == "cisco-nx":
        from capirca.lib import cisco

        return str(cisco.Cisco(pol, exp_info_weeks))
    elif platform == "cisco-xr":
        from capirca.lib import ciscoxr

        return str(ciscoxr.CiscoXR(pol, exp_info_weeks))
    elif platform == "ciscoasa":
        from capirca.lib import ciscoasa

        return str(ciscoasa.CiscoASA(pol, exp_info_weeks))
    elif platform == "juniper":
        from capirca.lib import juniper

        return str(juniper.Juniper(pol, exp_info_weeks))
    elif platform == "juniper-srx":
        from capirca.lib import junipersrx

        return str(junipersrx.JuniperSRX(pol, exp_info_weeks))
    elif platform == "paloalto":
        # from capirca.lib import paloaltofw
        # return str(paloaltofw.PaloAltoFW(pol, exp_info_weeks))
        raise ValueError(
            "Capirca generates Palo Alto ACLs in XML form, which Batfish does not yet parse"
        )
    else:
        raise ValueError(
            "Either Capirca or Pybatfish does not handle converting to ACLs in platform: "
            + platform
        )


def _init_definitions(definitions_or_path):
    # type: (Union[str, naming.Naming]) -> naming.Naming
    if isinstance(definitions_or_path, naming.Naming):
        return definitions_or_path

    return naming.Naming(naming_dir=definitions_or_path)


def init_snapshot_from_acl(
    session,
    pol,
    definitions,
    platform,
    filename=None,
    snapshot_name=None,
    overwrite=False,
    extra_args=None,
):
    # type: (Session, Union[str, policy.Policy], Union[str, naming.Naming], str, Optional[str], Optional[str], bool, Optional[Dict[str, Any]]) -> str
    """
    Initialize a snapshot containing a single host with the given ACL.

    :param session: the Pybatfish session in which the snapshot is created.
    :type session: a :py:class:~pybatfish.client.session.Session object
    :param pol: a Capirca Policy object, or the path to the Capirca policy file.
    :type pol: capirca.lib.policy.Policy or str
    :param definitions: a Capirca Naming definitions object, or the path to the
       Capirca definitions folder.
    :type definitions: capirca.lib.naming.Naming or str
    :param platform: the RANCID router.db name for the device platform,
       i.e., "cisco-nx", "arista", "f5", or "cisco-xr" for above examples.
       See https://www.shrubbery.net/rancid/man/router.db.5.html
    :type platform: str
    :param filename: name of the configuration file created, 'config' by
       default. This is used as the default hostname in Batfish for the created
       device.
    :type filename: str
    :param filename: name of the configuration file created, 'config' by
       default.
    :type filename: str
    :param snapshot_name: name of the snapshot to initialize
    :type snapshot_name: str
    :param overwrite: whether or not to overwrite an existing snapshot with
       the same name.
    :type overwrite: bool
    :param extra_args: extra arguments to be passed to the parse command
    :type extra_args: dict
    """
    definitions = _init_definitions(definitions)

    if not isinstance(pol, policy.Policy):
        with open(pol, "r") as pol_file:
            pol_text = pol_file.read()
        pol_dir = os.path.dirname(pol)

        # Capirca can optimize ACL outputs, but this is not well-documented.
        # Since we will likely be using Batfish to analyze the "raw" Capirca
        # config, disable optimization.
        optimize = False

        pol = policy.ParsePolicy(
            pol_text, definitions, base_dir=pol_dir, optimize=optimize
        )

    file_text = _get_acl_text(pol, platform)

    return session.init_snapshot_from_text(
        file_text,
        filename=filename,
        platform=platform,
        snapshot_name=snapshot_name,
        overwrite=overwrite,
        extra_args=extra_args,
    )


def create_reference_book(definitions, book_name="capirca"):
    # type: (Union[str, naming.Naming], str) -> ReferenceBook
    """
    Create a :py:class:~pybatfish.datamodel.referencelibrary.ReferenceBook containing the given Capirca network definitions.

    :param definitions: a Capirca Naming definitions object, or the path to the
       Capirca definitions folder.
    :type definitions: capirca.lib.naming.Naming or str
    :param book_name: the name of the created ReferenceBook. Defaults to
       'capirca'.
    :type book_name: str, optional
    """
    definitions = _init_definitions(definitions)

    groups = [
        _entry_to_group(network.name, network.items, definitions)
        for network in definitions.networks.values()
    ]

    return ReferenceBook(name=book_name, addressGroups=groups)
