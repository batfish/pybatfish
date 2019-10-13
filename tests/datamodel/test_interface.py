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

from __future__ import absolute_import, print_function

import pytest

# test if an acl trace is deserialized properly
from pybatfish.datamodel.primitives import Interface


def test_str():
    # no escaping
    assert str(Interface(hostname="node", interface="iface")) == "node[iface]"

    # escape hostname
    assert str(Interface(hostname="0node", interface="iface")) == '"0node"[iface]'

    # escape interface
    assert str(Interface(hostname="node", interface="/iface")) == 'node["/iface"]'


def test_html():
    i = Interface(hostname="host", interface="special&")
    assert i._repr_html_() == "host[&quot;special&amp;&quot;]"
    i = Interface(hostname="host", interface="normal:0/0.0")
    assert i._repr_html_() == "host[normal:0/0.0]"


if __name__ == "__main__":
    pytest.main()
