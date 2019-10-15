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
import os
from collections.abc import Mapping
from copy import deepcopy
from typing import Any, Dict, Optional, TYPE_CHECKING, Text, Tuple  # noqa: F401

import yaml

from pybatfish.datamodel import ListWrapper

if TYPE_CHECKING:
    from pybatfish.datamodel.answer import TableAnswer  # noqa: F401
    from pybatfish.client.session import Session  # noqa: F401

BATFISH_FACT_VERSION = "batfish_v0"

# Map of property name to new parent key
NODE_PROPERTIES_REORG = dict(
    [
        ("DNS_Servers", "DNS"),
        ("DNS_Source_Interface", "DNS"),
        ("IKE_Phase1_Keys", "IPsec"),
        ("IKE_Phase1_Policies", "IPsec"),
        ("IKE_Phase1_Proposals", "IPsec"),
        ("IPsec_Peer_Configs", "IPsec"),
        ("IPsec_Phase2_Policies", "IPsec"),
        ("IPsec_Phase2_Proposals", "IPsec"),
        ("NTP_Servers", "NTP"),
        ("NTP_Source_Interface", "NTP"),
        ("Logging_Servers", "Syslog"),
        ("Logging_Source_Interface", "Syslog"),
        ("SNMP_Source_Interface", "SNMP"),
        ("SNMP_Trap_Servers", "SNMP"),
        ("TACACS_Servers", "TACACS"),
        ("TACACS_Source_Interface", "TACACS"),
    ]
)  # type: Dict[Text, Text]


def get_facts(session, nodes_specifier="/.*/", snapshot=None):
    # type: (Session, Text, Optional[Text]) -> Dict[Text, Any]
    """
    Get snapshot facts from the specified session for nodes matching the nodes specifier.

    If a snapshot is specified, facts are collected for that snapshot, otherwise facts are collected for the current snapshot.
    """
    args = {}
    if nodes_specifier:
        args["nodes"] = nodes_specifier

    ans_args = {}
    if snapshot is not None:
        ans_args["snapshot"] = snapshot

    node_properties = session.q.nodeProperties(  # type: ignore
        **args
    ).answer(
        **ans_args
    )
    interface_properties = session.q.interfaceProperties(  # type: ignore
        **args
    ).answer(
        **ans_args
    )
    bgp_process_properties = session.q.bgpProcessConfiguration(  # type: ignore
        **args
    ).answer(**ans_args)
    bgp_peer_properties = session.q.bgpPeerConfiguration(  # type: ignore
        **args
    ).answer(
        **ans_args
    )
    ospf_proc = session.q.ospfProcessConfiguration(  # type: ignore
        **args
    ).answer(
        **ans_args
    )
    ospf_area = session.q.ospfAreaConfiguration(  # type: ignore
        **args
    ).answer(
        **ans_args
    )
    ospf_iface = session.q.ospfInterfaceConfiguration(  # type: ignore
        **args
    ).answer(
        **ans_args
    )

    return _encapsulate_nodes_facts(
        _process_facts(
            node_properties,
            interface_properties,
            bgp_process_properties,
            bgp_peer_properties,
            ospf_proc,
            ospf_area,
            ospf_iface,
        ),
        BATFISH_FACT_VERSION,
    )


def load_facts(input_directory):
    # type: (Text) -> Dict[Text, Any]
    """Load facts from text files in the specified directory."""
    out = {"version": None, "nodes": {}}  # type: Dict[Text, Any]
    out_nodes = out["nodes"]

    files = os.listdir(input_directory)
    if not len(files):
        raise ValueError("No files present in specified directory")

    for filename in files:
        with open(os.path.join(input_directory, filename), "r") as f:
            dict_ = yaml.safe_load(f.read())
            nodes, version = _unencapsulate_facts(dict_)

            # Assume latest version if none is specified
            if not version:
                version_text = BATFISH_FACT_VERSION
            else:
                version_text = version

            # Make sure version is consistent
            if out["version"] and version_text != out["version"]:
                raise ValueError("Input file version mismatch!")
            out["version"] = version_text

            # We allow a single input file to specify more than one node
            for node in nodes:
                out_nodes[node] = nodes[node]
    return out


def validate_facts(expected, actual, verbose=False):
    # type: (Dict[Text, Any], Dict[Text, Any], bool) -> Dict[Text, Any]
    """Return a map of node to non-matching facts based on the difference between the expected and actual facts supplied.

    If the `verbose` flag is set, matching facts are returned in addition-to non-matching facts.
    """
    failures = {}
    expected_facts = expected["nodes"]
    actual_facts = actual["nodes"]
    expected_version = expected["version"]
    actual_version = actual["version"]
    if expected_version != actual_version:
        return {
            n: {"Version": {"expected": expected_version, "actual": actual_version}}
            for n in expected_facts
        }
    for node in expected_facts:
        res = _assert_dict_subset(
            actual_facts.get(node, {}), expected_facts[node], verbose=verbose
        )
        if res:
            failures[node] = res
    return failures


def _process_facts(
    node_props,
    iface_props,
    bgp_process_props,
    bgp_peer_props,
    ospf_proc,
    ospf_area,
    ospf_iface,
):
    # type: (TableAnswer, TableAnswer, TableAnswer, TableAnswer, TableAnswer, TableAnswer, TableAnswer) -> Dict[Text, Any]
    """Process properties answers into a fact dict."""
    # out = {}
    out = _process_nodes(node_props)
    _process_interfaces(out, iface_props)
    _process_bgp_processes(out, bgp_process_props)
    _process_bgp_peers(out, bgp_peer_props)
    _process_ospf_processes(out, ospf_proc)
    _process_ospf_areas(out, ospf_area)
    _process_ospf_interfaces(out, ospf_iface)

    return _convert_listwrapper(out)


def _convert_listwrapper(dict_):
    # type: (Mapping[Text, Any]) -> Dict[Text, Any]
    """Convert ListWrapper objects in the specified dict into plain lists."""
    out = {}  # type: Dict[Text, Any]
    for k in dict_:
        val = dict_[k]
        if isinstance(val, Mapping):
            out[k] = _convert_listwrapper(val)
        elif isinstance(val, ListWrapper):
            out[k] = list(val)
        else:
            out[k] = val
    return out


def _process_bgp_processes(node_dict, bgp_proc_props):
    # type: (Dict[Text, Any], TableAnswer) -> None
    """Return fact dict with processed bgp process properties answer added to it."""
    bgp_proc_dict = bgp_proc_props.frame().to_dict(orient="records")
    for r in bgp_proc_dict:
        node = r.pop("Node")
        # These will be replaced by bgp peers when we process them
        r["Neighbors"] = {}
        node_dict[node]["BGP"] = r


def _process_bgp_peers(node_dict, bgp_peer_props):
    # type: (Dict[Text, Any], TableAnswer) -> None
    """Return fact dict with processed bgp peer properties answer added to it."""
    bgp_peer_dict = bgp_peer_props.frame().to_dict(orient="records")
    for r in bgp_peer_dict:
        node = r.pop("Node")
        ip = r.get("Remote_IP")
        node_dict[node]["BGP"]["Neighbors"][str(ip)] = r


def _process_ospf_processes(node_dict, ospf_props):
    # type: (Dict[Text, Any], TableAnswer) -> None
    """Update fact dict with processed ospf process properties answer added to it."""
    ospf_dict = ospf_props.frame().to_dict(orient="records")
    for r in ospf_dict:
        node = r.pop("Node")
        proc = r.pop("Process_ID")

        _get_or_create_ospf_processes(node_dict, node)[proc] = {
            "VRF": r.get("VRF"),
            "Reference_Bandwidth": r.get("Reference_Bandwidth"),
            "Router_ID": r.get("Router_ID"),
        }


def _process_ospf_areas(node_dict, ospf_props):
    # type: (Dict[Text, Any], TableAnswer) -> None
    """Update fact dict with processed ospf area properties answer added to it."""
    ospf_dict = ospf_props.frame().to_dict(orient="records")
    for r in ospf_dict:
        node = r.pop("Node")
        proc = r.pop("Process_ID")
        area = r.pop("Area")

        _get_or_create_ospf_areas(node_dict, node, proc)[area] = {
            "Area_Type": r.get("Area_Type")
        }


def _process_ospf_interfaces(node_dict, ospf_props):
    # type: (Dict[Text, Any], TableAnswer) -> None
    """Update fact dict with processed ospf interface properties answer added to it."""
    ospf_dict = ospf_props.frame().to_dict(orient="records")
    for r in ospf_dict:
        iface = r.pop("Interface")
        node = iface.hostname
        proc = r.pop("Process_ID")
        area = str(r.pop("OSPF_Area_Name"))

        _get_or_create_ospf_interfaces(node_dict, node, proc, area)[iface.interface] = {
            "Enabled": r.get("OSPF_Enabled"),
            "Passive": r.get("OSPF_Passive"),
            "Cost": r.get("OSPF_Cost"),
            "Dead_Interval": r.get("OSPF_Dead_Interval"),
            "Hello_Interval": r.get("OSPF_Hello_Interval"),
            "Network_Type": r.get("OSPF_Network_Type"),
        }


def _get_or_create_ospf_interfaces(node_dict, node, process, area):
    # type: (Dict[Text, Any], Text, Text, Text) -> Any
    """
    Get the OSPF interfaces dict under the specified OSPF area and process on the specified node.

    If it or any of its parents does not already exist, create them.
    """
    areas = _get_or_create_ospf_areas(node_dict, node, process)
    return areas.setdefault(area, {}).setdefault("Interfaces", {})


def _get_or_create_ospf_areas(node_dict, node, process):
    # type: (Dict[Text, Any], Text, Text) -> Any
    """
    Get the OSPF areas dict under the specified OSPF process on the specified node.

    If it or any of its parents does not already exist, create them.
    """
    procs = _get_or_create_ospf_processes(node_dict, node)
    return procs.setdefault(process, {}).setdefault("Areas", {})


def _get_or_create_ospf_processes(node_dict, node):
    # type: (Dict[Text, Any], Text) -> Any
    """
    Get the OSPF processes dict under the specified node.

    If it or any of its parents does not already exist, create them.
    """
    return (
        node_dict.setdefault(node, {})
        .setdefault("OSPF", {})
        .setdefault("Processes", {})
    )


def _process_interfaces(node_dict, iface_props):
    # type: (Dict[Text, Any], TableAnswer) -> None
    """Return fact dict with processed interface properties answer added to it."""
    iface_dict = iface_props.frame().to_dict(orient="records")
    for i in iface_dict:
        node = i["Interface"].hostname
        if node in node_dict:
            _add_interface(node_dict[node], i)
        else:
            # Should be impossible for ifaceProps to have node not in nodeProps
            raise ValueError("Interface belongs to non-existent node {}".format(node))


def _process_nodes(node_props):
    # type: (TableAnswer) -> Dict[Text, Any]
    """Return fact dict corresponding to processed node properties answer."""
    out = {}
    node_dict = node_props.frame().to_dict(orient="records")
    for record in node_dict:
        node = record.pop("Node")
        record.pop("Interfaces")

        # Remove Batfish-constructed structures e.g.:
        # routing policies like ~BGP_COMMON_EXPORT_POLICY:default~
        _remove_constructed_names(record)

        # Add properties as children of node
        out[node] = record
        _reorg_dict(out[node], NODE_PROPERTIES_REORG)
    return out


def _remove_constructed_names(dict_):
    # type: (Dict[Text, Any]) -> None
    """Remove names constructed by Batfish.

    Removes strings beginning with ~ from lists in the specified dict.
    """
    for k in dict_:
        if isinstance(dict_[k], list):
            dict_[k] = [i for i in dict_[k] if not i.startswith("~")]


def _add_interface(node_dict, iface_dict_in):
    # type: (Dict[Text, Any], Dict[Text, Any]) -> None
    """Update and add interface dict to the specified node dict."""
    if "Interfaces" not in node_dict:
        node_dict["Interfaces"] = {}
    iface_dict = deepcopy(iface_dict_in)

    iface_name = iface_dict_in["Interface"].interface
    iface_dict.pop("Interface")

    node_dict["Interfaces"][iface_name] = iface_dict


def _reorg_dict(dict, reorg_map):
    # type: (Dict[Text, Any], Dict[Text, Text]) -> None
    """Reorganize top-level keys in the input dict based on the supplied reorg map."""
    for key in reorg_map:
        new_parent = reorg_map[key]
        if new_parent not in dict:
            dict[new_parent] = {}
        dict[new_parent][key] = dict.pop(key)


def _write_yaml_file(dict_, filepath):
    # type: (Dict[Text, Any], Text) -> None
    with open(filepath, "w") as f:
        # default_flow_style=False dumps lists as hyphen lists instead of
        # square bracket lists
        yaml.safe_dump(dict_, stream=f, default_flow_style=False)


def write_facts(output_directory, facts):
    # type: (Text, Dict[Text, Any]) -> None
    """Write facts to YAML files in the supplied output directory."""
    nodes, version = _unencapsulate_facts(facts)

    if version:
        version_text = version
    else:
        raise ValueError("Version must be specified to write facts.")

    # Write facts for each node in its own file
    for node in nodes:
        filepath = os.path.join(output_directory, "{}.yml".format(node))
        node_facts = _encapsulate_nodes_facts(
            {node: facts["nodes"][node]}, version_text
        )
        _write_yaml_file(node_facts, filepath)


def _encapsulate_nodes_facts(nodes_facts, version):
    # type: (Dict[Text, Any], Text) -> Dict[Text, Any]
    """Format node(s) facts in final fact format (the way they are written to file)."""
    return {"nodes": nodes_facts, "version": version}


def _unencapsulate_facts(facts):
    # type: (Dict[Text, Any]) -> Tuple[Any, Optional[Any]]
    """Extract node facts and version from final fact format."""
    assert "nodes" in facts, "No nodes present in parsed facts file(s)"
    return facts["nodes"], facts.get("version")


def _assert_dict_subset(actual, expected, prefix="", diffs=None, verbose=False):
    # type: (Dict[Text, Any], Dict[Text, Any], Text, Optional[Dict], bool) -> Dict[Text, Any]
    """Assert that the expected dictionary is a subset of the actual dictionary.

    :param actual: the dictionary tested
    :param expected: the expected value of a dictionary
    :returns: if verbose=`False` returns dictionary of property name to non-matching expected and actual values, if verbose=`True` returns a dictionary of property name to expected and actual values for all checked values
    """
    if diffs is None:
        diffs_out = {}  # type: Dict[Text, Any]
    else:
        diffs_out = diffs
    for k in expected:
        key_name = "{}{}".format(prefix, k)
        if k not in actual:
            diffs_out[key_name] = {"key_present": False, "expected": expected[k]}
        else:
            if isinstance(expected[k], Mapping):
                _assert_dict_subset(
                    actual[k], expected[k], key_name + ".", diffs_out, verbose=verbose
                )
            else:
                if expected[k] != actual[k] or verbose:
                    diffs_out[key_name] = {"expected": expected[k], "actual": actual[k]}
    return diffs_out
