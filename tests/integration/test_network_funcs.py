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
import typing
from os.path import abspath, dirname, join, realpath
from typing import Optional, Sequence

from pytest import fixture, raises
from requests.exceptions import HTTPError

from pybatfish.client.consts import CoordConsts
from pybatfish.client.options import Options
from pybatfish.client.session import Session
from pybatfish.datamodel.primitives import AutoCompleteSuggestion, VariableType
from pybatfish.datamodel.referencelibrary import (
    NodeRolesData,
    ReferenceBook,
    RoleMapping,
)
from tests.common_util import requires_bf
from tests.conftest import COMPLETION_TYPES

_this_dir = abspath(dirname(realpath(__file__)))


@fixture(scope="module")
def bf() -> Session:
    return Session()


@fixture()
def network(bf: Session) -> typing.Generator[str, None, None]:
    name = bf.set_network()
    yield name
    # cleanup
    bf.delete_network(name)


def test_list_incomplete_works(bf: Session) -> None:
    """Test that list_incomplete_works succeeds"""
    network = "test_list_incomplete_works"
    bf.set_network(network)
    try:
        # Cannot reliably leave incomplete work, so just check the call succeeds
        ans = bf.list_incomplete_works()
        assert isinstance(ans, dict)
        assert CoordConsts.SVC_KEY_WORK_LIST in ans
        assert isinstance(ans[CoordConsts.SVC_KEY_WORK_LIST], str)
    finally:
        bf.delete_network(network)


@requires_bf("2024.07.01")
def test_delete_network_object(bf: Session, network: str) -> None:
    bf.put_network_object("new_object", "goodbye")
    bf.delete_network_object("new_object")
    # the object should be non-existent now
    with raises(HTTPError, match="404"):
        bf.get_network_object_text("new_object")


def test_set_network(bf: Session, network: str) -> None:
    try:
        assert bf.set_network("foobar") == "foobar"
    finally:
        bf.delete_network("foobar")

    name = bf.set_network()
    try:
        assert name.startswith(Options.default_network_prefix)
    finally:
        bf.delete_network(name)


def test_list_networks(bf: Session) -> None:
    name = "n1"
    try:
        bf.set_network(name)
        assert name in bf.list_networks()
    finally:
        bf.delete_network(name)


def test_add_node_roles_data(bf: Session) -> None:
    network_name = "n1"
    try:
        bf.set_network(network_name)
        mappings = [
            RoleMapping("mapping1", "(.*)-(.*)", {"type": [1], "index": [2]}, {})
        ]
        roles_data = NodeRolesData(None, ["type", "index"], mappings)
        bf.put_node_roles(roles_data)
        assert bf.get_node_roles() == roles_data
    finally:
        bf.delete_network(network_name)


@requires_bf("2024.07.01")
def test_get_network_object(bf: Session, network: str) -> None:
    # non-existent object should yield 404
    with raises(HTTPError, match="404"):
        bf.get_network_object_text("missing_object")
    # object should exist after being placed
    bf.put_network_object("new_object", "goodbye")
    assert bf.get_network_object_text("new_object") == "goodbye"


def test_put_node_roles(bf: Session) -> None:
    network_name = "n1"
    try:
        bf.set_network(network_name)
        mapping = RoleMapping(
            name="mapping", regex="(regex)", roleDimensionGroups={"dim1": [1]}
        )
        node_roles = NodeRolesData(
            defaultDimension="dim1", roleDimensionOrder=["dim1"], roleMappings=[mapping]
        )
        bf.put_node_roles(node_roles)
        assert bf.get_node_roles() == node_roles
    finally:
        bf.delete_network(network_name)


def test_put_reference_book(bf: Session) -> None:
    network_name = "n1"
    try:
        bf.set_network(network_name)
        book_name = "b1"
        book = ReferenceBook(book_name)
        bf.put_reference_book(book)
        assert bf.get_reference_book(book_name) == book
        # put again to check for idempotence
        bf.put_reference_book(book)
        assert bf.get_reference_book(book_name) == book
    finally:
        bf.delete_network(network_name)


def auto_complete_tester(bf: Session, completion_types: Sequence[VariableType]) -> None:
    name = bf.set_network()
    try:
        bf.init_snapshot(join(_this_dir, "snapshot"))
        for completion_type in completion_types:
            suggestions = bf.auto_complete(completion_type, ".*")
            # Not all completion types will have suggestions since this test snapshot only contains one empty config.
            # If a completion type is unsupported an error is thrown so this will test that no errors are thrown.
            if len(suggestions) > 0:
                assert isinstance(suggestions[0], AutoCompleteSuggestion)
    finally:
        bf.delete_network(name)


def auto_complete_tester_session(
    bf: Session,
    completion_types: Sequence[VariableType],
    max_suggestions: Optional[int] = None,
) -> None:
    name = bf.set_network()
    try:
        bf.init_snapshot(join(_this_dir, "snapshot"))
        for completion_type in completion_types:
            suggestions = bf.auto_complete(
                completion_type, ".*", max_suggestions=max_suggestions
            )
            if max_suggestions:
                assert len(suggestions) <= max_suggestions
            # Not all completion types will have suggestions since this test snapshot only contains one empty config.
            # If a completion type is unsupported an error is thrown so this will test that no errors are thrown.
            if len(suggestions) > 0:
                assert isinstance(suggestions[0], AutoCompleteSuggestion)
    finally:
        bf.delete_network(name)


def test_auto_complete(bf: Session) -> None:
    auto_complete_tester(bf, COMPLETION_TYPES)


def test_auto_complete_session(bf: Session) -> None:
    auto_complete_tester_session(bf, COMPLETION_TYPES)


@requires_bf("2022.08.17")
def test_auto_complete_limited_session(bf: Session) -> None:
    auto_complete_tester_session(bf, COMPLETION_TYPES, max_suggestions=1)


@requires_bf("2021.07.09")
def test_auto_complete_bgp_route_status_spec(bf: Session) -> None:
    """
    This type was newly added, so we test it separately. Move to conftest.py/COMPLETION_TYPES later.
    """
    auto_complete_tester_session(bf, [VariableType.BGP_ROUTE_STATUS_SPEC])


@requires_bf("2022.08.17")
def test_auto_complete_limited_bgp_route_status_spec(bf: Session) -> None:
    """
    This type was newly added, so we test it separately. Move to conftest.py/COMPLETION_TYPES later.
    """
    auto_complete_tester_session(
        bf, [VariableType.BGP_ROUTE_STATUS_SPEC], max_suggestions=1
    )
