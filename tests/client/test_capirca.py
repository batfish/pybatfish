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

from io import StringIO

from capirca.lib import naming

from pybatfish.client import capirca


def _load_test_definitions(defstr):
    # type: (str) -> naming.Naming
    """Converts the given string into a Capirca naming object."""
    def_file = StringIO(defstr)
    defs = naming.Naming()
    defs._ParseFile(def_file, 'networks')
    return defs


TEST_DATABASE = """
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
    return capirca._entry_to_group(name, DEFINITIONS.networks[name].items,
                                   DEFINITIONS)


def test_entry_to_group_naive():
    g = _get_group('RFC1918_10')
    assert set(g.addresses) == {'10.0.0.0/8'}
    assert not g.childGroupNames

    g = _get_group('RFC1918_172')
    assert set(g.addresses) == {'172.16.0.0/12'}
    assert not g.childGroupNames

    g = _get_group('RFC1918_192')
    assert set(g.addresses) == {'192.168.0.0/16'}
    assert not g.childGroupNames


def test_entry_to_group_recursive():
    g = _get_group('RFC1918')
    assert not g.addresses
    assert set(g.childGroupNames) == {'RFC1918_10', 'RFC1918_172',
                                      'RFC1918_192'}


def test_entry_to_group_mixed_6_4(caplog):
    g = _get_group('LOOPBACK')
    assert set(g.addresses) == {'127.0.0.0/8'}
    assert not g.childGroupNames

    assert 'Skipping IPv6 addresses in LOOPBACK' in caplog.text


def test_entry_to_group_error_undefined(caplog):
    g = _get_group('DENY-EXTERNAL-SRC')
    assert not g.addresses
    assert not g.childGroupNames

    assert 'error converting DENY-EXTERNAL-SRC, creating empty group' in caplog.text
