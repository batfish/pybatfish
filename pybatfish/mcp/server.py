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

"""Batfish MCP server implementation.

Exposes Batfish network analysis capabilities as MCP (Model Context Protocol)
tools, allowing AI agents to perform snapshot management, reachability
analysis, traceroute simulation, ACL/filter inspection, and routing queries.
"""

from __future__ import annotations

import json
import os
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError as e:
    raise ImportError(
        "The 'mcp' package is required to use the Batfish MCP server. Install it with: pip install 'pybatfish[mcp]'"
    ) from e

from pybatfish.client.session import Session
from pybatfish.datamodel import HeaderConstraints, Interface


def _get_session(host: str, load_questions: bool = True) -> Session:
    """Create a Batfish Session for the given host."""
    return Session(host=host, load_questions=load_questions)


def _df_to_json(df: Any) -> str:
    """Convert a pandas DataFrame (or any value) to a JSON string."""
    if hasattr(df, "to_json"):
        return df.to_json(orient="records", default_handler=str)
    return json.dumps(df, default=str)


def create_server(name: str = "Batfish") -> FastMCP:
    """Create and return a configured Batfish MCP server.

    :param name: Name for the MCP server (default: "Batfish")
    :return: Configured FastMCP server instance
    """
    mcp = FastMCP(
        name,
        instructions=(
            "This server provides tools to interact with a Batfish network analysis service. "
            "Use these tools to load network snapshots, run traceroutes, analyze reachability, "
            "inspect ACLs/firewall rules, query routing tables, and compare snapshots. "
            "Most tools require a 'host' parameter (Batfish server hostname, defaults to "
            "the BATFISH_HOST environment variable or 'localhost'), a 'network' parameter "
            "(the network name in Batfish), and a 'snapshot' parameter (the snapshot name). "
            "Start by listing networks or initializing a snapshot, then run analysis tools."
        ),
    )

    # -------------------------------------------------------------------------
    # Network management tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def bf_list_networks(host: str = "") -> str:
        """List all available networks on the Batfish server.

        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON array of network names.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host, load_questions=False)
        return json.dumps(bf.list_networks())

    @mcp.tool()
    def bf_set_network(network: str, host: str = "") -> str:
        """Create or select a network on the Batfish server.

        :param network: Name of the network to create or select.
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON object with the active network name.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host, load_questions=False)
        name = bf.set_network(network)
        return json.dumps({"network": name})

    @mcp.tool()
    def bf_delete_network(network: str, host: str = "") -> str:
        """Delete a network from the Batfish server.

        :param network: Name of the network to delete.
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON object confirming deletion.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host, load_questions=False)
        bf.delete_network(network)
        return json.dumps({"deleted": network})

    # -------------------------------------------------------------------------
    # Snapshot management tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def bf_list_snapshots(network: str, host: str = "") -> str:
        """List all snapshots within a network.

        :param network: Name of the network.
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON array of snapshot names.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host, load_questions=False)
        bf.set_network(network)
        return json.dumps(bf.list_snapshots())

    @mcp.tool()
    def bf_init_snapshot(
        network: str,
        snapshot_path: str,
        snapshot_name: str = "",
        overwrite: bool = False,
        host: str = "",
    ) -> str:
        """Initialize a new snapshot from a local directory or zip file.

        The snapshot directory or zip file should contain device configuration
        files under a ``configs/`` sub-directory.

        :param network: Name of the network to add the snapshot to.
        :param snapshot_path: Local path to a snapshot directory or zip file.
        :param snapshot_name: Optional name for the snapshot. Auto-generated if empty.
        :param overwrite: Whether to overwrite an existing snapshot with the same name.
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON object with the initialized snapshot name.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host)
        bf.set_network(network)
        name = bf.init_snapshot(
            snapshot_path,
            name=snapshot_name or None,
            overwrite=overwrite,
        )
        return json.dumps({"snapshot": name})

    @mcp.tool()
    def bf_init_snapshot_from_text(
        network: str,
        config_text: str,
        filename: str = "config",
        snapshot_name: str = "",
        platform: str = "",
        overwrite: bool = False,
        host: str = "",
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
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON object with the initialized snapshot name.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host)
        bf.set_network(network)
        name = bf.init_snapshot_from_text(
            config_text,
            filename=filename,
            snapshot_name=snapshot_name or None,
            platform=platform or None,
            overwrite=overwrite,
        )
        return json.dumps({"snapshot": name})

    @mcp.tool()
    def bf_delete_snapshot(network: str, snapshot: str, host: str = "") -> str:
        """Delete a snapshot from a network.

        :param network: Name of the network containing the snapshot.
        :param snapshot: Name of the snapshot to delete.
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON object confirming deletion.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host, load_questions=False)
        bf.set_network(network)
        bf.delete_snapshot(snapshot)
        return json.dumps({"deleted": snapshot})

    @mcp.tool()
    def bf_fork_snapshot(
        network: str,
        base_snapshot: str,
        new_snapshot: str = "",
        deactivate_nodes: str = "",
        deactivate_interfaces: str = "",
        restore_nodes: str = "",
        restore_interfaces: str = "",
        overwrite: bool = False,
        host: str = "",
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
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON object with the forked snapshot name.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host, load_questions=False)
        bf.set_network(network)

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
    def bf_run_traceroute(
        network: str,
        snapshot: str,
        start_location: str,
        dst_ips: str,
        src_ips: str = "",
        applications: str = "",
        ip_protocols: str = "",
        src_ports: str = "",
        dst_ports: str = "",
        host: str = "",
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
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON array of traceroute result rows.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host)
        bf.set_network(network)
        bf.set_snapshot(snapshot)

        headers = _build_header_constraints(
            dst_ips=dst_ips,
            src_ips=src_ips,
            applications=applications,
            ip_protocols=ip_protocols,
            src_ports=src_ports,
            dst_ports=dst_ports,
        )
        result = bf.q.traceroute(startLocation=start_location, headers=headers).answer().frame()
        return _df_to_json(result)

    @mcp.tool()
    def bf_run_bidirectional_traceroute(
        network: str,
        snapshot: str,
        start_location: str,
        dst_ips: str,
        src_ips: str = "",
        applications: str = "",
        ip_protocols: str = "",
        src_ports: str = "",
        dst_ports: str = "",
        host: str = "",
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
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON array of bidirectional traceroute result rows.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host)
        bf.set_network(network)
        bf.set_snapshot(snapshot)

        headers = _build_header_constraints(
            dst_ips=dst_ips,
            src_ips=src_ips,
            applications=applications,
            ip_protocols=ip_protocols,
            src_ports=src_ports,
            dst_ports=dst_ports,
        )
        result = bf.q.bidirectionalTraceroute(startLocation=start_location, headers=headers).answer().frame()
        return _df_to_json(result)

    @mcp.tool()
    def bf_check_reachability(
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
        host: str = "",
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
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON array of reachability result rows.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host)
        bf.set_network(network)
        bf.set_snapshot(snapshot)

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

        result = bf.q.reachability(**kwargs).answer().frame()
        return _df_to_json(result)

    # -------------------------------------------------------------------------
    # ACL / filter analysis tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def bf_analyze_acl(
        network: str,
        snapshot: str,
        filters: str = "",
        nodes: str = "",
        host: str = "",
    ) -> str:
        """Identify unreachable (shadowed) lines in ACLs and firewall rules.

        Reports lines that can never be matched because earlier lines in the
        same filter already match the same traffic.

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param filters: Filter specifier to restrict analysis (optional).
        :param nodes: Node specifier to restrict analysis (optional).
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON array of unreachable ACL/filter line rows.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host)
        bf.set_network(network)
        bf.set_snapshot(snapshot)

        kwargs: dict[str, Any] = {}
        if filters:
            kwargs["filters"] = filters
        if nodes:
            kwargs["nodes"] = nodes

        result = bf.q.filterLineReachability(**kwargs).answer().frame()
        return _df_to_json(result)

    @mcp.tool()
    def bf_search_filters(
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
        host: str = "",
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
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON array of matched flow rows.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host)
        bf.set_network(network)
        bf.set_snapshot(snapshot)

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

        result = bf.q.searchFilters(**kwargs).answer().frame()
        return _df_to_json(result)

    # -------------------------------------------------------------------------
    # Routing table tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def bf_get_routes(
        network: str,
        snapshot: str,
        nodes: str = "",
        vrfs: str = "",
        network_prefix: str = "",
        protocols: str = "",
        host: str = "",
    ) -> str:
        """Retrieve the routing table (RIB) from one or more devices.

        :param network: Name of the Batfish network.
        :param snapshot: Name of the snapshot.
        :param nodes: Node specifier to restrict results (optional).
        :param vrfs: VRF specifier to restrict results (optional).
        :param network_prefix: Prefix to filter routes by (optional).
        :param protocols: Routing protocol(s) to filter by, e.g. 'bgp,ospf' (optional).
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON array of routing table rows.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host)
        bf.set_network(network)
        bf.set_snapshot(snapshot)

        kwargs: dict[str, Any] = {}
        if nodes:
            kwargs["nodes"] = nodes
        if vrfs:
            kwargs["vrfs"] = vrfs
        if network_prefix:
            kwargs["network"] = network_prefix
        if protocols:
            kwargs["protocols"] = protocols

        result = bf.q.routes(**kwargs).answer().frame()
        return _df_to_json(result)

    @mcp.tool()
    def bf_compare_routes(
        network: str,
        snapshot: str,
        reference_snapshot: str,
        nodes: str = "",
        vrfs: str = "",
        network_prefix: str = "",
        protocols: str = "",
        host: str = "",
    ) -> str:
        """Compare routing tables between two snapshots to identify route changes.

        Useful for validating that a configuration change produces the expected
        routing changes (and no unintended ones).

        :param network: Name of the Batfish network.
        :param snapshot: Name of the candidate (new) snapshot.
        :param reference_snapshot: Name of the reference (baseline) snapshot.
        :param nodes: Node specifier to restrict results (optional).
        :param vrfs: VRF specifier to restrict results (optional).
        :param network_prefix: Prefix to filter routes by (optional).
        :param protocols: Routing protocol(s) to filter by (optional).
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON array showing route differences (added/removed routes).
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host)
        bf.set_network(network)
        bf.set_snapshot(snapshot)

        kwargs: dict[str, Any] = {}
        if nodes:
            kwargs["nodes"] = nodes
        if vrfs:
            kwargs["vrfs"] = vrfs
        if network_prefix:
            kwargs["network"] = network_prefix
        if protocols:
            kwargs["protocols"] = protocols

        result = bf.q.routes(**kwargs).answer(snapshot=snapshot, reference_snapshot=reference_snapshot).frame()
        return _df_to_json(result)

    # -------------------------------------------------------------------------
    # BGP tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def bf_get_bgp_session_status(
        network: str,
        snapshot: str,
        nodes: str = "",
        remote_nodes: str = "",
        status: str = "",
        host: str = "",
    ) -> str:
        """Get the status of BGP sessions in a snapshot.

        Reports which BGP sessions are established, incompatible, or missing.

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param nodes: Node specifier for local BGP speakers (optional).
        :param remote_nodes: Node specifier for remote BGP speakers (optional).
        :param status: BGP session status specifier to filter by (optional).
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON array of BGP session status rows.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host)
        bf.set_network(network)
        bf.set_snapshot(snapshot)

        kwargs: dict[str, Any] = {}
        if nodes:
            kwargs["nodes"] = nodes
        if remote_nodes:
            kwargs["remoteNodes"] = remote_nodes
        if status:
            kwargs["status"] = status

        result = bf.q.bgpSessionStatus(**kwargs).answer().frame()
        return _df_to_json(result)

    @mcp.tool()
    def bf_get_bgp_session_compatibility(
        network: str,
        snapshot: str,
        nodes: str = "",
        remote_nodes: str = "",
        status: str = "",
        host: str = "",
    ) -> str:
        """Check BGP session compatibility between peers.

        Reports BGP sessions that are mis-configured or incompatible, including
        issues with address families, authentication, and other parameters.

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param nodes: Node specifier for local BGP speakers (optional).
        :param remote_nodes: Node specifier for remote BGP speakers (optional).
        :param status: BGP compatibility status specifier to filter by (optional).
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON array of BGP compatibility rows.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host)
        bf.set_network(network)
        bf.set_snapshot(snapshot)

        kwargs: dict[str, Any] = {}
        if nodes:
            kwargs["nodes"] = nodes
        if remote_nodes:
            kwargs["remoteNodes"] = remote_nodes
        if status:
            kwargs["status"] = status

        result = bf.q.bgpSessionCompatibility(**kwargs).answer().frame()
        return _df_to_json(result)

    # -------------------------------------------------------------------------
    # Node and interface information tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def bf_get_node_properties(
        network: str,
        snapshot: str,
        nodes: str = "",
        properties: str = "",
        host: str = "",
    ) -> str:
        """Retrieve configuration properties of network nodes (routers/switches).

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param nodes: Node specifier to restrict results (optional).
        :param properties: Comma-separated list of property names to retrieve (optional).
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON array of node property rows.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host)
        bf.set_network(network)
        bf.set_snapshot(snapshot)

        kwargs: dict[str, Any] = {}
        if nodes:
            kwargs["nodes"] = nodes
        if properties:
            kwargs["properties"] = properties

        result = bf.q.nodeProperties(**kwargs).answer().frame()
        return _df_to_json(result)

    @mcp.tool()
    def bf_get_interface_properties(
        network: str,
        snapshot: str,
        nodes: str = "",
        interfaces: str = "",
        properties: str = "",
        host: str = "",
    ) -> str:
        """Retrieve configuration properties of network interfaces.

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param nodes: Node specifier to restrict results (optional).
        :param interfaces: Interface specifier to restrict results (optional).
        :param properties: Comma-separated list of property names to retrieve (optional).
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON array of interface property rows.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host)
        bf.set_network(network)
        bf.set_snapshot(snapshot)

        kwargs: dict[str, Any] = {}
        if nodes:
            kwargs["nodes"] = nodes
        if interfaces:
            kwargs["interfaces"] = interfaces
        if properties:
            kwargs["properties"] = properties

        result = bf.q.interfaceProperties(**kwargs).answer().frame()
        return _df_to_json(result)

    @mcp.tool()
    def bf_get_ip_owners(
        network: str,
        snapshot: str,
        duplicates_only: bool = False,
        host: str = "",
    ) -> str:
        """Get the mapping of IP addresses to network interfaces.

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param duplicates_only: If True, return only IPs assigned to multiple interfaces.
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON array of IP ownership rows.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host)
        bf.set_network(network)
        bf.set_snapshot(snapshot)

        result = bf.q.ipOwners(duplicatesOnly=duplicates_only).answer().frame()
        return _df_to_json(result)

    # -------------------------------------------------------------------------
    # Snapshot comparison tools
    # -------------------------------------------------------------------------

    @mcp.tool()
    def bf_compare_filters(
        network: str,
        snapshot: str,
        reference_snapshot: str,
        filters: str = "",
        nodes: str = "",
        host: str = "",
    ) -> str:
        """Compare ACL/firewall filter behaviour between two snapshots.

        Identifies flows that are treated differently (permitted vs. denied)
        between the candidate snapshot and the reference (baseline) snapshot.

        :param network: Name of the network.
        :param snapshot: Name of the candidate (new) snapshot.
        :param reference_snapshot: Name of the reference (baseline) snapshot.
        :param filters: Filter specifier to restrict comparison (optional).
        :param nodes: Node specifier to restrict comparison (optional).
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON array of filter difference rows.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host)
        bf.set_network(network)
        bf.set_snapshot(snapshot)

        kwargs: dict[str, Any] = {}
        if filters:
            kwargs["filters"] = filters
        if nodes:
            kwargs["nodes"] = nodes

        result = bf.q.compareFilters(**kwargs).answer(snapshot=snapshot, reference_snapshot=reference_snapshot).frame()
        return _df_to_json(result)

    @mcp.tool()
    def bf_get_undefined_references(
        network: str,
        snapshot: str,
        nodes: str = "",
        host: str = "",
    ) -> str:
        """Find undefined references in device configurations.

        Reports references to named objects (e.g. ACLs, route-maps, prefix-lists)
        that are used but never defined, which can indicate configuration errors.

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param nodes: Node specifier to restrict results (optional).
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON array of undefined reference rows.
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host)
        bf.set_network(network)
        bf.set_snapshot(snapshot)

        kwargs: dict[str, Any] = {}
        if nodes:
            kwargs["nodes"] = nodes

        result = bf.q.undefinedReferences(**kwargs).answer().frame()
        return _df_to_json(result)

    @mcp.tool()
    def bf_detect_loops(
        network: str,
        snapshot: str,
        host: str = "",
    ) -> str:
        """Detect forwarding loops in the network snapshot.

        Identifies any packet flows that would loop indefinitely through the
        network without being delivered.

        :param network: Name of the network.
        :param snapshot: Name of the snapshot.
        :param host: Batfish server hostname. Defaults to BATFISH_HOST env var or 'localhost'.
        :return: JSON array of forwarding loop rows (empty if no loops found).
        """
        host = host or os.environ.get("BATFISH_HOST", "localhost")
        bf = _get_session(host)
        bf.set_network(network)
        bf.set_snapshot(snapshot)

        result = bf.q.detectLoops().answer().frame()
        return _df_to_json(result)

    return mcp


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _parse_interfaces(interfaces_str: str) -> list[Interface]:
    """Parse a comma-separated 'node[iface]' string into Interface objects."""
    result = []
    for item in interfaces_str.split(","):
        item = item.strip()
        if not item:
            continue
        if "[" in item and item.endswith("]"):
            node, iface = item[:-1].split("[", 1)
            result.append(Interface(hostname=node.strip(), interface=iface.strip()))
        else:
            # Treat the whole token as a node name with no specific interface
            result.append(Interface(hostname=item, interface=""))
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
