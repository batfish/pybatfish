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

"""Batfish MCP server implementation (Beta).

.. warning::
    This MCP server is currently in **beta**. The tool names, parameters, and
    return formats may change in future releases without prior notice.

Exposes Batfish network analysis capabilities as MCP (Model Context Protocol)
tools, allowing AI agents to perform snapshot management, reachability
analysis, traceroute simulation, ACL/filter inspection, and routing queries.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    raise ImportError(
        "The 'mcp' package is required to use the Batfish MCP server. Install it with: pip install 'pybatfish[mcp]'"
    ) from e

from pathlib import Path

from pybatfish.client.session import Session
from pybatfish.datamodel import HeaderConstraints, Interface

# Legacy next-hop column names that Batfish is deprecating.  The structured
# ``Next_Hop`` column contains the same information in a richer format and
# should be preferred.  We drop these from route results so that consumers
# of this MCP server are not exposed to the deprecated columns.
_LEGACY_NEXTHOP_COLUMNS: frozenset[str] = frozenset(
    [
        "Next_Hop_IP",
        "Next_Hop_Interface",
        "NextHopIp",
        "NextHopInterface",
    ]
)

# Default path for the sessions configuration file.
_SESSIONS_CONFIG_PATH = Path.home() / ".batfish" / "sessions.json"

# Named session registry.  Sessions are created lazily from their stored
# configs and cached for the lifetime of the process.
_session_configs: dict[str, dict[str, Any]] = {}
_session_cache: dict[str, Session] = {}
_session_cache_lock = threading.Lock()


def _load_sessions_config(path: Path = _SESSIONS_CONFIG_PATH) -> None:
    """Load session configurations from a JSON file.

    The file should contain a JSON object mapping session names to
    ``{"type": "<entry_point_name>", "params": {<constructor_kwargs>}}``.
    If the file does not exist, a single ``"default"`` session is created
    using the ``BATFISH_HOST`` environment variable (or ``localhost``).
    """
    if path.exists():
        with open(path) as f:
            configs = json.load(f)
        for name, cfg in configs.items():
            _session_configs[name] = cfg
    if "default" not in _session_configs:
        host = os.environ.get("BATFISH_HOST", "localhost")
        _session_configs["default"] = {"type": "bf", "params": {"host": host}}


def _register_session(name: str, type_: str, **params: Any) -> Session:
    """Register and immediately create a named session."""
    _session_configs[name] = {"type": type_, "params": params}
    with _session_cache_lock:
        _session_cache.pop(name, None)
    return _get_session(name)


def _get_session(name: str = "default") -> Session:
    """Return the cached Session for the given name.

    Creates the session lazily from ``_session_configs`` on first access.
    """
    with _session_cache_lock:
        if name not in _session_cache:
            cfg = _session_configs.get(name)
            if cfg is None:
                raise ValueError(
                    f"No session named '{name}'. "
                    f"Available sessions: {sorted(_session_configs.keys())}. "
                    "Use the register_session tool to create one."
                )
            _session_cache[name] = Session.get(cfg["type"], **cfg.get("params", {}))
        return _session_cache[name]


def _clear_session_cache() -> None:
    """Clear the session cache and configs.

    Intended for use in tests and in situations where the caller wants to
    force sessions to be re-created.
    """
    with _session_cache_lock:
        _session_cache.clear()
        _session_configs.clear()


def _mgmt_session(session: str, network: str = "") -> Session:
    """Return the named session with an optional network set."""
    bf = _get_session(session)
    if network:
        bf.set_network(network)
    return bf


def _analysis_session(session: str, network: str, snapshot: str) -> Session:
    """Return the named session with network and snapshot set."""
    bf = _get_session(session)
    bf.set_network(network)
    bf.set_snapshot(snapshot)
    return bf


def _df_to_json(df: Any) -> str:
    """Convert a pandas DataFrame (or any value) to a JSON string."""
    if hasattr(df, "to_json"):
        result: str | None = df.to_json(orient="records", default_handler=str)
        return result or "[]"
    return json.dumps(df, default=str)


def _drop_legacy_nexthop_columns(df: Any) -> Any:
    """Drop deprecated next-hop columns from a routes DataFrame.

    Keeps only the structured ``Next_Hop`` column and removes the legacy
    ``Next_Hop_IP`` and ``Next_Hop_Interface`` columns (and their camelCase
    variants) that Batfish is deprecating.
    """
    if not hasattr(df, "columns"):
        return df
    cols_to_drop = [c for c in df.columns if c in _LEGACY_NEXTHOP_COLUMNS]
    if cols_to_drop:
        return df.drop(columns=cols_to_drop)
    return df


def create_server(
    name: str = "Batfish",
    default_session: Session | None = None,
    sessions_config: Path | None = None,
) -> FastMCP:
    """Create and return a configured Batfish MCP server (Beta).

    .. warning::
        This MCP server is currently in **beta**. Tool names, parameters, and
        return formats may change in future releases without prior notice.

    :param name: Name for the MCP server (default: "Batfish")
    :param default_session: Optional pre-created session to register as "default".
    :param sessions_config: Path to sessions JSON config file.
        Defaults to ``~/.batfish/sessions.json``.
    :return: Configured FastMCP server instance
    """
    # Load session configs from file (or set up BATFISH_HOST default).
    _load_sessions_config(sessions_config or _SESSIONS_CONFIG_PATH)

    # If a pre-created session was provided, register it as "default".
    if default_session is not None:
        with _session_cache_lock:
            _session_configs["default"] = {"type": "precreated", "params": {}}
            _session_cache["default"] = default_session

    mcp = FastMCP(
        name,
        instructions=(
            "[BETA] This server provides tools to interact with a Batfish network analysis service. "
            "Note: this MCP server is in beta — tool names and parameters may change in future releases. "
            "Use these tools to load network snapshots, run traceroutes, analyze reachability, "
            "inspect ACLs/firewall rules, query routing tables, and compare snapshots. "
            "Most tools require a 'network' parameter (the network name in Batfish) "
            "and a 'snapshot' parameter (the snapshot name). "
            "All tools accept an optional 'session' parameter to select a named session "
            "(default: 'default'). Use register_session to configure additional sessions. "
            "Start by listing networks or initializing a snapshot, then run analysis tools."
        ),
    )

    # -------------------------------------------------------------------------
    # Session management tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def register_session(
        name: str,
        type: str = "bf",
        params: str = "{}",
    ) -> str:
        """Register a new named session for use with all other tools.

        The session type must be a registered pybatfish session entry point
        (e.g. 'bf' for standard Batfish, 'dhalperianvdemo' for ANVDemo).

        :param name: Name for the session (used as the 'session' parameter in other tools).
        :param type: Session type entry point name (default: 'bf').
        :param params: JSON object of constructor keyword arguments for the session type
            (e.g. '{"host": "localhost"}' for bf, '{"endpoint": "https://...", "aws_profile": "..."}' for others).
        :return: JSON object confirming registration.
        """
        parsed_params = json.loads(params) if isinstance(params, str) else params
        _register_session(name, type, **parsed_params)
        return json.dumps({"registered": name, "type": type})

    @mcp.tool()
    def list_sessions() -> str:
        """List all registered session names and their types.

        :return: JSON object mapping session names to their types.
        """
        return json.dumps({
            name: cfg.get("type", "unknown")
            for name, cfg in _session_configs.items()
        })

    # -------------------------------------------------------------------------
    # Network management tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def list_networks(session: str = "default") -> str:
        """List all available networks on the Batfish server.

        :param session: Named session to use (default: 'default').
        :return: JSON array of network names.
        """
        bf = _mgmt_session(session)
        return json.dumps(bf.list_networks())

    @mcp.tool()
    def set_network(network: str, session: str = "default") -> str:
        """Create or select a network on the Batfish server.

        :param network: Name of the network to create or select.
        :param session: Named session to use (default: 'default').
        :return: JSON object with the active network name.
        """
        bf = _mgmt_session(session)
        name = bf.set_network(network)
        return json.dumps({"network": name})

    @mcp.tool()
    def delete_network(network: str, session: str = "default") -> str:
        """Delete a network from the Batfish server.

        :param network: Name of the network to delete.
        :param session: Named session to use (default: 'default').
        :return: JSON object confirming deletion.
        """
        bf = _mgmt_session(session)
        bf.delete_network(network)
        return json.dumps({"deleted": network})

    # -------------------------------------------------------------------------
    # Snapshot management tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def list_snapshots(network: str, session: str = "default") -> str:
        """List all snapshots within a network.

        :param network: Name of the network.
        :param session: Named session to use (default: 'default').
        :return: JSON array of snapshot names.
        """
        bf = _mgmt_session(session, network)
        return json.dumps(bf.list_snapshots())

    @mcp.tool()
    def init_snapshot(
        network: str,
        snapshot_path: str,
        snapshot_name: str = "",
        overwrite: bool = False,
        session: str = "default",
    ) -> str:
        """Initialize a new snapshot from a local directory or zip file.

        The snapshot directory or zip file should contain device configuration
        files under a ``configs/`` sub-directory.

        :param network: Name of the network to add the snapshot to.
        :param snapshot_path: Local path to a snapshot directory or zip file.
        :param snapshot_name: Optional name for the snapshot. Auto-generated if empty.
        :param overwrite: Whether to overwrite an existing snapshot with the same name.
        :param session: Named session to use (default: 'default').
        :return: JSON object with the initialized snapshot name.
        """
        bf = _mgmt_session(session, network)
        name = bf.init_snapshot(
            snapshot_path,
            name=snapshot_name or None,
            overwrite=overwrite,
        )
        return json.dumps({"snapshot": name})

    @mcp.tool()
    def init_snapshot_from_text(
        network: str,
        config_text: str,
        filename: str = "config",
        snapshot_name: str = "",
        platform: str = "",
        overwrite: bool = False,
        session: str = "default",
    ) -> str:
        """Initialize a single-device snapshot from configuration text.

        Useful for quickly loading one device's configuration without needing
        a local file or zip archive.

        :param network: Name of the network to add the snapshot to.
        :param config_text: Raw configuration text (e.g. output of "show running-config").
        :param filename: Filename to use inside the snapshot (default: 'config').
        :param snapshot_name: Optional name for the snapshot. Auto-generated if empty.
        :param platform: RANCID platform string (e.g. 'cisco-nx', 'arista', 'juniper').
            If empty, the platform is inferred from the configuration header.
        :param overwrite: Whether to overwrite an existing snapshot with the same name.
        :param session: Named session to use (default: 'default').
        :return: JSON object with the initialized snapshot name.
        """
        bf = _mgmt_session(session, network)
        name = bf.init_snapshot_from_text(
            config_text,
            filename=filename,
            snapshot_name=snapshot_name or None,
            platform=platform or None,
            overwrite=overwrite,
        )
        return json.dumps({"snapshot": name})

    @mcp.tool()
    def delete_snapshot(network: str, snapshot: str, session: str = "default") -> str:
        """Delete a snapshot from a network.

        :param network: Name of the network containing the snapshot.
        :param snapshot: Name of the snapshot to delete.
        :param session: Named session to use (default: 'default').
        :return: JSON object confirming deletion.
        """
        bf = _mgmt_session(session, network)
        bf.delete_snapshot(snapshot)
        return json.dumps({"deleted": snapshot})

    @mcp.tool()
    def fork_snapshot(
        network: str,
        base_snapshot: str,
        new_snapshot: str = "",
        deactivate_nodes: str = "",
        deactivate_interfaces: str = "",
        restore_nodes: str = "",
        restore_interfaces: str = "",
        overwrite: bool = False,
        session: str = "default",
    ) -> str:
        """Fork an existing snapshot, optionally deactivating or restoring nodes/interfaces.

        Use this to simulate failure scenarios (e.g. deactivate a node or link) or
        to restore previously deactivated elements.

        :param network: Name of the network containing the base snapshot.
        :param base_snapshot: Name of the snapshot to fork from.
        :param new_snapshot: Name for the new forked snapshot. Auto-generated if empty.
        :param deactivate_nodes: Comma-separated list of node names to deactivate.
        :param deactivate_interfaces: Comma-separated list of 'node[interface]' pairs to deactivate.
        :param restore_nodes: Comma-separated list of node names to restore.
        :param restore_interfaces: Comma-separated list of 'node[interface]' pairs to restore.
        :param overwrite: Whether to overwrite an existing snapshot with the same name.
        :param session: Named session to use (default: 'default').
        :return: JSON object with the forked snapshot name.
        """
        bf = _mgmt_session(session, network)

        deactivate_nodes_list = [n.strip() for n in deactivate_nodes.split(",") if n.strip()] or None
        restore_nodes_list = [n.strip() for n in restore_nodes.split(",") if n.strip()] or None

        deactivate_ifaces = _parse_interfaces(deactivate_interfaces)
        restore_ifaces = _parse_interfaces(restore_interfaces)

        name = bf.fork_snapshot(
            base_snapshot,
            name=new_snapshot or None,
            overwrite=overwrite,
            deactivate_nodes=deactivate_nodes_list,
            deactivate_interfaces=deactivate_ifaces or None,
            restore_nodes=restore_nodes_list,
            restore_interfaces=restore_ifaces or None,
        )
        return json.dumps({"snapshot": name})

    # -------------------------------------------------------------------------
    # Reachability and traceroute tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def run_traceroute(
        network: str,
        snapshot: str,
        start_location: str,
        dst_ips: str,
        src_ips: str = "",
        applications: str = "",
        ip_protocols: str = "",
        src_ports: str = "",
        dst_ports: str = "",
        session: str = "default",
    ) -> str:
        """Simulate a traceroute from a location to a destination IP address.

        Returns the forwarding path(s) a packet would take through the network,
        including all hops, interfaces, and any access-list hits.

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param start_location: Source location specifier (e.g. node name, interface).
        :param dst_ips: Destination IP address or prefix (e.g. '10.0.0.1').
        :param src_ips: Source IP address or prefix (optional).
        :param applications: Application specifier, e.g. 'ssh', 'HTTP' (optional).
        :param ip_protocols: IP protocol(s) e.g. 'TCP' (optional).
        :param src_ports: Source port(s) e.g. '1024-65535' (optional).
        :param dst_ports: Destination port(s) e.g. '22' (optional).
        :param session: Named session to use (default: 'default').
        :return: JSON array of traceroute result rows.
        """
        bf = _analysis_session(session, network, snapshot)

        headers = _build_header_constraints(
            dst_ips=dst_ips,
            src_ips=src_ips,
            applications=applications,
            ip_protocols=ip_protocols,
            src_ports=src_ports,
            dst_ports=dst_ports,
        )
        result = bf.q.traceroute(startLocation=start_location, headers=headers).answer().frame()  # type: ignore[attr-defined]
        return _df_to_json(result)

    @mcp.tool()
    def run_bidirectional_traceroute(
        network: str,
        snapshot: str,
        start_location: str,
        dst_ips: str,
        src_ips: str = "",
        applications: str = "",
        ip_protocols: str = "",
        src_ports: str = "",
        dst_ports: str = "",
        session: str = "default",
    ) -> str:
        """Simulate a bidirectional traceroute (forward + reverse paths).

        Returns both the forward path from source to destination and the
        reverse path from destination back to source.

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param start_location: Source location specifier (e.g. node name, interface).
        :param dst_ips: Destination IP address or prefix.
        :param src_ips: Source IP address or prefix (optional).
        :param applications: Application specifier (optional).
        :param ip_protocols: IP protocol(s) (optional).
        :param src_ports: Source port(s) (optional).
        :param dst_ports: Destination port(s) (optional).
        :param session: Named session to use (default: 'default').
        :return: JSON array of bidirectional traceroute result rows.
        """
        bf = _analysis_session(session, network, snapshot)

        headers = _build_header_constraints(
            dst_ips=dst_ips,
            src_ips=src_ips,
            applications=applications,
            ip_protocols=ip_protocols,
            src_ports=src_ports,
            dst_ports=dst_ports,
        )
        result = bf.q.bidirectionalTraceroute(startLocation=start_location, headers=headers).answer().frame()  # type: ignore[attr-defined]
        return _df_to_json(result)

    @mcp.tool()
    def check_reachability(
        network: str,
        snapshot: str,
        src_locations: str = "",
        dst_ips: str = "",
        src_ips: str = "",
        applications: str = "",
        ip_protocols: str = "",
        src_ports: str = "",
        dst_ports: str = "",
        actions: str = "",
        session: str = "default",
    ) -> str:
        """Check reachability between network locations.

        Determines which flows can successfully reach the destination, and which
        are dropped, denied, or otherwise blocked.

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param src_locations: Source location specifier (optional).
        :param dst_ips: Destination IP address or prefix (optional).
        :param src_ips: Source IP address or prefix (optional).
        :param applications: Application specifier (optional).
        :param ip_protocols: IP protocol(s) (optional).
        :param src_ports: Source port(s) (optional).
        :param dst_ports: Destination port(s) (optional).
        :param actions: Disposition filter, e.g. 'DENIED_IN,DENIED_OUT,DROP' (optional).
        :param session: Named session to use (default: 'default').
        :return: JSON array of reachability result rows.
        """
        bf = _analysis_session(session, network, snapshot)

        headers = _build_header_constraints(
            dst_ips=dst_ips,
            src_ips=src_ips,
            applications=applications,
            ip_protocols=ip_protocols,
            src_ports=src_ports,
            dst_ports=dst_ports,
        )
        kwargs: dict[str, Any] = {"headers": headers}
        if src_locations:
            kwargs["pathConstraints"] = {"startLocation": src_locations}
        if actions:
            kwargs["actions"] = actions

        result = bf.q.reachability(**kwargs).answer().frame()  # type: ignore[attr-defined]
        return _df_to_json(result)

    # -------------------------------------------------------------------------
    # ACL / filter analysis tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def analyze_acl(
        network: str,
        snapshot: str,
        filters: str = "",
        nodes: str = "",
        session: str = "default",
    ) -> str:
        """Identify unreachable (shadowed) lines in ACLs and firewall rules.

        Reports lines that can never be matched because earlier lines in the
        same filter already match the same traffic.

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param filters: Filter specifier to restrict analysis (optional).
        :param nodes: Node specifier to restrict analysis (optional).
        :param session: Named session to use (default: 'default').
        :return: JSON array of unreachable ACL/filter line rows.
        """
        bf = _analysis_session(session, network, snapshot)

        kwargs: dict[str, Any] = {}
        if filters:
            kwargs["filters"] = filters
        if nodes:
            kwargs["nodes"] = nodes

        result = bf.q.filterLineReachability(**kwargs).answer().frame()  # type: ignore[attr-defined]
        return _df_to_json(result)

    @mcp.tool()
    def search_filters(
        network: str,
        snapshot: str,
        filters: str = "",
        nodes: str = "",
        dst_ips: str = "",
        src_ips: str = "",
        applications: str = "",
        ip_protocols: str = "",
        src_ports: str = "",
        dst_ports: str = "",
        action: str = "",
        session: str = "default",
    ) -> str:
        """Search for flows that match specific filter (ACL/firewall) criteria.

        Finds concrete example flows that are permitted or denied by the
        specified filters, useful for validating ACL intent.

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param filters: Filter specifier (optional).
        :param nodes: Node specifier (optional).
        :param dst_ips: Destination IP address or prefix to match (optional).
        :param src_ips: Source IP address or prefix to match (optional).
        :param applications: Application specifier (optional).
        :param ip_protocols: IP protocol(s) (optional).
        :param src_ports: Source port(s) (optional).
        :param dst_ports: Destination port(s) (optional).
        :param action: Filter action: 'PERMIT' or 'DENY' (optional).
        :param session: Named session to use (default: 'default').
        :return: JSON array of matched flow rows.
        """
        bf = _analysis_session(session, network, snapshot)

        headers = _build_header_constraints(
            dst_ips=dst_ips,
            src_ips=src_ips,
            applications=applications,
            ip_protocols=ip_protocols,
            src_ports=src_ports,
            dst_ports=dst_ports,
        )
        kwargs: dict[str, Any] = {"headers": headers}
        if filters:
            kwargs["filters"] = filters
        if nodes:
            kwargs["nodes"] = nodes
        if action:
            kwargs["action"] = action

        result = bf.q.searchFilters(**kwargs).answer().frame()  # type: ignore[attr-defined]
        return _df_to_json(result)

    # -------------------------------------------------------------------------
    # Routing table tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def get_routes(
        network: str,
        snapshot: str,
        nodes: str = "",
        vrfs: str = "",
        network_prefix: str = "",
        protocols: str = "",
        session: str = "default",
    ) -> str:
        """Retrieve the routing table (RIB) from one or more devices.

        Legacy next-hop columns (Next_Hop_IP, Next_Hop_Interface)
        are omitted from the results; use the structured Next_Hop column instead.

        :param network: Name of the Batfish network.
        :param snapshot: Name of the snapshot.
        :param nodes: Node specifier to restrict results (optional).
        :param vrfs: VRF specifier to restrict results (optional).
        :param network_prefix: Prefix to filter routes by (optional).
        :param protocols: Routing protocol(s) to filter by, e.g. 'bgp,ospf' (optional).
        :param session: Named session to use (default: 'default').
        :return: JSON array of routing table rows.
        """
        bf = _analysis_session(session, network, snapshot)

        kwargs: dict[str, Any] = {}
        if nodes:
            kwargs["nodes"] = nodes
        if vrfs:
            kwargs["vrfs"] = vrfs
        if network_prefix:
            kwargs["network"] = network_prefix
        if protocols:
            kwargs["protocols"] = protocols

        result = _drop_legacy_nexthop_columns(bf.q.routes(**kwargs).answer().frame())  # type: ignore[attr-defined]
        return _df_to_json(result)

    @mcp.tool()
    def compare_routes(
        network: str,
        snapshot: str,
        reference_snapshot: str,
        nodes: str = "",
        vrfs: str = "",
        network_prefix: str = "",
        protocols: str = "",
        session: str = "default",
    ) -> str:
        """Compare routing tables between two snapshots to identify route changes.

        Useful for validating that a configuration change produces the expected
        routing changes (and no unintended ones).

        Legacy next-hop columns (Next_Hop_IP, Next_Hop_Interface)
        are omitted from the results; use the structured Next_Hop column instead.

        :param network: Name of the Batfish network.
        :param snapshot: Name of the candidate (new) snapshot.
        :param reference_snapshot: Name of the reference (baseline) snapshot.
        :param nodes: Node specifier to restrict results (optional).
        :param vrfs: VRF specifier to restrict results (optional).
        :param network_prefix: Prefix to filter routes by (optional).
        :param protocols: Routing protocol(s) to filter by (optional).
        :param session: Named session to use (default: 'default').
        :return: JSON array showing route differences (added/removed routes).
        """
        bf = _analysis_session(session, network, snapshot)

        kwargs: dict[str, Any] = {}
        if nodes:
            kwargs["nodes"] = nodes
        if vrfs:
            kwargs["vrfs"] = vrfs
        if network_prefix:
            kwargs["network"] = network_prefix
        if protocols:
            kwargs["protocols"] = protocols

        result = _drop_legacy_nexthop_columns(
            bf.q.routes(**kwargs).answer(snapshot=snapshot, reference_snapshot=reference_snapshot).frame()  # type: ignore[attr-defined]
        )
        return _df_to_json(result)

    # -------------------------------------------------------------------------
    # BGP tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def get_bgp_session_status(
        network: str,
        snapshot: str,
        nodes: str = "",
        remote_nodes: str = "",
        status: str = "",
        session: str = "default",
    ) -> str:
        """Get the status of BGP sessions in a snapshot.

        Reports which BGP sessions are established, incompatible, or missing.

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param nodes: Node specifier for local BGP speakers (optional).
        :param remote_nodes: Node specifier for remote BGP speakers (optional).
        :param status: BGP session status specifier to filter by (optional).
        :param session: Named session to use (default: 'default').
        :return: JSON array of BGP session status rows.
        """
        bf = _analysis_session(session, network, snapshot)

        kwargs: dict[str, Any] = {}
        if nodes:
            kwargs["nodes"] = nodes
        if remote_nodes:
            kwargs["remoteNodes"] = remote_nodes
        if status:
            kwargs["status"] = status

        result = bf.q.bgpSessionStatus(**kwargs).answer().frame()  # type: ignore[attr-defined]
        return _df_to_json(result)

    @mcp.tool()
    def get_bgp_session_compatibility(
        network: str,
        snapshot: str,
        nodes: str = "",
        remote_nodes: str = "",
        status: str = "",
        session: str = "default",
    ) -> str:
        """Check BGP session compatibility between peers.

        Returns the full BGP session compatibility table for the snapshot.
        Each row represents a BGP session and includes its compatibility status
        (e.g., UNIQUE_MATCH, NO_MATCH, DYNAMIC_MATCH) along with details about
        address families, authentication, and other parameters.  Use the
        *status* parameter to filter results to a specific compatibility status,
        such as ``NO_MATCH`` or ``NO_LOCAL_AS``, when you are interested in only
        mis-configured or incompatible sessions.

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param nodes: Node specifier for local BGP speakers (optional).
        :param remote_nodes: Node specifier for remote BGP speakers (optional).
        :param status: BGP compatibility status specifier to filter by (optional).
        :param session: Named session to use (default: 'default').
        :return: JSON array of BGP compatibility rows.
        """
        bf = _analysis_session(session, network, snapshot)

        kwargs: dict[str, Any] = {}
        if nodes:
            kwargs["nodes"] = nodes
        if remote_nodes:
            kwargs["remoteNodes"] = remote_nodes
        if status:
            kwargs["status"] = status

        result = bf.q.bgpSessionCompatibility(**kwargs).answer().frame()  # type: ignore[attr-defined]
        return _df_to_json(result)

    # -------------------------------------------------------------------------
    # Node and interface information tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def get_node_properties(
        network: str,
        snapshot: str,
        nodes: str = "",
        properties: str = "",
        session: str = "default",
    ) -> str:
        """Retrieve configuration properties of network nodes (routers/switches).

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param nodes: Node specifier to restrict results (optional).
        :param properties: Comma-separated list of property names to retrieve (optional).
        :param session: Named session to use (default: 'default').
        :return: JSON array of node property rows.
        """
        bf = _analysis_session(session, network, snapshot)

        kwargs: dict[str, Any] = {}
        if nodes:
            kwargs["nodes"] = nodes
        if properties:
            kwargs["properties"] = properties

        result = bf.q.nodeProperties(**kwargs).answer().frame()  # type: ignore[attr-defined]
        return _df_to_json(result)

    @mcp.tool()
    def get_interface_properties(
        network: str,
        snapshot: str,
        nodes: str = "",
        interfaces: str = "",
        properties: str = "",
        session: str = "default",
    ) -> str:
        """Retrieve configuration properties of network interfaces.

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param nodes: Node specifier to restrict results (optional).
        :param interfaces: Interface specifier to restrict results (optional).
        :param properties: Comma-separated list of property names to retrieve (optional).
        :param session: Named session to use (default: 'default').
        :return: JSON array of interface property rows.
        """
        bf = _analysis_session(session, network, snapshot)

        kwargs: dict[str, Any] = {}
        if nodes:
            kwargs["nodes"] = nodes
        if interfaces:
            kwargs["interfaces"] = interfaces
        if properties:
            kwargs["properties"] = properties

        result = bf.q.interfaceProperties(**kwargs).answer().frame()  # type: ignore[attr-defined]
        return _df_to_json(result)

    @mcp.tool()
    def get_ip_owners(
        network: str,
        snapshot: str,
        duplicates_only: bool = False,
        session: str = "default",
    ) -> str:
        """Get the mapping of IP addresses to network interfaces.

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param duplicates_only: If True, return only IPs assigned to multiple interfaces.
        :param session: Named session to use (default: 'default').
        :return: JSON array of IP ownership rows.
        """
        bf = _analysis_session(session, network, snapshot)

        result = bf.q.ipOwners(duplicatesOnly=duplicates_only).answer().frame()  # type: ignore[attr-defined]
        return _df_to_json(result)

    # -------------------------------------------------------------------------
    # Snapshot comparison tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def compare_filters(
        network: str,
        snapshot: str,
        reference_snapshot: str,
        filters: str = "",
        nodes: str = "",
        session: str = "default",
    ) -> str:
        """Compare ACL/firewall filter behavior between two snapshots.

        Identifies flows that are treated differently (permitted vs. denied)
        between the candidate snapshot and the reference (baseline) snapshot.

        :param network: Name of the network.
        :param snapshot: Name of the candidate (new) snapshot.
        :param reference_snapshot: Name of the reference (baseline) snapshot.
        :param filters: Filter specifier to restrict comparison (optional).
        :param nodes: Node specifier to restrict comparison (optional).
        :param session: Named session to use (default: 'default').
        :return: JSON array of filter difference rows.
        """
        bf = _analysis_session(session, network, snapshot)

        kwargs: dict[str, Any] = {}
        if filters:
            kwargs["filters"] = filters
        if nodes:
            kwargs["nodes"] = nodes

        result = bf.q.compareFilters(**kwargs).answer(snapshot=snapshot, reference_snapshot=reference_snapshot).frame()  # type: ignore[attr-defined]
        return _df_to_json(result)

    @mcp.tool()
    def get_undefined_references(
        network: str,
        snapshot: str,
        nodes: str = "",
        session: str = "default",
    ) -> str:
        """Find undefined references in device configurations.

        Reports references to named objects (e.g. ACLs, route-maps, prefix-lists)
        that are used but never defined, which can indicate configuration errors.

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param nodes: Node specifier to restrict results (optional).
        :param session: Named session to use (default: 'default').
        :return: JSON array of undefined reference rows.
        """
        bf = _analysis_session(session, network, snapshot)

        kwargs: dict[str, Any] = {}
        if nodes:
            kwargs["nodes"] = nodes

        result = bf.q.undefinedReferences(**kwargs).answer().frame()  # type: ignore[attr-defined]
        return _df_to_json(result)

    @mcp.tool()
    def detect_loops(
        network: str,
        snapshot: str,
        session: str = "default",
    ) -> str:
        """Detect forwarding loops in the network snapshot.

        Identifies any packet flows that would loop indefinitely through the
        network without being delivered.

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param session: Named session to use (default: 'default').
        :return: JSON array of forwarding loop rows (empty if no loops found).
        """
        bf = _analysis_session(session, network, snapshot)

        result = bf.q.detectLoops().answer().frame()  # type: ignore[attr-defined]
        return _df_to_json(result)

    return mcp


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _parse_interfaces(interfaces_str: str) -> list[Interface]:
    """Parse a comma-separated 'node[iface]' string into Interface objects.

    Each token must follow the ``node[interface]`` format.  Bare node names
    (e.g. ``"router1"`` without a bracketed interface) are rejected with a
    :exc:`ValueError`; use the *deactivate_nodes* / *restore_nodes* parameters
    for node-level operations instead.

    :param interfaces_str: Comma-separated interface specifiers, e.g.
        ``"r1[Gi0/0], r2[Ethernet1/1]"``.
    :raises ValueError: If a token does not match the ``node[interface]`` format.
    """
    result = []
    for item in interfaces_str.split(","):
        item = item.strip()
        if not item:
            continue
        if "[" in item and item.endswith("]"):
            node, iface = item[:-1].split("[", 1)
            result.append(Interface(hostname=node.strip(), interface=iface.strip()))
        else:
            raise ValueError(
                f"Invalid interface specifier {item!r}: expected 'node[interface]' format. "
                "Use deactivate_nodes/restore_nodes for node-level operations."
            )
    return result


def _build_header_constraints(
    dst_ips: str = "",
    src_ips: str = "",
    applications: str = "",
    ip_protocols: str = "",
    src_ports: str = "",
    dst_ports: str = "",
) -> HeaderConstraints:
    """Build a HeaderConstraints object from string parameters."""
    kwargs: dict[str, Any] = {}
    if dst_ips:
        kwargs["dstIps"] = dst_ips
    if src_ips:
        kwargs["srcIps"] = src_ips
    if applications:
        kwargs["applications"] = applications
    if ip_protocols:
        kwargs["ipProtocols"] = ip_protocols
    if src_ports:
        kwargs["srcPorts"] = src_ports
    if dst_ports:
        kwargs["dstPorts"] = dst_ports
    return HeaderConstraints(**kwargs)
