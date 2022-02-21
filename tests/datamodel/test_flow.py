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

from operator import attrgetter

import attr
import pytest

from pybatfish.datamodel import NextHopDiscard, NextHopIp
from pybatfish.datamodel.flow import (
    Accept,
    ArpErrorStepDetail,
    DelegatedToNextVrf,
    DeliveredStepDetail,
    Discarded,
    EnterInputIfaceStepDetail,
    ExitOutputIfaceStepDetail,
    FilterStepDetail,
    Flow,
    FlowDiff,
    FlowTraceHop,
    ForwardedIntoVxlanTunnel,
    ForwardedOutInterface,
    ForwardingDetail,
    ForwardOutInterface,
    HeaderConstraints,
    Hop,
    InboundStepDetail,
    IncomingSessionScope,
    LoopStepDetail,
    MatchSessionStepDetail,
    MatchTcpFlags,
    OriginatingSessionScope,
    PostNatFibLookup,
    PreNatFibLookup,
    RouteInfo,
    RoutingStepDetail,
    SessionAction,
    SessionMatchExpr,
    SessionScope,
    SetupSessionStepDetail,
    Step,
    TcpFlags,
    TransformationStepDetail,
)


def test_arp_error_step_detail_str():
    detail = ArpErrorStepDetail("iface", "1.1.1.1")

    step = Step(detail, "ACTION")
    assert str(step) == "ACTION(Output Interface: iface, Resolved Next Hop IP: 1.1.1.1)"


def test_arp_error_step_detail_deserialization():
    json = {"outputInterface": {"interface": "iface"}, "resolvedNexthopIp": "1.1.1.1"}
    detail = ArpErrorStepDetail.from_dict(json)
    assert detail == ArpErrorStepDetail("iface", "1.1.1.1")


def test_delivered_step_detail_str():
    detail = DeliveredStepDetail("iface", "1.1.1.1")

    step = Step(detail, "ACTION")
    assert str(step) == "ACTION(Output Interface: iface, Resolved Next Hop IP: 1.1.1.1)"


def test_delivered_step_detail_deserialization():
    json = {"outputInterface": {"interface": "iface"}, "resolvedNexthopIp": "1.1.1.1"}
    detail = DeliveredStepDetail.from_dict(json)
    assert detail == DeliveredStepDetail("iface", "1.1.1.1")


def test_exit_output_iface_step_detail_str():
    detail = ExitOutputIfaceStepDetail("iface", None)

    step = Step(detail, "ACTION")
    assert str(step) == "ACTION(iface)"


def test_transformation_step_detail_str():
    no_diffs = TransformationStepDetail("type", [])
    one_diff = TransformationStepDetail("type", [FlowDiff("field", "old", "new")])
    two_diffs = TransformationStepDetail(
        "type", [FlowDiff("field1", "old1", "new1"), FlowDiff("field2", "old2", "new2")]
    )

    step = Step(no_diffs, "ACTION")
    assert str(step) == "ACTION(type)"

    step = Step(one_diff, "ACTION")
    assert str(step) == "ACTION(type field: old -> new)"

    step = Step(two_diffs, "ACTION")
    assert str(step) == "ACTION(type field1: old1 -> new1, field2: old2 -> new2)"


def test_filter_step_detail():
    json_dict = {
        "filter": "ACL",
        "type": "ingressAcl",
        "inputInterface": "iface",
        "flow": {
            "dscp": 0,
            "dstIp": "2.1.1.1",
            "dstPort": 0,
            "ecn": 0,
            "fragmentOffset": 0,
            "icmpCode": 255,
            "icmpVar": 255,
            "ingressInterface": "intface",
            "ingressNode": "ingress",
            "ingressVrf": "vrfAbc",
            "ipProtocol": "IP",
            "packetLength": 0,
            "srcIp": "5.5.1.1",
            "srcPort": 0,
            "tcpFlagsAck": 0,
            "tcpFlagsCwr": 0,
            "tcpFlagsEce": 0,
            "tcpFlagsFin": 0,
            "tcpFlagsPsh": 0,
            "tcpFlagsRst": 0,
            "tcpFlagsSyn": 0,
            "tcpFlagsUrg": 0,
        },
    }

    detail = FilterStepDetail.from_dict(json_dict)

    assert detail.filter == "ACL"
    assert detail.filterType == "ingressAcl"
    assert detail.inputInterface == "iface"

    flow = detail.flow

    assert flow.srcIp == "5.5.1.1"
    assert flow.ingressInterface == "intface"
    assert flow.ingressVrf == "vrfAbc"


def test_flow_deserialization():
    hop_dict = {
        "dscp": 0,
        "dstIp": "2.1.1.1",
        "dstPort": 0,
        "ecn": 0,
        "fragmentOffset": 0,
        "icmpCode": 255,
        "icmpVar": 255,
        "ingressInterface": "intface",
        "ingressNode": "ingress",
        "ingressVrf": "vrfAbc",
        "ipProtocol": "TCP",
        "packetLength": 0,
        "srcIp": "5.5.1.1",
        "srcPort": 0,
        "tcpFlagsAck": 0,
        "tcpFlagsCwr": 0,
        "tcpFlagsEce": 0,
        "tcpFlagsFin": 0,
        "tcpFlagsPsh": 0,
        "tcpFlagsRst": 0,
        "tcpFlagsSyn": 0,
        "tcpFlagsUrg": 0,
    }

    # check deserialization
    flow = Flow.from_dict(hop_dict)
    assert flow.srcIp == "5.5.1.1"
    assert flow.ingressInterface == "intface"
    assert flow.ingressVrf == "vrfAbc"

    # check the string representation has the essential elements (without forcing a strict format)
    flow_str = str(flow)
    assert "5.5.1.1" in flow_str
    assert "intface" in flow_str
    assert "vrfAbc" in flow_str


# test if a flow is deserialized properly when the optional fields are missing
def test_flow_deserialization_optional_missing():
    hop_dict = {
        "dscp": 0,
        "dstIp": "2.1.1.1",
        "dstPort": 0,
        "ecn": 0,
        "fragmentOffset": 0,
        "icmpCode": 255,
        "icmpVar": 255,
        "ingressNode": "ingress",
        "ipProtocol": "TCP",
        "packetLength": 0,
        "srcIp": "5.5.1.1",
        "srcPort": 0,
        "tcpFlagsAck": 0,
        "tcpFlagsCwr": 0,
        "tcpFlagsEce": 0,
        "tcpFlagsFin": 0,
        "tcpFlagsPsh": 0,
        "tcpFlagsRst": 0,
        "tcpFlagsSyn": 0,
        "tcpFlagsUrg": 0,
    }
    # check deserialization
    flow = Flow.from_dict(hop_dict)
    assert flow.srcIp == "5.5.1.1"

    # should convert to string without problems
    str(flow)


def test_flow_trace_hop_no_transformed_flow():
    """Test we don't crash on missing or None values."""
    FlowTraceHop.from_dict(
        {
            "edge": {
                "node1": "dummy",
                "node1interface": "eth0",
                "node2": "router1",
                "node2interface": "Ethernet1",
            },
            "filterIn": None,
            "filterOut": None,
            "routes": [
                "StaticRoute<0.0.0.0/0,nhip:10.192.48.1,nhint:eth0>_fnhip:10.192.48.1"
            ],
            "transformedFlow": None,
        }
    )

    FlowTraceHop.from_dict(
        {
            "edge": {
                "node1": "dummy",
                "node1interface": "eth0",
                "node2": "router1",
                "node2interface": "Ethernet1",
            },
            "filterIn": None,
            "filterOut": None,
            "routes": [
                "StaticRoute<0.0.0.0/0,nhip:10.192.48.1,nhint:eth0>_fnhip:10.192.48.1"
            ],
        }
    )


def test_get_ip_protocol_str_nodetail():
    flow_dict = {
        "dscp": 0,
        "dstIp": "2.1.1.1",
        "dstPort": 0,
        "ecn": 0,
        "fragmentOffset": 0,
        "icmpCode": 255,
        "icmpVar": 255,
        "ingressNode": "ingress",
        "ipProtocol": "UNNAMED_243",
        "packetLength": 0,
        "srcIp": "5.5.1.1",
        "srcPort": 0,
        "tcpFlagsAck": 0,
        "tcpFlagsCwr": 0,
        "tcpFlagsEce": 0,
        "tcpFlagsFin": 0,
        "tcpFlagsPsh": 0,
        "tcpFlagsRst": 0,
        "tcpFlagsSyn": 0,
        "tcpFlagsUrg": 0,
    }
    assert Flow.from_dict(flow_dict).get_ip_protocol_str() == "ipProtocol=243"

    # named
    flow_dict["ipProtocol"] = "UDP"
    assert Flow.from_dict(flow_dict).get_ip_protocol_str() == "UDP"


def test_get_ip_protocol_str_tcp():
    flow_dict = {
        "dscp": 0,
        "dstIp": "2.1.1.1",
        "dstPort": 80,
        "ecn": 0,
        "fragmentOffset": 0,
        "icmpCode": 255,
        "icmpVar": 255,
        "ingressNode": "ingress",
        "ipProtocol": "TCP",
        "packetLength": 0,
        "srcIp": "5.5.1.1",
        "srcPort": 80,
        "tcpFlagsAck": 0,
        "tcpFlagsCwr": 0,
        "tcpFlagsEce": 0,
        "tcpFlagsFin": 0,
        "tcpFlagsPsh": 0,
        "tcpFlagsRst": 0,
        "tcpFlagsSyn": 0,
        "tcpFlagsUrg": 0,
    }
    assert Flow.from_dict(flow_dict).get_ip_protocol_str() == "TCP (no flags set)"

    # with flags
    flow_dict["tcpFlagsAck"] = 1
    assert Flow.from_dict(flow_dict).get_ip_protocol_str() == "TCP (ACK)"


def test_get_ip_protocol_str_icmp():
    flow_dict = {
        "dscp": 0,
        "dstIp": "2.1.1.1",
        "dstPort": 0,
        "ecn": 0,
        "fragmentOffset": 0,
        "icmpCode": 0,
        "icmpVar": 8,
        "ingressNode": "ingress",
        "ipProtocol": "ICMP",
        "packetLength": 0,
        "srcIp": "5.5.1.1",
        "srcPort": 0,
        "tcpFlagsAck": 0,
        "tcpFlagsCwr": 0,
        "tcpFlagsEce": 0,
        "tcpFlagsFin": 0,
        "tcpFlagsPsh": 0,
        "tcpFlagsRst": 0,
        "tcpFlagsSyn": 0,
        "tcpFlagsUrg": 0,
    }
    assert Flow.from_dict(flow_dict).get_ip_protocol_str() == "ICMP (type=8, code=0)"


def test_get_flag_str():
    flow_dict = {
        "dscp": 0,
        "dstIp": "2.1.1.1",
        "dstPort": 0,
        "ecn": 0,
        "fragmentOffset": 0,
        "icmpCode": 0,
        "icmpVar": 8,
        "ingressNode": "ingress",
        "ipProtocol": "ICMP",
        "packetLength": 0,
        "srcIp": "5.5.1.1",
        "srcPort": 0,
        "tcpFlagsAck": 0,
        "tcpFlagsCwr": 0,
        "tcpFlagsEce": 0,
        "tcpFlagsFin": 0,
        "tcpFlagsPsh": 0,
        "tcpFlagsRst": 0,
        "tcpFlagsSyn": 0,
        "tcpFlagsUrg": 0,
    }
    assert Flow.from_dict(flow_dict).get_flag_str() == "no flags set"

    flow_dict["tcpFlagsAck"] = 1
    assert Flow.from_dict(flow_dict).get_flag_str() == "ACK"

    flow_dict["tcpFlagsSyn"] = 1
    assert Flow.from_dict(flow_dict).get_flag_str() == "SYN-ACK"

    flow_dict["tcpFlagsCwr"] = 1
    assert Flow.from_dict(flow_dict).get_flag_str() == "SYN-ACK-CWR"

    flow_dict["tcpFlagsEce"] = 1
    assert Flow.from_dict(flow_dict).get_flag_str() == "SYN-ACK-CWR-ECE"

    flow_dict["tcpFlagsFin"] = 1
    assert Flow.from_dict(flow_dict).get_flag_str() == "SYN-FIN-ACK-CWR-ECE"

    flow_dict["tcpFlagsPsh"] = 1
    assert Flow.from_dict(flow_dict).get_flag_str() == "SYN-FIN-ACK-CWR-ECE-PSH"

    flow_dict["tcpFlagsRst"] = 1
    assert Flow.from_dict(flow_dict).get_flag_str() == "SYN-FIN-ACK-RST-CWR-ECE-PSH"

    flow_dict["tcpFlagsUrg"] = 1
    assert Flow.from_dict(flow_dict).get_flag_str() == "SYN-FIN-ACK-RST-CWR-ECE-PSH-URG"


def test_str():
    flow_dict = {
        "dscp": 0,
        "dstIp": "2.1.1.1",
        "dstPort": 0,
        "ecn": 0,
        "fragmentOffset": 0,
        "icmpCode": 0,
        "icmpVar": 0,
        "ingressNode": "ingress",
        "ipProtocol": "UNNAMED_168",
        "packetLength": 512,
        "srcIp": "5.5.1.1",
        "srcPort": 0,
        "tcpFlagsAck": 0,
        "tcpFlagsCwr": 0,
        "tcpFlagsEce": 0,
        "tcpFlagsFin": 0,
        "tcpFlagsPsh": 0,
        "tcpFlagsRst": 0,
        "tcpFlagsSyn": 0,
        "tcpFlagsUrg": 0,
    }
    # no ports
    assert (
        str(Flow.from_dict(flow_dict))
        == "start=ingress [5.5.1.1->2.1.1.1 ipProtocol=168]"
    )

    # with ports
    flow_dict["ipProtocol"] = "TCP"
    flow_dict["dstPort"] = "80"
    flow_dict["srcPort"] = "800"
    assert (
        str(Flow.from_dict(flow_dict))
        == "start=ingress [5.5.1.1:800->2.1.1.1:80 TCP (no flags set)]"
    )

    # uncommon dscp
    flow_dict["dscp"] = "1"
    assert (
        str(Flow.from_dict(flow_dict))
        == "start=ingress [5.5.1.1:800->2.1.1.1:80 TCP (no flags set) dscp=1]"
    )

    # uncommon ecn
    flow_dict["ecn"] = "1"
    assert (
        str(Flow.from_dict(flow_dict))
        == "start=ingress [5.5.1.1:800->2.1.1.1:80 TCP (no flags set) dscp=1 ecn=1]"
    )

    # uncommon fragment offset
    flow_dict["fragmentOffset"] = "1501"
    assert (
        str(Flow.from_dict(flow_dict))
        == "start=ingress [5.5.1.1:800->2.1.1.1:80 TCP (no flags set) dscp=1 ecn=1 fragmentOffset=1501]"
    )

    # uncommon packet length
    flow_dict["packetLength"] = "100"
    assert (
        str(Flow.from_dict(flow_dict))
        == "start=ingress [5.5.1.1:800->2.1.1.1:80 TCP (no flags set) dscp=1 ecn=1 fragmentOffset=1501 length=100]"
    )


def test_repr_html_lines():
    flow_dict = {
        "dscp": 0,
        "dstIp": "2.1.1.1",
        "dstPort": 0,
        "ecn": 0,
        "fragmentOffset": 0,
        "icmpCode": 0,
        "icmpVar": 0,
        "ingressNode": "ingress",
        "ipProtocol": "UNNAMED_168",
        "packetLength": 512,
        "srcIp": "5.5.1.1",
        "srcPort": 0,
        "tcpFlagsAck": 0,
        "tcpFlagsCwr": 0,
        "tcpFlagsEce": 0,
        "tcpFlagsFin": 0,
        "tcpFlagsPsh": 0,
        "tcpFlagsRst": 0,
        "tcpFlagsSyn": 0,
        "tcpFlagsUrg": 0,
    }
    # no ports
    assert Flow.from_dict(flow_dict)._repr_html_lines() == [
        "Start Location: ingress",
        "Src IP: 5.5.1.1",
        "Dst IP: 2.1.1.1",
        "IP Protocol: ipProtocol=168",
    ]

    # with ports
    flow_dict["ipProtocol"] = "TCP"
    flow_dict["dstPort"] = "80"
    flow_dict["srcPort"] = "800"
    assert Flow.from_dict(flow_dict)._repr_html_lines() == [
        "Start Location: ingress",
        "Src IP: 5.5.1.1",
        "Src Port: 800",
        "Dst IP: 2.1.1.1",
        "Dst Port: 80",
        "IP Protocol: TCP (no flags set)",
    ]

    # uncommon dscp
    flow_dict["dscp"] = "1"
    assert Flow.from_dict(flow_dict)._repr_html_lines() == [
        "Start Location: ingress",
        "Src IP: 5.5.1.1",
        "Src Port: 800",
        "Dst IP: 2.1.1.1",
        "Dst Port: 80",
        "IP Protocol: TCP (no flags set)",
        "DSCP: 1",
    ]

    # uncommon ecn
    flow_dict["ecn"] = "1"
    assert Flow.from_dict(flow_dict)._repr_html_lines() == [
        "Start Location: ingress",
        "Src IP: 5.5.1.1",
        "Src Port: 800",
        "Dst IP: 2.1.1.1",
        "Dst Port: 80",
        "IP Protocol: TCP (no flags set)",
        "DSCP: 1",
        "ECN: 1",
    ]

    # uncommon fragment offset
    flow_dict["fragmentOffset"] = "1501"
    assert Flow.from_dict(flow_dict)._repr_html_lines() == [
        "Start Location: ingress",
        "Src IP: 5.5.1.1",
        "Src Port: 800",
        "Dst IP: 2.1.1.1",
        "Dst Port: 80",
        "IP Protocol: TCP (no flags set)",
        "DSCP: 1",
        "ECN: 1",
        "Fragment Offset: 1501",
    ]

    # uncommon packet length
    flow_dict["packetLength"] = "100"
    assert Flow.from_dict(flow_dict)._repr_html_lines() == [
        "Start Location: ingress",
        "Src IP: 5.5.1.1",
        "Src Port: 800",
        "Dst IP: 2.1.1.1",
        "Dst Port: 80",
        "IP Protocol: TCP (no flags set)",
        "DSCP: 1",
        "ECN: 1",
        "Fragment Offset: 1501",
        "Packet Length: 100",
    ]


def test_header_constraints_serialization():
    hc = HeaderConstraints()
    hcd = hc.dict()
    fields = set(map(attrgetter("name"), attr.fields(HeaderConstraints)))
    for field in fields:
        assert hcd[field] is None

    hc = HeaderConstraints(srcIps="1.1.1.1")
    assert hc.dict()["srcIps"] == "1.1.1.1"

    hc = HeaderConstraints(dstPorts=["10-20", "33-33"])
    assert hc.dict()["dstPorts"] == "10-20,33-33"

    hc = HeaderConstraints(dstPorts="10-20,33")
    assert hc.dict()["dstPorts"] == "10-20,33"

    for dp in [10, "10", [10], ["10"]]:
        hc = HeaderConstraints(dstPorts=dp)
        assert hc.dict()["dstPorts"] == "10"

    hc = HeaderConstraints(applications="dns,ssh")
    assert hc.dict()["applications"] == ["dns", "ssh"]

    hc = HeaderConstraints(applications=["dns", "ssh"])
    assert hc.dict()["applications"] == ["dns", "ssh"]

    hc = HeaderConstraints(ipProtocols="  ,  dns,")
    assert hc.dict()["ipProtocols"] == ["dns"]

    hc = HeaderConstraints(ipProtocols=["tcp", "udp"])
    assert hc.dict()["ipProtocols"] == ["tcp", "udp"]

    match_syn = MatchTcpFlags(tcpFlags=TcpFlags(syn=True), useSyn=True)
    hc1 = HeaderConstraints(tcpFlags=match_syn)
    hc2 = HeaderConstraints(tcpFlags=[match_syn])
    assert hc1.dict() == hc2.dict()

    with pytest.raises(ValueError):
        HeaderConstraints(applications="")


def test_hop_repr_str():
    hop = Hop(
        "node1",
        [
            Step(EnterInputIfaceStepDetail("in_iface1", "in_vrf1"), "SENT_IN"),
            Step(
                RoutingStepDetail(
                    [
                        RouteInfo(
                            "bgp", "1.1.1.1/24", NextHopIp("1.2.3.4"), None, 1, 1
                        ),
                        RouteInfo(
                            "static", "1.1.1.2/24", NextHopIp("1.2.3.5"), None, 1, 1
                        ),
                    ],
                    ForwardedOutInterface("iface1", "12.123.1.2"),
                    "12.123.1.2",
                    "iface1",
                ),
                "FORWARDED",
            ),
            Step(
                FilterStepDetail("preSourceNat_filter", "PRENAT", "", ""), "PERMITTED"
            ),
            Step(ExitOutputIfaceStepDetail("out_iface1", None), "SENT_OUT"),
        ],
    )

    assert (
        str(hop) == "node: node1\n  SENT_IN(in_iface1)\n"
        "  FORWARDED(Forwarded out interface: iface1 with resolved next-hop IP: 12.123.1.2, Routes: [bgp (Network: 1.1.1.1/24, Next Hop: ip 1.2.3.4),static (Network: 1.1.1.2/24, Next Hop: ip 1.2.3.5)])\n  "
        "PERMITTED(preSourceNat_filter (PRENAT))\n  SENT_OUT(out_iface1)"
    )


# TODO: remove after sufficient period
def test_hop_repr_str_legacy():
    hop = Hop(
        "node1",
        [
            Step(EnterInputIfaceStepDetail("in_iface1", "in_vrf1"), "SENT_IN"),
            Step(
                RoutingStepDetail(
                    [
                        RouteInfo("bgp", "1.1.1.1/24", None, "1.2.3.4", 1, 1),
                        RouteInfo("static", "1.1.1.2/24", None, "1.2.3.5", 1, 1),
                    ],
                    None,
                    "12.123.1.2",
                    "iface1",
                ),
                "FORWARDED",
            ),
            Step(
                FilterStepDetail("preSourceNat_filter", "PRENAT", "", ""), "PERMITTED"
            ),
            Step(ExitOutputIfaceStepDetail("out_iface1", None), "SENT_OUT"),
        ],
    )

    assert (
        str(hop) == "node: node1\n  SENT_IN(in_iface1)\n"
        "  FORWARDED(ARP IP: 12.123.1.2, Output Interface: iface1, Routes: [bgp (Network: 1.1.1.1/24, Next Hop IP:1.2.3.4),static (Network: 1.1.1.2/24, Next Hop IP:1.2.3.5)])\n  "
        "PERMITTED(preSourceNat_filter (PRENAT))\n  SENT_OUT(out_iface1)"
    )


# TOOD: remove after sufficient period
def test_only_routes_str_legacy():
    routingStepDetail = RoutingStepDetail(
        [RouteInfo("bgp", "1.1.1.1/24", None, "1.2.3.4", 1, 1)],
        None,
        None,
        None,
    )

    assert (
        str(routingStepDetail)
        == "Routes: [bgp (Network: 1.1.1.1/24, Next Hop IP:1.2.3.4)]"
    )


# TOOD: remove after sufficient period
def test_no_output_iface_str_legacy():
    routingStepDetail = RoutingStepDetail(
        [RouteInfo("bgp", "1.1.1.1/24", None, "1.2.3.4", 1, 1)],
        None,
        "1.2.3.4",
        None,
    )
    assert (
        str(routingStepDetail)
        == "ARP IP: 1.2.3.4, Routes: [bgp (Network: 1.1.1.1/24, Next Hop IP:1.2.3.4)]"
    )


# TOOD: remove after sufficient period
def test_no_arp_ip_str_legacy():
    routingStepDetail = RoutingStepDetail(
        [RouteInfo("bgp", "1.1.1.1/24", None, "1.2.3.4", 1, 1)],
        None,
        None,
        "iface1",
    )
    assert (
        str(routingStepDetail)
        == "Output Interface: iface1, Routes: [bgp (Network: 1.1.1.1/24, Next Hop IP:1.2.3.4)]"
    )


def test_no_route():
    step = Step(RoutingStepDetail([], Discarded(), None, None), "NO_ROUTE")
    assert str(step) == "NO_ROUTE(Discarded)"


# TODO: remove after sufficient period
def test_no_route_legacy():
    step = Step(RoutingStepDetail([], None, None, None), "NO_ROUTE")
    assert str(step) == "NO_ROUTE"


def test_match_tcp_generators():
    assert MatchTcpFlags.match_ack() == MatchTcpFlags(TcpFlags(ack=True), useAck=True)
    assert MatchTcpFlags.match_rst() == MatchTcpFlags(TcpFlags(rst=True), useRst=True)
    assert MatchTcpFlags.match_syn() == MatchTcpFlags(TcpFlags(syn=True), useSyn=True)
    assert MatchTcpFlags.match_synack() == MatchTcpFlags(
        TcpFlags(ack=True, syn=True), useAck=True, useSyn=True
    )
    assert len(MatchTcpFlags.match_established()) == 2
    assert MatchTcpFlags.match_established() == [
        MatchTcpFlags.match_ack(),
        MatchTcpFlags.match_rst(),
    ]
    assert MatchTcpFlags.match_not_established() == [
        MatchTcpFlags(useAck=True, useRst=True, tcpFlags=TcpFlags(ack=False, rst=False))
    ]


def test_flow_repr_html_ports():
    # ICMP flows do not have ports
    flow_dict = {
        "dscp": 0,
        "dstIp": "2.1.1.1",
        "dstPort": 0,
        "ecn": 0,
        "fragmentOffset": 0,
        "icmpCode": 255,
        "icmpVar": 255,
        "ingressNode": "ingress",
        "ipProtocol": "ICMP",
        "packetLength": 0,
        "srcIp": "5.5.1.1",
        "srcPort": 0,
        "tcpFlagsAck": 0,
        "tcpFlagsCwr": 0,
        "tcpFlagsEce": 0,
        "tcpFlagsFin": 0,
        "tcpFlagsPsh": 0,
        "tcpFlagsRst": 0,
        "tcpFlagsSyn": 0,
        "tcpFlagsUrg": 0,
    }
    assert "Port" not in Flow.from_dict(flow_dict)._repr_html_()

    # UDP
    flow_dict["ipProtocol"] = "UDP"
    assert "Port" in Flow.from_dict(flow_dict)._repr_html_()


def test_flow_repr_html_start_location():
    # ICMP flows do not have ports
    flow_dict = {
        "dscp": 0,
        "dstIp": "2.1.1.1",
        "dstPort": 0,
        "ecn": 0,
        "fragmentOffset": 0,
        "icmpCode": 255,
        "icmpVar": 255,
        "ingressNode": "ingressNode",
        "ingressVrf": "default",
        "ipProtocol": "ICMP",
        "packetLength": 0,
        "srcIp": "5.5.1.1",
        "srcPort": 0,
        "tcpFlagsAck": 0,
        "tcpFlagsCwr": 0,
        "tcpFlagsEce": 0,
        "tcpFlagsFin": 0,
        "tcpFlagsPsh": 0,
        "tcpFlagsRst": 0,
        "tcpFlagsSyn": 0,
        "tcpFlagsUrg": 0,
    }

    assert "Start Location: ingressNode" in Flow.from_dict(flow_dict)._repr_html_lines()

    flow_dict["ingressVrf"] = "ingressVrf"
    assert (
        "Start Location: ingressNode vrf=ingressVrf"
        in Flow.from_dict(flow_dict)._repr_html_lines()
    )

    del flow_dict["ingressVrf"]
    flow_dict["ingressInterface"] = "ingressIface"

    flow = Flow.from_dict(flow_dict)
    assert (
        "Start Location: ingressNode interface=ingressIface" in flow._repr_html_lines()
    )


def test_flow_str_ports():
    # ICMP flows do not have ports
    flow_dict = {
        "dscp": 0,
        "dstIp": "2.1.1.1",
        "dstPort": 1234,
        "ecn": 0,
        "fragmentOffset": 0,
        "icmpCode": 255,
        "icmpVar": 255,
        "ingressNode": "ingress",
        "ipProtocol": "ICMP",
        "packetLength": 0,
        "srcIp": "5.5.1.1",
        "srcPort": 2345,
        "tcpFlagsAck": 0,
        "tcpFlagsCwr": 0,
        "tcpFlagsEce": 0,
        "tcpFlagsFin": 0,
        "tcpFlagsPsh": 0,
        "tcpFlagsRst": 0,
        "tcpFlagsSyn": 0,
        "tcpFlagsUrg": 0,
    }
    s = repr(Flow.from_dict(flow_dict))
    assert "2.1.1.1:1234" not in s
    assert "5.5.1.1:2345" not in s

    # UDP
    flow_dict["ipProtocol"] = "UDP"
    s = repr(Flow.from_dict(flow_dict))
    assert "2.1.1.1:1234" not in s
    assert "5.5.1.1:2345" not in s


def test_InboundStepDetail_from_dict():
    interface = "GigabitEthernet1/0"
    d = {"type": "InboundStep", "interface": interface, "action": "ACCEPTED"}
    assert InboundStepDetail.from_dict(d) == InboundStepDetail(interface)


def test_InboundStepDetail_str():
    interface = "GigabitEthernet1/0"
    assert str(InboundStepDetail(interface)) == interface


def test_LoopStep_from_dict():
    step = Step.from_dict({"type": "Loop", "action": "LOOP", "detail": {}})
    assert step.action == "LOOP"
    assert step.detail == LoopStepDetail()


def test_LoopStepDetail_str():
    assert str(LoopStepDetail()) == ""


def test_SetupSessionStepDetail_from_dict():
    d = {
        "sessionScope": {"incomingInterfaces": ["reth0.6"]},
        "sessionAction": {"type": "Accept"},
        "matchCriteria": {"ipProtocol": "ICMP", "srcIp": "2.2.2.2", "dstIp": "3.3.3.3"},
        "transformation": [
            {"fieldName": "srcIp", "oldValue": "2.2.2.2", "newValue": "1.1.1.1"}
        ],
    }
    assert SetupSessionStepDetail.from_dict(d) == SetupSessionStepDetail(
        IncomingSessionScope(["reth0.6"]),
        Accept(),
        SessionMatchExpr("ICMP", "2.2.2.2", "3.3.3.3"),
        [FlowDiff("srcIp", "2.2.2.2", "1.1.1.1")],
    )


def test_SetupSessionStepDetail_from_dict_bw_compat():
    """
    For backward compatibility, allow "incomingInterfaces" instead of
    "sessionScope".
    """
    d = {
        "incomingInterfaces": ["reth0.6"],
        "sessionAction": {"type": "Accept"},
        "matchCriteria": {"ipProtocol": "ICMP", "srcIp": "2.2.2.2", "dstIp": "3.3.3.3"},
        "transformation": [
            {"fieldName": "srcIp", "oldValue": "2.2.2.2", "newValue": "1.1.1.1"}
        ],
    }
    assert SetupSessionStepDetail.from_dict(d) == SetupSessionStepDetail(
        IncomingSessionScope(["reth0.6"]),
        Accept(),
        SessionMatchExpr("ICMP", "2.2.2.2", "3.3.3.3"),
        [FlowDiff("srcIp", "2.2.2.2", "1.1.1.1")],
    )


def test_SetupSessionStepDetail_str():
    detail = SetupSessionStepDetail(
        IncomingSessionScope(["reth0.6"]),
        Accept(),
        SessionMatchExpr("ICMP", "2.2.2.2", "3.3.3.3"),
        [FlowDiff("srcIp", "2.2.2.2", "1.1.1.1")],
    )
    assert str(detail) == (
        "Incoming Interfaces: [reth0.6], "
        "Action: Accept, "
        "Match Criteria: [ipProtocol=ICMP, srcIp=2.2.2.2, dstIp=3.3.3.3], "
        "Transformation: [srcIp: 2.2.2.2 -> 1.1.1.1]"
    )
    detail = SetupSessionStepDetail(
        IncomingSessionScope(["reth0.6"]),
        Accept(),
        SessionMatchExpr("ICMP", "2.2.2.2", "3.3.3.3"),
    )
    assert str(detail) == (
        "Incoming Interfaces: [reth0.6], "
        "Action: Accept, "
        "Match Criteria: [ipProtocol=ICMP, srcIp=2.2.2.2, dstIp=3.3.3.3]"
    )


def test_MatchSessionStepDetail_from_dict():
    d = {
        "sessionScope": {"incomingInterfaces": ["reth0.6"]},
        "sessionAction": {"type": "Accept"},
        "matchCriteria": {"ipProtocol": "ICMP", "srcIp": "2.2.2.2", "dstIp": "3.3.3.3"},
        "transformation": [
            {"fieldName": "srcIp", "oldValue": "2.2.2.2", "newValue": "1.1.1.1"}
        ],
    }
    assert MatchSessionStepDetail.from_dict(d) == MatchSessionStepDetail(
        IncomingSessionScope(["reth0.6"]),
        Accept(),
        SessionMatchExpr("ICMP", "2.2.2.2", "3.3.3.3"),
        [FlowDiff("srcIp", "2.2.2.2", "1.1.1.1")],
    )


def test_MatchSessionStepDetail_from_dict_bw_compat():
    """
    For backward compatibility, allow "incomingInterfaces" instead of
    "sessionScope".
    """
    d = {
        "incomingInterfaces": ["reth0.6"],
        "sessionAction": {"type": "Accept"},
        "matchCriteria": {"ipProtocol": "ICMP", "srcIp": "2.2.2.2", "dstIp": "3.3.3.3"},
        "transformation": [
            {"fieldName": "srcIp", "oldValue": "2.2.2.2", "newValue": "1.1.1.1"}
        ],
    }
    assert MatchSessionStepDetail.from_dict(d) == MatchSessionStepDetail(
        IncomingSessionScope(["reth0.6"]),
        Accept(),
        SessionMatchExpr("ICMP", "2.2.2.2", "3.3.3.3"),
        [FlowDiff("srcIp", "2.2.2.2", "1.1.1.1")],
    )


def test_MatchSessionStepDetail_str():
    detail = MatchSessionStepDetail(
        IncomingSessionScope(["reth0.6"]),
        Accept(),
        SessionMatchExpr("ICMP", "2.2.2.2", "3.3.3.3"),
        [FlowDiff("srcIp", "2.2.2.2", "1.1.1.1")],
    )
    assert str(detail) == (
        "Incoming Interfaces: [reth0.6], "
        "Action: Accept, "
        "Match Criteria: [ipProtocol=ICMP, srcIp=2.2.2.2, dstIp=3.3.3.3], "
        "Transformation: [srcIp: 2.2.2.2 -> 1.1.1.1]"
    )
    detail = MatchSessionStepDetail(
        IncomingSessionScope(["reth0.6"]),
        Accept(),
        SessionMatchExpr("ICMP", "2.2.2.2", "3.3.3.3"),
    )
    assert str(detail) == (
        "Incoming Interfaces: [reth0.6], "
        "Action: Accept, "
        "Match Criteria: [ipProtocol=ICMP, srcIp=2.2.2.2, dstIp=3.3.3.3]"
    )


def test_SessionMatchExpr_from_dict():
    d = {"ipProtocol": "ICMP", "srcIp": "1.1.1.1", "dstIp": "2.2.2.2"}
    assert SessionMatchExpr.from_dict(d) == SessionMatchExpr(
        "ICMP", "1.1.1.1", "2.2.2.2"
    )
    d = {
        "ipProtocol": "ICMP",
        "srcIp": "1.1.1.1",
        "dstIp": "2.2.2.2",
        "srcPort": 1111,
        "dstPort": 2222,
    }
    assert SessionMatchExpr.from_dict(d) == SessionMatchExpr(
        "ICMP", "1.1.1.1", "2.2.2.2", 1111, 2222
    )


def test_SessionMatchExpr_str():
    match = SessionMatchExpr("ICMP", "1.1.1.1", "2.2.2.2")
    assert str(match) == "[ipProtocol=ICMP, srcIp=1.1.1.1, dstIp=2.2.2.2]"
    match = SessionMatchExpr("ICMP", "1.1.1.1", "2.2.2.2", 1111, 2222)
    assert str(match) == (
        "[ipProtocol=ICMP, srcIp=1.1.1.1, dstIp=2.2.2.2, srcPort=1111, dstPort=2222]"
    )


def test_SessionScope_from_dict():
    d = {"incomingInterfaces": ["iface"]}
    assert SessionScope.from_dict(d) == IncomingSessionScope(["iface"])
    d = {"originatingVrf": "vrf"}
    assert SessionScope.from_dict(d) == OriginatingSessionScope("vrf")


def test_IncomingSessionScope_str():
    scope = IncomingSessionScope(["iface1", "iface2"])
    assert str(scope) == "Incoming Interfaces: [iface1, iface2]"


def test_OriginatingSessionScope_str():
    scope = OriginatingSessionScope("vrf")
    assert str(scope) == "Originating VRF: vrf"


def test_SessionAction_from_dict():
    assert SessionAction.from_dict({"type": "Accept"}) == Accept()
    assert SessionAction.from_dict({"type": "FibLookup"}) == PostNatFibLookup()
    assert SessionAction.from_dict({"type": "PostNatFibLookup"}) == PostNatFibLookup()
    assert SessionAction.from_dict({"type": "PreNatFibLookup"}) == PreNatFibLookup()
    d = {
        "type": "ForwardOutInterface",
        "nextHop": {"hostname": "1.1.1.1", "interface": "iface1"},
        "outgoingInterface": "iface2",
    }
    assert SessionAction.from_dict(d) == ForwardOutInterface(
        "1.1.1.1", "iface1", "iface2"
    )
    with pytest.raises(ValueError):
        SessionAction.from_dict({"type": "NotAType"})


def test_SessionAction_str():
    assert str(Accept()) == "Accept"
    assert str(PostNatFibLookup()) == "PostNatFibLookup"
    assert str(PreNatFibLookup()) == "PreNatFibLookup"
    assert str(ForwardOutInterface("1.1.1.1", "iface1", "iface2")) == (
        "ForwardOutInterface(Next Hop: 1.1.1.1, Next Hop Interface: iface1, Outgoing Interface: iface2)"
    )


def test_header_constraints_of():
    hc = HeaderConstraints.of(
        Flow(
            ipProtocol="ICMP",
            icmpCode=7,
            srcIp="1.1.1.1",
            dstIp="2.2.2.2",
            dscp=0,
            dstPort=0,
            srcPort=0,
            ecn=0,
            fragmentOffset=0,
            icmpVar=0,
            ingressInterface="",
            ingressNode="",
            ingressVrf="",
            packetLength=0,
            tcpFlagsAck=0,
            tcpFlagsCwr=0,
            tcpFlagsEce=0,
            tcpFlagsFin=0,
            tcpFlagsPsh=0,
            tcpFlagsRst=0,
            tcpFlagsSyn=0,
            tcpFlagsUrg=0,
        )
    )
    assert hc.srcIps == "1.1.1.1"
    assert hc.dstIps == "2.2.2.2"
    assert hc.ipProtocols == ["ICMP"]
    assert hc.icmpCodes == "7"
    assert hc.srcPorts is None
    assert hc.dstPorts is None
    assert hc.tcpFlags is None

    hc = HeaderConstraints.of(
        Flow(
            ipProtocol="TCP",
            srcPort=1000,
            dstPort=2000,
            tcpFlagsAck=True,
            srcIp="1.1.1.1",
            dstIp="2.2.2.2",
            dscp=0,
            ecn=0,
            fragmentOffset=0,
            icmpCode=0,
            icmpVar=0,
            ingressInterface="",
            ingressNode="",
            ingressVrf="",
            packetLength=0,
            tcpFlagsCwr=0,
            tcpFlagsEce=0,
            tcpFlagsFin=0,
            tcpFlagsPsh=0,
            tcpFlagsRst=0,
            tcpFlagsSyn=0,
            tcpFlagsUrg=0,
        )
    )
    assert hc.srcIps == "1.1.1.1"
    assert hc.dstIps == "2.2.2.2"
    assert hc.ipProtocols == ["TCP"]
    assert hc.icmpCodes is None
    assert hc.icmpTypes is None
    assert hc.srcPorts == "1000"
    assert hc.dstPorts == "2000"
    assert hc.tcpFlags == [
        MatchTcpFlags(
            TcpFlags(ack=True),
            useAck=True,
            useCwr=True,
            useEce=True,
            useFin=True,
            usePsh=True,
            useRst=True,
            useSyn=True,
            useUrg=True,
        )
    ]


def testForwardingDetailCannotInstantiate():
    with pytest.raises(TypeError):
        ForwardingDetail()


def testForwardingDetailDeserializationInvalid():
    with pytest.raises(ValueError):
        ForwardingDetail.from_dict({"type": "foo"})
    with pytest.raises(ValueError):
        ForwardingDetail.from_dict({})


def testDelegatedToNextVrfSerialization():
    assert DelegatedToNextVrf("foo").dict() == {
        "type": "DelegatedToNextVrf",
        "nextVrf": "foo",
    }


def testDelegatedToNextVrfDeserialization():
    assert ForwardingDetail.from_dict(
        {"type": "DelegatedToNextVrf", "nextVrf": "foo"}
    ) == DelegatedToNextVrf("foo")
    assert DelegatedToNextVrf.from_dict(
        {"type": "DelegatedToNextVrf", "nextVrf": "foo"}
    ) == DelegatedToNextVrf("foo")


def testDelegatedToNextVrfStr():
    assert str(DelegatedToNextVrf("foo")) == "Delegated to next VRF: foo"
    assert str(DelegatedToNextVrf("foo bar")) == 'Delegated to next VRF: "foo bar"'


def testForwardedOutInterfaceSerialization():
    assert ForwardedOutInterface("foo").dict() == {
        "type": "ForwardedOutInterface",
        "outputInterface": "foo",
        "resolvedNextHopIp": None,
    }
    assert ForwardedOutInterface("foo", "1.1.1.1").dict() == {
        "type": "ForwardedOutInterface",
        "outputInterface": "foo",
        "resolvedNextHopIp": "1.1.1.1",
    }


def testForwardedOutInterfaceDeserialization():
    assert ForwardingDetail.from_dict(
        {"type": "ForwardedOutInterface", "outputInterface": "foo"}
    ) == ForwardedOutInterface("foo")
    assert ForwardedOutInterface.from_dict(
        {"type": "ForwardedOutInterface", "outputInterface": "foo"}
    ) == ForwardedOutInterface("foo")
    assert (
        ForwardedOutInterface.from_dict(
            {
                "type": "ForwardedOutInterface",
                "outputInterface": "foo",
                "resolvedNextHopIp": None,
            }
        )
        == ForwardedOutInterface("foo")
    )
    assert (
        ForwardedOutInterface.from_dict(
            {
                "type": "ForwardedOutInterface",
                "outputInterface": "foo",
                "resolvedNextHopIp": "1.1.1.1",
            }
        )
        == ForwardedOutInterface("foo", "1.1.1.1")
    )


def testForwardedOutInterfaceStr():
    assert str(ForwardedOutInterface("foo")) == "Forwarded out interface: foo"
    assert str(ForwardedOutInterface("foo bar")) == 'Forwarded out interface: "foo bar"'
    assert (
        str(ForwardedOutInterface("foo bar", "1.1.1.1"))
        == 'Forwarded out interface: "foo bar" with resolved next-hop IP: 1.1.1.1'
    )


def testForwardedIntoVxlanTunnelVtepSerialization():
    assert ForwardedIntoVxlanTunnel(5, "1.1.1.1").dict() == {
        "type": "ForwardedIntoVxlanTunnel",
        "vni": 5,
        "vtep": "1.1.1.1",
    }


def testForwardedIntoVxlanTunnelDeserialization():
    assert ForwardingDetail.from_dict(
        {"type": "ForwardedIntoVxlanTunnel", "vni": 5, "vtep": "1.1.1.1"}
    ) == ForwardedIntoVxlanTunnel(5, "1.1.1.1")
    assert ForwardedIntoVxlanTunnel.from_dict(
        {"type": "ForwardedIntoVxlanTunnel", "vni": 5, "vtep": "1.1.1.1"}
    ) == ForwardedIntoVxlanTunnel(5, "1.1.1.1")


def testForwardedIntoVxlanTunnelStr():
    assert (
        str(ForwardedIntoVxlanTunnel(5, "1.1.1.1"))
        == "Forwarded into VXLAN tunnel with VNI: 5 and VTEP: 1.1.1.1"
    )


def testDiscardedSerialization():
    assert Discarded().dict() == {"type": "Discarded"}


def testDiscardedDeserialization():
    assert ForwardingDetail.from_dict({"type": "Discarded"}) == Discarded()
    assert Discarded.from_dict({"type": "Discarded"}) == Discarded()


def testDiscardedStr():
    assert str(Discarded()) == "Discarded"


def testRouteInfoSerialization():
    assert RouteInfo("tcp", "1.1.1.1/32", NextHopDiscard(), None, 1, 2).dict() == {
        "protocol": "tcp",
        "network": "1.1.1.1/32",
        "nextHop": {"type": "discard"},
        "nextHopIp": None,
        "admin": 1,
        "metric": 2,
    }


# TODO: remove after sufficient period
def testRouteInfoSerialization_legacy():
    assert RouteInfo("tcp", "1.1.1.1/32", None, "2.2.2.2", 1, 2).dict() == {
        "protocol": "tcp",
        "network": "1.1.1.1/32",
        "nextHop": None,
        "nextHopIp": "2.2.2.2",
        "admin": 1,
        "metric": 2,
    }


def testRouteInfoDeserialization():
    assert (
        RouteInfo.from_dict(
            {
                "protocol": "tcp",
                "network": "1.1.1.1/32",
                "nextHop": {"type": "discard"},
                "admin": 1,
                "metric": 2,
            }
        )
        == RouteInfo("tcp", "1.1.1.1/32", NextHopDiscard(), None, 1, 2)
    )


# TODO: remove after sufficient period
def testRouteInfoDeserialization_legacy():
    assert (
        RouteInfo.from_dict(
            {
                "protocol": "tcp",
                "network": "1.1.1.1/32",
                "nextHopIp": "2.2.2.2",
                "admin": 1,
                "metric": 2,
            }
        )
        == RouteInfo("tcp", "1.1.1.1/32", None, "2.2.2.2", 1, 2)
    )


def testRouteInfoStr():
    assert (
        str(RouteInfo("tcp", "1.1.1.1/32", NextHopDiscard(), None, 1, 2))
        == "tcp (Network: 1.1.1.1/32, Next Hop: discard)"
    )


# TODO: remove after sufficient period
def testRouteInfoStr_legacy():
    assert (
        str(RouteInfo("tcp", "1.1.1.1/32", None, "2.2.2.2", 1, 2))
        == "tcp (Network: 1.1.1.1/32, Next Hop IP:2.2.2.2)"
    )


if __name__ == "__main__":
    pytest.main()
