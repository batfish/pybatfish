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

import re
from io import StringIO
from typing import Optional, Text  # noqa: F401

from capirca.lib import naming, policy

from pybatfish.client import capirca


def _load_test_definitions(netstr: str, svcstr: Optional[str] = None) -> naming.Naming:
    """Parses a Capirca Naming from the given network and services strings."""
    defs = naming.Naming()
    if netstr:
        defs._ParseFile(StringIO(netstr), "networks")
    if svcstr:
        defs._ParseFile(StringIO(svcstr), "services")
    return defs


TEST_DATABASE = """
    HOST_BITS = 1.2.3.4/8        # some prefix with host bits present

    RFC1918_10 = 10.0.0.0/8      # non-public

    RFC1918_172 = 172.16.0.0/12  # non-public

    RFC1918_192 = 192.168.0.0/16  # non-public

    RFC1918 = RFC1918_10
              RFC1918_172
              RFC1918_192

    LOOPBACK = 127.0.0.0/8  # loopback
               ::1/128       # ipv6 loopback

    RFC_3330 = 169.254.0.0/16  # special use IPv4 addresses - netdeploy

    RFC_6598 = 100.64.0.0/10   # Shared Address Space

    MULTICAST = 224.0.0.0/4  # IP multicast
                FF00::/8     # IPv6 multicast

    CLASS-E   = 240.0.0.0/4

    DENY-EXTERNAL-SRC =
        RFC1918
        LOOPBACK
        RFC_3330
        MULTICAST
        CLASS-E
        UNDEFINED
"""
DEFINITIONS = _load_test_definitions(TEST_DATABASE)


def _get_group(name):
    return capirca._entry_to_group(name, DEFINITIONS.networks[name].items, DEFINITIONS)


def test_entry_to_group_naive():
    g = _get_group("RFC1918_10")
    assert set(g.addresses) == {"10.0.0.0/8"}
    assert not g.childGroupNames

    g = _get_group("RFC1918_172")
    assert set(g.addresses) == {"172.16.0.0/12"}
    assert not g.childGroupNames

    g = _get_group("RFC1918_192")
    assert set(g.addresses) == {"192.168.0.0/16"}
    assert not g.childGroupNames


def test_entry_to_group_host_bits():
    g = _get_group("HOST_BITS")
    assert set(g.addresses) == {"1.0.0.0/8"}


def test_entry_to_group_recursive():
    g = _get_group("RFC1918")
    assert not g.addresses
    assert set(g.childGroupNames) == {"RFC1918_10", "RFC1918_172", "RFC1918_192"}


def test_entry_to_group_mixed_6_4(caplog):
    g = _get_group("LOOPBACK")
    assert set(g.addresses) == {"127.0.0.0/8"}
    assert not g.childGroupNames

    assert "Skipping IPv6 addresses in LOOPBACK" in caplog.text


def test_entry_to_group_error_undefined(caplog):
    g = _get_group("DENY-EXTERNAL-SRC")
    assert not g.addresses
    assert not g.childGroupNames

    assert "error converting DENY-EXTERNAL-SRC, creating empty group" in caplog.text


def test_create_reference_book():
    simple_database = """
        RFC1918_10 = 10.0.0.0/8      # non-public

        RFC1918_172 = 172.16.0.0/12  # non-public

        RFC1918_192 = 192.168.0.0/16  # non-public

        RFC1918 = RFC1918_10
                  RFC1918_172
                  RFC1918_192
    """
    defs = _load_test_definitions(simple_database)

    book = capirca.create_reference_book(defs)
    assert book.name == "capirca"
    assert len(book.addressGroups) == 4
    assert set(g.name for g in book.addressGroups) == {
        "RFC1918",
        "RFC1918_10",
        "RFC1918_172",
        "RFC1918_192",
    }
    assert not book.interfaceGroups

    book_custom = capirca.create_reference_book(defs, "testbook")
    assert book_custom.name == "testbook"
    assert book_custom.addressGroups == book.addressGroups
    assert book_custom.interfaceGroups == book.interfaceGroups


TEST_SVCS = """
SSH = 22/tcp
DNS = 53/udp
"""

TEST_POLICY = """
header {
  target:: arista some_acl
  target:: cisco some_acl
  target:: juniper some_acl
  target:: paloalto some_acl
}

term permit_ssh {
  protocol:: tcp
  destination-port:: SSH
  action:: accept
}

term permit_dns {
  protocol:: udp
  destination-port:: DNS
  action:: accept
}

term deny_all {
  action:: reject
}
"""


def test_get_acl_text():
    defs = _load_test_definitions(TEST_DATABASE, TEST_SVCS)
    pol = policy.ParsePolicy(TEST_POLICY, defs)

    cisco = capirca._get_acl_text(pol, "cisco")
    assert "permit tcp any any eq 22" in cisco
    assert "permit udp any any eq 53" in cisco
    assert "deny ip any any" in cisco

    cisco_wrong = capirca._get_acl_text(pol, " CISCO ")
    assert cisco_wrong == cisco

    juniper = capirca._get_acl_text(pol, "juniper")
    assert re.search(
        r"from {\s*(protocol tcp;\s*destination-port 22;|destination-port 22;\s*protocol tcp;)\s*}",
        juniper,
    )
    assert re.search(
        r"from {\s*(protocol udp;\s*destination-port 53;|destination-port 53;\s*protocol udp;)\s*}",
        juniper,
    )
    assert re.search(r"term deny_all {\s*then {\s*reject;\s*}\s*}", juniper)

    arista = capirca._get_acl_text(pol, "arista")
    assert "permit tcp any any eq ssh" in arista
    assert "permit udp any any eq domain" in arista
    assert "deny ip any any" in arista

    # palo alto currently unsupported
    try:
        capirca._get_acl_text(pol, "paloalto")
        assert False
    except ValueError as e:
        assert "Batfish" in str(e)
