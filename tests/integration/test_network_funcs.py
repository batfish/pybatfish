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
from os.path import abspath, dirname, join, realpath

from pytest import fixture, raises
from requests.exceptions import HTTPError

from pybatfish.client.commands import (bf_add_node_role_dimension,
                                       bf_auto_complete,
                                       bf_delete_network,
                                       bf_delete_node_role_dimension,
                                       bf_get_node_role_dimension,
                                       bf_get_node_roles, bf_init_snapshot,
                                       bf_list_networks, bf_put_node_roles,
                                       bf_set_network)
from pybatfish.client.consts import COMPLETION_TYPES
from pybatfish.client.extended import (bf_get_network_object_text,
                                       bf_put_network_object)
from pybatfish.client.options import Options
from pybatfish.datamodel.primitives import AutoCompleteSuggestion
from pybatfish.datamodel.referencelibrary import NodeRoleDimension, \
    NodeRolesData

_this_dir = abspath(dirname(realpath(__file__)))


@fixture()
def network():
    name = bf_set_network()
    yield name
    # cleanup
    bf_delete_network(name)


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


def test_add_node_role_dimension():
    try:
        network_name = 'n1'
        bf_set_network(network_name)
        dim_name = 'd1'
        dim = NodeRoleDimension(dim_name)
        bf_add_node_role_dimension(dim)
        assert bf_get_node_role_dimension(dim_name) == dim
    finally:
        bf_delete_network(network_name)


def test_get_network_object(network):
    # non-existent object should yield 404
    with raises(HTTPError, match='404'):
        bf_get_network_object_text('missing_object')
    # object should exist after being placed
    bf_put_network_object('new_object', 'goodbye')
    assert bf_get_network_object_text('new_object') == 'goodbye'


def test_get_node_role_dimension():
    try:
        network_name = 'n1'
        bf_set_network(network_name)
        dim_name = 'd1'
        with raises(HTTPError, match='404'):
            bf_get_node_role_dimension(dim_name)
    finally:
        bf_delete_network(network_name)


def test_get_node_roles():
    try:
        network_name = 'n1'
        bf_set_network(network_name)
        assert bf_get_node_roles() == NodeRolesData([])
    finally:
        bf_delete_network(network_name)


def test_delete_node_role_dimension():
    try:
        network_name = 'n1'
        bf_set_network(network_name)
        dim_name = 'd1'
        dim = NodeRoleDimension(dim_name)
        bf_add_node_role_dimension(dim)
        # should not crash
        bf_get_node_role_dimension(dim_name)
        bf_delete_node_role_dimension(dim_name)
        # dimension should no longer exist
        with raises(HTTPError, match='404'):
            bf_get_node_role_dimension(dim_name)
        # second delete should fail
        with raises(HTTPError, match='404'):
            bf_delete_node_role_dimension(dim_name)

    finally:
        bf_delete_network(network_name)


def test_put_node_roles():
    try:
        network_name = 'n1'
        bf_set_network(network_name)
        node_roles = NodeRolesData([NodeRoleDimension('dim1')])
        bf_put_node_roles(node_roles)
        assert bf_get_node_roles() == node_roles
    finally:
        bf_delete_network(network_name)


def test_auto_complete():
    try:
        name = bf_set_network()
        bf_init_snapshot(join(_this_dir, 'snapshot'))
        for completion_type in COMPLETION_TYPES:
            suggestions = bf_auto_complete(completion_type, ".*")
            # Not all completion types will have suggestions since this test snapshot only contains one empty config.
            # If a completion type is unsupported an error is thrown so this will test that no errors are thrown.
            if len(suggestions) > 0:
                assert isinstance(suggestions[0], AutoCompleteSuggestion)
    finally:
        bf_delete_network(name)
