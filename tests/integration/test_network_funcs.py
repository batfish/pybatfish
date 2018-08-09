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

from pybatfish.client.commands import (bf_delete_network, bf_list_networks,
                                       bf_set_network)
from pybatfish.client.options import Options


def test_set_network():
    try:
        assert bf_set_network('foobar') == 'foobar'
    finally:
        bf_delete_network('foobar')

    name = bf_set_network()
    try:
        assert name.startswith(Options.default_network_prefix)
    finally:
        bf_delete_network(name)


def test_list_networks():
    try:
        name = bf_set_network()
        assert name in bf_list_networks()
    finally:
        bf_delete_network(name)
