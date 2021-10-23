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

import pytest

from pybatfish.client.session import Session
from pybatfish.datamodel import HeaderConstraints
from pybatfish.exception import BatfishAssertException
from tests.common_util import requires_bf

_this_dir = abspath(dirname(realpath(__file__)))


# Just use a single session and snapshot for all passing assertion tests
@pytest.fixture(scope="module")
def session_pass():
    s = Session()
    name = s.init_snapshot(join(_this_dir, "snapshots", "asserts"))
    yield s
    s.delete_snapshot(name)


# Just use a single session and snapshot for all failing assertion tests
@pytest.fixture(scope="module")
def session_fail():
    s = Session()
    name = s.init_snapshot(join(_this_dir, "snapshots", "asserts_fail"))
    yield s
    s.delete_snapshot(name)


@pytest.mark.parametrize(
    "assert_func, params",
    [
        (
            "assert_filter_denies",
            {
                "filters": "/101/",
                "headers": HeaderConstraints(srcIps="12.34.56.78"),
                "startLocation": "@enter(node[GigabitEthernet1/0])",
            },
        ),
        ("assert_filter_has_no_unreachable_lines", {"filters": "/101/"}),
        (
            "assert_filter_permits",
            {
                "filters": "/101/",
                "headers": HeaderConstraints(srcIps="1.0.1.0", dstIps="8.8.8.8"),
                "startLocation": "@enter(node[GigabitEthernet1/0])",
            },
        ),
        (
            "assert_flows_fail",
            {
                "startLocation": "@enter(node[GigabitEthernet1/0])",
                "headers": HeaderConstraints(
                    srcIps="12.34.56.78", dstIps="1.0.1.0", ipProtocols=["TCP"]
                ),
            },
        ),
        (
            "assert_flows_succeed",
            {
                "startLocation": "@enter(node[GigabitEthernet1/0])",
                "headers": HeaderConstraints(
                    srcIps="2.0.1.0", dstIps="1.0.1.0", ipProtocols=["TCP"]
                ),
            },
        ),
        ("assert_no_incompatible_bgp_sessions", {}),
        ("assert_no_incompatible_ospf_sessions", {}),
        ("assert_no_unestablished_bgp_sessions", {}),
        ("assert_no_undefined_references", {}),
    ],
)
def test_asserts_pass(session_pass, assert_func, params):
    """Test that each assertion runs successfully."""
    # Assertion should run without errors and return True (passing assert)
    assert getattr(session_pass.asserts, assert_func)(**params)


@pytest.mark.parametrize(
    "assert_func, params",
    [
        (
            "assert_filter_denies",
            {
                "filters": "/101/",
                "headers": HeaderConstraints(srcIps="1.0.1.0", dstIps="8.8.8.8"),
                "startLocation": "@enter(node[GigabitEthernet1/0])",
            },
        ),
        ("assert_filter_has_no_unreachable_lines", {"filters": "/101/"}),
        (
            "assert_filter_permits",
            {
                "filters": "/101/",
                "headers": HeaderConstraints(srcIps="12.34.56.78"),
                "startLocation": "@enter(node[GigabitEthernet1/0])",
            },
        ),
        (
            "assert_flows_fail",
            {
                "startLocation": "@enter(node[GigabitEthernet1/0])",
                "headers": HeaderConstraints(
                    srcIps="2.0.1.0", dstIps="1.0.1.0", ipProtocols=["TCP"]
                ),
            },
        ),
        (
            "assert_flows_succeed",
            {
                "startLocation": "@enter(node[GigabitEthernet1/0])",
                "headers": HeaderConstraints(
                    srcIps="12.34.56.78", dstIps="1.0.1.0", ipProtocols=["TCP"]
                ),
            },
        ),
        ("assert_no_incompatible_bgp_sessions", {}),
        ("assert_no_incompatible_ospf_sessions", {}),
        ("assert_no_unestablished_bgp_sessions", {}),
        ("assert_no_undefined_references", {}),
    ],
)
def test_asserts_fail(session_fail, assert_func, params):
    """Test that each assertion fails as expected."""
    # Assertion should fail and raise a BatfishAssertException
    with pytest.raises(BatfishAssertException):
        getattr(session_fail.asserts, assert_func)(**params)


# Assertions which require a minimum release version of Pybatfish and Batfish


@requires_bf("2019.11.05")
def test_assert_no_duplicate_router_ids_pass(session_pass):
    """Test that there are no duplicate router IDs."""
    # Assertion should run without errors and return True (passing assert)
    assert session_pass.asserts.assert_no_duplicate_router_ids()


@requires_bf("2019.11.05")
def test_assert_no_duplicate_router_ids_fail(session_fail):
    """Test that there are duplicate router IDs."""
    # Assertion should fail and raise a BatfishAssertException
    with pytest.raises(BatfishAssertException):
        assert session_fail.asserts.assert_no_duplicate_router_ids()
