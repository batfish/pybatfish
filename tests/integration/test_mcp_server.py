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

"""Integration tests for the Batfish MCP server.

These tests run against a live Batfish service and are executed as part of
the integration_tests CI job (see .github/workflows/reusable-precommit.yml).
"""

from __future__ import annotations

import asyncio
import json
import typing
import uuid
from os.path import abspath, dirname, join, realpath
from typing import Any

import pytest
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from pybatfish.mcp.server import create_server

_this_dir = abspath(dirname(realpath(__file__)))

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_MCP_NETWORK = "mcp_integration_test_network"


def _call_tool(server: Any, tool_name: str, args: dict[str, Any]) -> Any:
    """Call an MCP tool synchronously and return the parsed JSON result."""
    # call_tool returns (list[ContentBlock], meta_dict) at runtime
    result = asyncio.run(server.call_tool(tool_name, args))
    content = result[0]
    first = content[0]
    assert isinstance(first, TextContent)
    return json.loads(first.text)


@pytest.fixture(scope="module")
def mcp() -> FastMCP:
    """Return a configured MCP server instance."""
    return create_server()


@pytest.fixture(scope="module")
def network(mcp: FastMCP) -> typing.Generator[str, None, None]:
    """Create a Batfish network for testing and clean it up afterwards."""
    _call_tool(mcp, "set_network", {"network": _MCP_NETWORK})
    yield _MCP_NETWORK
    try:
        _call_tool(mcp, "delete_network", {"network": _MCP_NETWORK})
    except Exception:
        pass


@pytest.fixture(scope="module")
def snapshot(mcp: FastMCP, network: str) -> typing.Generator[str, None, None]:
    """Initialize a snapshot from the canonical integration test directory."""
    snap_name = "mcp_snap_" + uuid.uuid4().hex[:8]
    _call_tool(
        mcp,
        "init_snapshot",
        {
            "network": network,
            "snapshot_path": join(_this_dir, "snapshot"),
            "snapshot_name": snap_name,
        },
    )
    yield snap_name
    try:
        _call_tool(mcp, "delete_snapshot", {"network": network, "snapshot": snap_name})
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Network management tests
# ---------------------------------------------------------------------------


def test_list_networks_includes_test_network(mcp: FastMCP, network: str) -> None:
    """list_networks should include our test network."""
    data = _call_tool(mcp, "list_networks", {})
    assert isinstance(data, list)
    assert network in data


def test_set_network_returns_name(mcp: FastMCP) -> None:
    """set_network should return a JSON object with the network name."""
    result = _call_tool(mcp, "set_network", {"network": _MCP_NETWORK})
    assert result == {"network": _MCP_NETWORK}


# ---------------------------------------------------------------------------
# Snapshot management tests
# ---------------------------------------------------------------------------


def test_list_snapshots_includes_test_snapshot(mcp: FastMCP, network: str, snapshot: str) -> None:
    """list_snapshots should include the snapshot we just created."""
    data = _call_tool(mcp, "list_snapshots", {"network": network})
    assert isinstance(data, list)
    assert snapshot in data


def test_init_snapshot_from_text(mcp: FastMCP, network: str) -> None:
    """init_snapshot_from_text should succeed and return a snapshot name."""
    config = "! Cisco IOS XE\nhostname test-router\n"
    snap_name = "mcp_text_snap_" + uuid.uuid4().hex[:8]
    try:
        result = _call_tool(
            mcp,
            "init_snapshot_from_text",
            {
                "network": network,
                "config_text": config,
                "snapshot_name": snap_name,
                "filename": "test-router.cfg",
            },
        )
        assert result == {"snapshot": snap_name}
        # Snapshot should now appear in the list
        snaps = _call_tool(mcp, "list_snapshots", {"network": network})
        assert snap_name in snaps
    finally:
        try:
            _call_tool(mcp, "delete_snapshot", {"network": network, "snapshot": snap_name})
        except Exception:
            pass


def test_delete_snapshot(mcp: FastMCP, network: str) -> None:
    """delete_snapshot should remove the snapshot from the network."""
    snap_name = "mcp_del_snap_" + uuid.uuid4().hex[:8]
    _call_tool(
        mcp,
        "init_snapshot",
        {
            "network": network,
            "snapshot_path": join(_this_dir, "snapshot"),
            "snapshot_name": snap_name,
        },
    )
    # Snapshot should exist
    snaps_before = _call_tool(mcp, "list_snapshots", {"network": network})
    assert snap_name in snaps_before

    result = _call_tool(mcp, "delete_snapshot", {"network": network, "snapshot": snap_name})
    assert result == {"deleted": snap_name}

    snaps_after = _call_tool(mcp, "list_snapshots", {"network": network})
    assert snap_name not in snaps_after


# ---------------------------------------------------------------------------
# Analysis tool tests
# ---------------------------------------------------------------------------


def test_get_ip_owners_returns_list(mcp: FastMCP, network: str, snapshot: str) -> None:
    """get_ip_owners should return a JSON array of IP ownership rows."""
    data = _call_tool(mcp, "get_ip_owners", {"network": network, "snapshot": snapshot})
    assert isinstance(data, list)


def test_get_node_properties_returns_list(mcp: FastMCP, network: str, snapshot: str) -> None:
    """get_node_properties should return a JSON array of node property rows."""
    data = _call_tool(mcp, "get_node_properties", {"network": network, "snapshot": snapshot})
    assert isinstance(data, list)


def test_get_interface_properties_returns_list(mcp: FastMCP, network: str, snapshot: str) -> None:
    """get_interface_properties should return a JSON array."""
    data = _call_tool(mcp, "get_interface_properties", {"network": network, "snapshot": snapshot})
    assert isinstance(data, list)


def test_get_routes_returns_list(mcp: FastMCP, network: str, snapshot: str) -> None:
    """get_routes should return a JSON array of route rows."""
    data = _call_tool(mcp, "get_routes", {"network": network, "snapshot": snapshot})
    assert isinstance(data, list)


def test_get_routes_no_legacy_nexthop_columns(mcp: FastMCP, network: str, snapshot: str) -> None:
    """get_routes must not include deprecated next-hop columns in results."""
    data = _call_tool(mcp, "get_routes", {"network": network, "snapshot": snapshot})
    legacy_cols = {"Next_Hop_IP", "Next_Hop_Interface", "Next_Hop_Type", "NextHopIp", "NextHopInterface"}
    for row in data:
        for col in legacy_cols:
            assert col not in row, f"Deprecated column '{col}' found in routes result"


def test_get_bgp_session_status_returns_list(mcp: FastMCP, network: str, snapshot: str) -> None:
    """get_bgp_session_status should return a JSON array."""
    data = _call_tool(mcp, "get_bgp_session_status", {"network": network, "snapshot": snapshot})
    assert isinstance(data, list)


def test_detect_loops_returns_list(mcp: FastMCP, network: str, snapshot: str) -> None:
    """detect_loops should return a JSON array (empty if no loops found)."""
    data = _call_tool(mcp, "detect_loops", {"network": network, "snapshot": snapshot})
    assert isinstance(data, list)


def test_get_undefined_references_returns_list(mcp: FastMCP, network: str, snapshot: str) -> None:
    """get_undefined_references should return a JSON array."""
    data = _call_tool(mcp, "get_undefined_references", {"network": network, "snapshot": snapshot})
    assert isinstance(data, list)


def test_analyze_acl_returns_list(mcp: FastMCP, network: str, snapshot: str) -> None:
    """analyze_acl should return a JSON array of unreachable ACL line rows."""
    data = _call_tool(mcp, "analyze_acl", {"network": network, "snapshot": snapshot})
    assert isinstance(data, list)
