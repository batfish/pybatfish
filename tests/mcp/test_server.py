# Copyright 2018 The Batfish Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the Batfish MCP server."""

from __future__ import annotations

import asyncio
import json
from typing import Any
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from pybatfish.datamodel import HeaderConstraints, Interface
from pybatfish.mcp.server import (
    _analysis_session,
    _build_header_constraints,
    _clear_session_cache,
    _df_to_json,
    _drop_legacy_nexthop_columns,
    _get_session,
    _load_sessions_config,
    _mgmt_session,
    _parse_interfaces,
    _register_session,
    _session_configs,
    create_server,
)

# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def _make_answer_frame(rows: list[dict[str, Any]]) -> MagicMock:
    """Return a mock that behaves like a Batfish question answering chain."""
    df = pd.DataFrame(rows)
    mock_frame = MagicMock()
    mock_frame.frame.return_value = df
    mock_answer = MagicMock()
    mock_answer.answer.return_value = mock_frame
    return mock_answer


def _make_session_mock(list_networks: list[str] | None = None, list_snapshots: list[str] | None = None) -> MagicMock:
    """Return a mock Session whose question chain is pre-configured."""
    session = MagicMock()
    session.list_networks.return_value = list_networks or []
    session.list_snapshots.return_value = list_snapshots or []
    return session


def _call_tool(server: Any, tool_name: str, args: dict[str, Any]) -> Any:
    """Call an MCP tool and return the parsed JSON result from the first content item."""
    content, _meta = asyncio.run(server.call_tool(tool_name, args))
    return json.loads(content[0].text)


# ---------------------------------------------------------------------------
# Unit tests for private helpers
# ---------------------------------------------------------------------------


class TestDfToJson:
    def test_converts_dataframe(self):
        df = pd.DataFrame([{"a": 1, "b": "x"}, {"a": 2, "b": "y"}])
        result = json.loads(_df_to_json(df))
        assert result == [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]

    def test_converts_non_dataframe(self):
        result = json.loads(_df_to_json({"key": "value"}))
        assert result == {"key": "value"}

    def test_handles_empty_dataframe(self):
        df = pd.DataFrame()
        result = json.loads(_df_to_json(df))
        assert result == []


class TestParseInterfaces:
    def test_empty_string(self):
        assert _parse_interfaces("") == []

    def test_single_interface(self):
        result = _parse_interfaces("router1[GigabitEthernet0/0]")
        assert len(result) == 1
        assert result[0].hostname == "router1"
        assert result[0].interface == "GigabitEthernet0/0"

    def test_multiple_interfaces(self):
        result = _parse_interfaces("r1[Gi0/0], r2[Gi0/1]")
        assert len(result) == 2
        assert result[0].hostname == "r1"
        assert result[1].hostname == "r2"

    def test_node_without_interface_raises(self):
        """Bare node tokens (no [interface]) must raise ValueError."""
        with pytest.raises(ValueError, match="node\\[interface\\]"):
            _parse_interfaces("router1")

    def test_mixed_entries_raises(self):
        """Any bare node token in a list must raise ValueError."""
        with pytest.raises(ValueError, match="node\\[interface\\]"):
            _parse_interfaces("r1[Gi0/0], r2")

    def test_invalid_format_error_message(self):
        """ValueError message should include the bad token."""
        with pytest.raises(ValueError, match="bare-node"):
            _parse_interfaces("bare-node")


class TestBuildHeaderConstraints:
    def test_empty_returns_empty_constraints(self):
        hc = _build_header_constraints()
        assert isinstance(hc, HeaderConstraints)
        assert hc.dstIps is None
        assert hc.srcIps is None

    def test_dst_ips_set(self):
        hc = _build_header_constraints(dst_ips="10.0.0.1")
        assert hc.dstIps == "10.0.0.1"

    def test_all_fields(self):
        hc = _build_header_constraints(
            dst_ips="10.0.0.1",
            src_ips="192.168.1.0/24",
            applications="SSH",
            ip_protocols="TCP",
            src_ports="1024-65535",
            dst_ports="22",
        )
        assert hc.dstIps == "10.0.0.1"
        assert hc.srcIps == "192.168.1.0/24"
        # HeaderConstraints normalises single-string values to lists
        assert "SSH" in hc.applications
        assert "TCP" in hc.ipProtocols
        assert hc.srcPorts == "1024-65535"
        assert hc.dstPorts == "22"


class TestSessionRegistry:
    """Tests for the session registry and config loading."""

    def setup_method(self):
        _clear_session_cache()

    def teardown_method(self):
        _clear_session_cache()

    def test_default_session_from_env(self, monkeypatch):
        monkeypatch.setenv("BATFISH_HOST", "env-host")
        _load_sessions_config()
        assert _session_configs["default"] == {"type": "bf", "params": {"host": "env-host"}}

    def test_default_session_localhost(self, monkeypatch):
        monkeypatch.delenv("BATFISH_HOST", raising=False)
        _load_sessions_config()
        assert _session_configs["default"]["params"]["host"] == "localhost"

    def test_load_from_config_file(self, tmp_path):
        config = {"prod": {"type": "bf", "params": {"host": "prod-host"}}}
        config_file = tmp_path / "sessions.json"
        config_file.write_text(json.dumps(config))
        _load_sessions_config(config_file)
        assert "prod" in _session_configs
        assert _session_configs["prod"]["params"]["host"] == "prod-host"
        # Default is still added
        assert "default" in _session_configs

    def test_config_file_overrides_default(self, tmp_path):
        config = {"default": {"type": "bf", "params": {"host": "custom-host"}}}
        config_file = tmp_path / "sessions.json"
        config_file.write_text(json.dumps(config))
        _load_sessions_config(config_file)
        assert _session_configs["default"]["params"]["host"] == "custom-host"

    def test_register_session_creates_and_caches(self):
        mock_session = MagicMock()
        with patch("pybatfish.mcp.server.Session") as MockSession:
            MockSession.get.return_value = mock_session
            _load_sessions_config()
            result = _register_session("test", "bf", host="test-host")
        assert result is mock_session
        assert _session_configs["test"] == {"type": "bf", "params": {"host": "test-host"}}

    def test_get_session_uses_session_get(self):
        mock_session = MagicMock()
        with patch("pybatfish.mcp.server.Session") as MockSession:
            MockSession.get.return_value = mock_session
            _load_sessions_config()
            result = _get_session("default")
        MockSession.get.assert_called_once_with("bf", host="localhost")
        assert result is mock_session

    def test_get_session_caches(self):
        mock_session = MagicMock()
        with patch("pybatfish.mcp.server.Session") as MockSession:
            MockSession.get.return_value = mock_session
            _load_sessions_config()
            s1 = _get_session("default")
            s2 = _get_session("default")
        assert MockSession.get.call_count == 1
        assert s1 is s2

    def test_get_session_unknown_raises(self):
        _load_sessions_config()
        with pytest.raises(ValueError, match="No session named"):
            _get_session("nonexistent")


class TestMgmtSession:
    """Tests for the _mgmt_session() helper."""

    def setup_method(self):
        _clear_session_cache()

    def teardown_method(self):
        _clear_session_cache()

    def test_returns_session(self):
        mock_session = MagicMock()
        with patch("pybatfish.mcp.server.Session") as MockSession:
            MockSession.get.return_value = mock_session
            _load_sessions_config()
            result = _mgmt_session("default")
        assert result is mock_session

    def test_sets_network_when_provided(self):
        mock_session = MagicMock()
        with patch("pybatfish.mcp.server.Session") as MockSession:
            MockSession.get.return_value = mock_session
            _load_sessions_config()
            _mgmt_session("default", "my-network")
        mock_session.set_network.assert_called_once_with("my-network")

    def test_skips_set_network_when_empty(self):
        mock_session = MagicMock()
        with patch("pybatfish.mcp.server.Session") as MockSession:
            MockSession.get.return_value = mock_session
            _load_sessions_config()
            _mgmt_session("default", "")
        mock_session.set_network.assert_not_called()

    def test_shares_cache_with_analysis_session(self):
        """_mgmt_session and _analysis_session must return the same cached session."""
        mock_session = MagicMock()
        with patch("pybatfish.mcp.server.Session") as MockSession:
            MockSession.get.return_value = mock_session
            _load_sessions_config()
            s1 = _mgmt_session("default")
            s2 = _analysis_session("default", "net1", "snap1")
        assert MockSession.get.call_count == 1
        assert s1 is s2


class TestAnalysisSession:
    """Tests for the _analysis_session() helper."""

    def setup_method(self):
        _clear_session_cache()

    def teardown_method(self):
        _clear_session_cache()

    def test_sets_network_and_snapshot(self):
        mock_session = MagicMock()
        with patch("pybatfish.mcp.server.Session") as MockSession:
            MockSession.get.return_value = mock_session
            _load_sessions_config()
            _analysis_session("default", "net1", "snap1")
        mock_session.set_network.assert_called_once_with("net1")
        mock_session.set_snapshot.assert_called_once_with("snap1")


class TestDropLegacyNexthopColumns:
    def test_drops_known_legacy_columns(self):
        df = pd.DataFrame(
            [
                {
                    "Node": "r1",
                    "Network": "10.0.0.0/8",
                    "Next_Hop": "ip 1.2.3.4",
                    "Next_Hop_IP": "1.2.3.4",
                    "Next_Hop_Interface": "GigabitEthernet0/0",
                }
            ]
        )
        result = _drop_legacy_nexthop_columns(df)
        assert "Next_Hop" in result.columns
        assert "Next_Hop_IP" not in result.columns
        assert "Next_Hop_Interface" not in result.columns

    def test_leaves_unrelated_columns_intact(self):
        df = pd.DataFrame([{"Node": "r1", "Network": "10.0.0.0/8", "Next_Hop": "ip 1.2.3.4"}])
        result = _drop_legacy_nexthop_columns(df)
        assert list(result.columns) == ["Node", "Network", "Next_Hop"]

    def test_handles_non_dataframe_gracefully(self):
        result = _drop_legacy_nexthop_columns({"key": "value"})
        assert result == {"key": "value"}

    def test_drops_camelcase_variants(self):
        df = pd.DataFrame([{"Node": "r1", "NextHopIp": "1.2.3.4", "NextHopInterface": "Gi0/0"}])
        result = _drop_legacy_nexthop_columns(df)
        assert "NextHopIp" not in result.columns
        assert "NextHopInterface" not in result.columns


# ---------------------------------------------------------------------------
# Integration-style tests for MCP server tools (Session is mocked)
# ---------------------------------------------------------------------------


PATCH_TARGET = "pybatfish.mcp.server._get_session"


class TestCreateServer:
    def setup_method(self):
        _clear_session_cache()

    def teardown_method(self):
        _clear_session_cache()

    def test_returns_fastmcp_instance(self):
        from mcp.server.fastmcp import FastMCP

        server = create_server()
        assert isinstance(server, FastMCP)

    def test_custom_name(self):
        server = create_server(name="MyBatfish")
        assert server.name == "MyBatfish"

    def test_default_session_injection(self):
        mock_session = MagicMock()
        mock_session.list_networks.return_value = ["net1"]
        server = create_server(default_session=mock_session)
        data = _call_tool(server, "list_networks", {})
        assert data == ["net1"]


class TestRegisterSessionTool:
    def setup_method(self):
        _clear_session_cache()

    def teardown_method(self):
        _clear_session_cache()

    def test_registers_session(self):
        mock_session = MagicMock()
        with patch("pybatfish.mcp.server.Session") as MockSession:
            MockSession.get.return_value = mock_session
            server = create_server()
            data = _call_tool(
                server,
                "register_session",
                {"name": "test", "type": "bf", "params": '{"host": "test-host"}'},
            )
        assert data == {"registered": "test", "type": "bf"}


class TestListSessionsTool:
    def setup_method(self):
        _clear_session_cache()

    def teardown_method(self):
        _clear_session_cache()

    def test_lists_sessions(self):
        server = create_server()
        data = _call_tool(server, "list_sessions", {})
        assert "default" in data


class TestListNetworksTool:
    def test_returns_network_list(self):
        mock_session = _make_session_mock(list_networks=["net1", "net2"])
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(server, "list_networks", {})
        assert data == ["net1", "net2"]

    def test_explicit_session_param(self):
        mock_session = _make_session_mock(list_networks=["net1"])
        with patch(PATCH_TARGET, return_value=mock_session) as mock_get:
            server = create_server()
            _call_tool(server, "list_networks", {"session": "default"})
        mock_get.assert_called_once_with("default")


class TestSetNetworkTool:
    def test_returns_network_name(self):
        mock_session = MagicMock()
        mock_session.set_network.return_value = "my-network"
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(server, "set_network", {"network": "my-network"})
        assert data == {"network": "my-network"}


class TestDeleteNetworkTool:
    def test_returns_deleted_name(self):
        mock_session = MagicMock()
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(server, "delete_network", {"network": "old-net"})
        assert data == {"deleted": "old-net"}
        mock_session.delete_network.assert_called_once_with("old-net")


class TestListSnapshotsTool:
    def test_returns_snapshot_list(self):
        mock_session = _make_session_mock(list_snapshots=["snap1", "snap2"])
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(server, "list_snapshots", {"network": "net1"})
        assert data == ["snap1", "snap2"]


class TestInitSnapshotTool:
    def test_returns_snapshot_name(self):
        mock_session = MagicMock()
        mock_session.init_snapshot.return_value = "my-snap"
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(
                server,
                "init_snapshot",
                {"network": "net1", "snapshot_path": "/path/to/snap"},
            )
        assert data == {"snapshot": "my-snap"}

    def test_passes_name_and_overwrite(self):
        mock_session = MagicMock()
        mock_session.init_snapshot.return_value = "named-snap"
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            _call_tool(
                server,
                "init_snapshot",
                {
                    "network": "net1",
                    "snapshot_path": "/path",
                    "snapshot_name": "named-snap",
                    "overwrite": True,
                },
            )
        mock_session.init_snapshot.assert_called_once_with("/path", name="named-snap", overwrite=True)


class TestInitSnapshotFromTextTool:
    def test_returns_snapshot_name(self):
        mock_session = MagicMock()
        mock_session.init_snapshot_from_text.return_value = "text-snap"
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(
                server,
                "init_snapshot_from_text",
                {"network": "net1", "config_text": "hostname router1"},
            )
        assert data == {"snapshot": "text-snap"}

    def test_passes_platform_when_set(self):
        mock_session = MagicMock()
        mock_session.init_snapshot_from_text.return_value = "snap"
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            _call_tool(
                server,
                "init_snapshot_from_text",
                {
                    "network": "net1",
                    "config_text": "config",
                    "platform": "arista",
                },
            )
        call_kwargs = mock_session.init_snapshot_from_text.call_args[1]
        assert call_kwargs["platform"] == "arista"

    def test_passes_none_platform_when_empty(self):
        mock_session = MagicMock()
        mock_session.init_snapshot_from_text.return_value = "snap"
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            _call_tool(
                server,
                "init_snapshot_from_text",
                {"network": "net1", "config_text": "config"},
            )
        call_kwargs = mock_session.init_snapshot_from_text.call_args[1]
        assert call_kwargs["platform"] is None


class TestDeleteSnapshotTool:
    def test_returns_deleted_name(self):
        mock_session = MagicMock()
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(server, "delete_snapshot", {"network": "net1", "snapshot": "snap1"})
        assert data == {"deleted": "snap1"}
        mock_session.delete_snapshot.assert_called_once_with("snap1")


class TestForkSnapshotTool:
    def test_basic_fork(self):
        mock_session = MagicMock()
        mock_session.fork_snapshot.return_value = "forked-snap"
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(
                server,
                "fork_snapshot",
                {"network": "net1", "base_snapshot": "base", "new_snapshot": "forked"},
            )
        assert data == {"snapshot": "forked-snap"}

    def test_deactivate_nodes(self):
        mock_session = MagicMock()
        mock_session.fork_snapshot.return_value = "forked"
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            _call_tool(
                server,
                "fork_snapshot",
                {
                    "network": "net1",
                    "base_snapshot": "base",
                    "deactivate_nodes": "r1,r2",
                },
            )
        call_kwargs = mock_session.fork_snapshot.call_args[1]
        assert call_kwargs["deactivate_nodes"] == ["r1", "r2"]

    def test_deactivate_interfaces(self):
        mock_session = MagicMock()
        mock_session.fork_snapshot.return_value = "forked"
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            _call_tool(
                server,
                "fork_snapshot",
                {
                    "network": "net1",
                    "base_snapshot": "base",
                    "deactivate_interfaces": "r1[Gi0/0]",
                },
            )
        call_kwargs = mock_session.fork_snapshot.call_args[1]
        assert call_kwargs["deactivate_interfaces"] == [Interface(hostname="r1", interface="Gi0/0")]


class TestRunTracerouteTool:
    def test_returns_json_rows(self):
        rows = [{"Flow": "f1", "Traces": "t1"}]
        mock_session = MagicMock()
        mock_session.q.traceroute.return_value = _make_answer_frame(rows)
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(
                server,
                "run_traceroute",
                {
                    "network": "net1",
                    "snapshot": "snap1",
                    "start_location": "router1",
                    "dst_ips": "10.0.0.1",
                },
            )
        assert len(data) == 1
        assert data[0]["Flow"] == "f1"

    def test_optional_header_params_passed(self):
        mock_session = MagicMock()
        mock_session.q.traceroute.return_value = _make_answer_frame([])
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            _call_tool(
                server,
                "run_traceroute",
                {
                    "network": "net1",
                    "snapshot": "snap1",
                    "start_location": "router1",
                    "dst_ips": "10.0.0.1",
                    "src_ips": "192.168.0.1",
                    "applications": "ssh",
                    "ip_protocols": "TCP",
                    "src_ports": "1024",
                    "dst_ports": "22",
                },
            )
        call_kwargs = mock_session.q.traceroute.call_args[1]
        assert call_kwargs["headers"].dstIps == "10.0.0.1"
        assert call_kwargs["headers"].srcIps == "192.168.0.1"


class TestRunBidirectionalTracerouteTool:
    def test_returns_json_rows(self):
        rows = [{"Forward_Flow": "f1", "Reverse_Flow": "f2"}]
        mock_session = MagicMock()
        mock_session.q.bidirectionalTraceroute.return_value = _make_answer_frame(rows)
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(
                server,
                "run_bidirectional_traceroute",
                {
                    "network": "net1",
                    "snapshot": "snap1",
                    "start_location": "router1",
                    "dst_ips": "10.0.0.1",
                },
            )
        assert len(data) == 1
        assert data[0]["Forward_Flow"] == "f1"


class TestCheckReachabilityTool:
    def test_basic_call(self):
        mock_session = MagicMock()
        mock_session.q.reachability.return_value = _make_answer_frame([{"Flow": "f", "Action": "ACCEPT"}])
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(
                server,
                "check_reachability",
                {"network": "net1", "snapshot": "snap1", "dst_ips": "8.8.8.8"},
            )
        assert data[0]["Action"] == "ACCEPT"

    def test_optional_params_passed(self):
        mock_session = MagicMock()
        mock_session.q.reachability.return_value = _make_answer_frame([])
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            _call_tool(
                server,
                "check_reachability",
                {
                    "network": "net1",
                    "snapshot": "snap1",
                    "src_locations": "router1",
                    "actions": "DENIED_IN,DROP",
                },
            )
        call_kwargs = mock_session.q.reachability.call_args[1]
        assert call_kwargs["pathConstraints"] == {"startLocation": "router1"}
        assert call_kwargs["actions"] == "DENIED_IN,DROP"


class TestAnalyzeAclTool:
    def test_returns_acl_rows(self):
        mock_session = MagicMock()
        mock_session.q.filterLineReachability.return_value = _make_answer_frame([{"Filter": "acl1"}])
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(
                server,
                "analyze_acl",
                {"network": "net1", "snapshot": "snap1"},
            )
        assert data[0]["Filter"] == "acl1"


class TestSearchFiltersTool:
    def test_permit_action_passed(self):
        mock_session = MagicMock()
        mock_session.q.searchFilters.return_value = _make_answer_frame([])
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            _call_tool(
                server,
                "search_filters",
                {"network": "net1", "snapshot": "snap1", "action": "PERMIT"},
            )
        call_kwargs = mock_session.q.searchFilters.call_args[1]
        assert call_kwargs["action"] == "PERMIT"


class TestGetRoutesTool:
    def test_returns_routes(self):
        mock_session = MagicMock()
        mock_session.q.routes.return_value = _make_answer_frame([{"Node": "r1", "Network": "0.0.0.0/0"}])
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(
                server,
                "get_routes",
                {"network": "net1", "snapshot": "snap1"},
            )
        assert data[0]["Node"] == "r1"

    def test_legacy_nexthop_columns_dropped(self):
        mock_session = MagicMock()
        mock_session.q.routes.return_value = _make_answer_frame(
            [
                {
                    "Node": "r1",
                    "Network": "0.0.0.0/0",
                    "Next_Hop": "ip 1.2.3.4",
                    "Next_Hop_IP": "1.2.3.4",
                    "Next_Hop_Interface": "GigabitEthernet0/0",
                }
            ]
        )
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(
                server,
                "get_routes",
                {"network": "net1", "snapshot": "snap1"},
            )
        assert "Next_Hop" in data[0]
        assert "Next_Hop_IP" not in data[0]
        assert "Next_Hop_Interface" not in data[0]

    def test_filters_passed(self):
        mock_session = MagicMock()
        mock_session.q.routes.return_value = _make_answer_frame([])
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            _call_tool(
                server,
                "get_routes",
                {
                    "network": "net1",
                    "snapshot": "snap1",
                    "nodes": "r1",
                    "vrfs": "default",
                    "network_prefix": "10.0.0.0/8",
                    "protocols": "bgp",
                },
            )
        call_kwargs = mock_session.q.routes.call_args[1]
        assert call_kwargs["nodes"] == "r1"
        assert call_kwargs["vrfs"] == "default"
        assert call_kwargs["network"] == "10.0.0.0/8"
        assert call_kwargs["protocols"] == "bgp"


class TestCompareRoutesTool:
    def test_calls_differential_answer(self):
        mock_frame_obj = MagicMock()
        mock_frame_obj.frame.return_value = pd.DataFrame([{"Node": "r1"}])
        mock_answer_obj = MagicMock()
        mock_answer_obj.answer.return_value = mock_frame_obj
        mock_session = MagicMock()
        mock_session.q.routes.return_value = mock_answer_obj

        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            _call_tool(
                server,
                "compare_routes",
                {
                    "network": "net1",
                    "snapshot": "snap-new",
                    "reference_snapshot": "snap-old",
                },
            )
        mock_answer_obj.answer.assert_called_once_with(snapshot="snap-new", reference_snapshot="snap-old")


class TestGetBgpSessionStatusTool:
    def test_returns_bgp_rows(self):
        mock_session = MagicMock()
        mock_session.q.bgpSessionStatus.return_value = _make_answer_frame([{"Node": "r1", "Status": "ESTABLISHED"}])
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(
                server,
                "get_bgp_session_status",
                {"network": "net1", "snapshot": "snap1"},
            )
        assert data[0]["Status"] == "ESTABLISHED"


class TestGetBgpSessionCompatibilityTool:
    def test_returns_compat_rows(self):
        mock_session = MagicMock()
        mock_session.q.bgpSessionCompatibility.return_value = _make_answer_frame([{"Node": "r1"}])
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(
                server,
                "get_bgp_session_compatibility",
                {"network": "net1", "snapshot": "snap1"},
            )
        assert data[0]["Node"] == "r1"


class TestGetNodePropertiesTool:
    def test_returns_node_properties(self):
        mock_session = MagicMock()
        mock_session.q.nodeProperties.return_value = _make_answer_frame([{"Node": "r1", "AS_Path_Access_Lists": []}])
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(
                server,
                "get_node_properties",
                {"network": "net1", "snapshot": "snap1", "nodes": "r1"},
            )
        assert data[0]["Node"] == "r1"


class TestGetInterfacePropertiesTool:
    def test_returns_interface_properties(self):
        mock_session = MagicMock()
        mock_session.q.interfaceProperties.return_value = _make_answer_frame([{"Interface": "r1[Gi0/0]"}])
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(
                server,
                "get_interface_properties",
                {"network": "net1", "snapshot": "snap1"},
            )
        assert data[0]["Interface"] == "r1[Gi0/0]"


class TestGetIpOwnersTool:
    def test_returns_ip_rows(self):
        mock_session = MagicMock()
        mock_session.q.ipOwners.return_value = _make_answer_frame([{"IP": "10.0.0.1", "Node": "r1"}])
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(
                server,
                "get_ip_owners",
                {"network": "net1", "snapshot": "snap1"},
            )
        assert data[0]["IP"] == "10.0.0.1"

    def test_duplicates_only_flag(self):
        mock_session = MagicMock()
        mock_session.q.ipOwners.return_value = _make_answer_frame([])
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            _call_tool(
                server,
                "get_ip_owners",
                {"network": "net1", "snapshot": "snap1", "duplicates_only": True},
            )
        mock_session.q.ipOwners.assert_called_once_with(duplicatesOnly=True)


class TestCompareFiltersTool:
    def test_calls_differential_answer(self):
        mock_frame_obj = MagicMock()
        mock_frame_obj.frame.return_value = pd.DataFrame([{"Node": "r1"}])
        mock_answer_obj = MagicMock()
        mock_answer_obj.answer.return_value = mock_frame_obj
        mock_session = MagicMock()
        mock_session.q.compareFilters.return_value = mock_answer_obj

        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            _call_tool(
                server,
                "compare_filters",
                {
                    "network": "net1",
                    "snapshot": "snap-new",
                    "reference_snapshot": "snap-old",
                },
            )
        mock_answer_obj.answer.assert_called_once_with(snapshot="snap-new", reference_snapshot="snap-old")


class TestGetUndefinedReferencesTool:
    def test_returns_reference_rows(self):
        mock_session = MagicMock()
        mock_session.q.undefinedReferences.return_value = _make_answer_frame([{"Node": "r1", "Ref_Name": "acl-foo"}])
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(
                server,
                "get_undefined_references",
                {"network": "net1", "snapshot": "snap1"},
            )
        assert data[0]["Ref_Name"] == "acl-foo"


class TestDetectLoopsTool:
    def test_returns_loop_rows(self):
        mock_session = MagicMock()
        mock_session.q.detectLoops.return_value = _make_answer_frame([{"Node": "r1"}])
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(
                server,
                "detect_loops",
                {"network": "net1", "snapshot": "snap1"},
            )
        assert data[0]["Node"] == "r1"

    def test_no_loops(self):
        mock_session = MagicMock()
        mock_session.q.detectLoops.return_value = _make_answer_frame([])
        with patch(PATCH_TARGET, return_value=mock_session):
            server = create_server()
            data = _call_tool(
                server,
                "detect_loops",
                {"network": "net1", "snapshot": "snap1"},
            )
        assert data == []


class TestToolListCompleteness:
    """Verify the server exposes the expected set of tools."""

    EXPECTED_TOOLS = {
        "register_session",
        "list_sessions",
        "list_networks",
        "set_network",
        "delete_network",
        "list_snapshots",
        "init_snapshot",
        "init_snapshot_from_text",
        "delete_snapshot",
        "fork_snapshot",
        "run_traceroute",
        "run_bidirectional_traceroute",
        "check_reachability",
        "analyze_acl",
        "search_filters",
        "get_routes",
        "compare_routes",
        "get_bgp_session_status",
        "get_bgp_session_compatibility",
        "get_node_properties",
        "get_interface_properties",
        "get_ip_owners",
        "compare_filters",
        "get_undefined_references",
        "detect_loops",
    }

    def setup_method(self):
        _clear_session_cache()

    def teardown_method(self):
        _clear_session_cache()

    def test_all_expected_tools_registered(self):
        server = create_server()
        tools = asyncio.run(server.list_tools())
        tool_names = {t.name for t in tools}
        assert self.EXPECTED_TOOLS == tool_names
