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

from pybatfish.datamodel.flow import (
    EnterInputIfaceStepDetail,
    ExitOutputIfaceStepDetail,
    FilterStepDetail,
    Flow,
    FlowDiff,
    FlowTraceHop,
    HeaderConstraints,
    Hop,
    MatchSessionStepDetail,
    MatchTcpFlags,
    RoutingStepDetail,
    SetupSessionStepDetail,
    Step,
    TcpFlags,
    TransformationStepDetail,
)


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
        "ipProtocol": "IP",
        "packetLength": 0,
        "srcIp": "5.5.1.1",
        "srcPort": 0,
        "state": "NEW",
        "tag": "BASE",
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
        "ipProtocol": "IP",
        "packetLength": 0,
        "srcIp": "5.5.1.1",
        "srcPort": 0,
        "state": "NEW",
        "tag": "BASE",
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


def test_get_ip_protocol_str():
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
        "state": "NEW",
        "tag": "BASE",
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

    flow_dict["ipProtocol"] = "TCP"
    assert Flow.from_dict(flow_dict).get_ip_protocol_str() == "TCP"


def test_header_constraints_serialization():
    hc = HeaderConstraints()
    hcd = hc.dict()
    fields = set(map(attrgetter("name"), attr.fields(HeaderConstraints))) - {
        "firewallClassifications"
    } | {"flowStates"}
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
                        {
                            "network": "1.1.1.1/24",
                            "protocol": "bgp",
                            "nextHopIp": "1.2.3.4",
                        },
                        {
                            "network": "1.1.1.2/24",
                            "protocol": "static",
                            "nextHopIp": "1.2.3.5",
                        },
                    ]
                ),
                "FORWARDED",
            ),
            Step(FilterStepDetail("preSourceNat_filter", "PRENAT"), "PERMITTED"),
            Step(ExitOutputIfaceStepDetail("out_iface1", None), "SENT_OUT"),
        ],
    )

    assert (
        str(hop)
        == "node: node1\n  SENT_IN(in_iface1)\n  FORWARDED(Routes: bgp [Network: 1.1.1.1/24, Next Hop IP:1.2.3.4],static [Network: 1.1.1.2/24, Next Hop IP:1.2.3.5])\n  PERMITTED(preSourceNat_filter (PRENAT))\n  SENT_OUT(out_iface1)"
    )


def test_no_route():
    step = Step(RoutingStepDetail([]), "NO_ROUTE")
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
        "state": "NEW",
        "tag": "BASE",
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
        "state": "NEW",
        "tag": "BASE",
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


def test_flow_repr_html_state():
    # ICMP flows do not have ports
    flow_dict = {
        "dscp": 0,
        "dstIp": "2.1.1.1",
        "dstPort": 0,
        "ecn": 0,
        "fragmentOffset": 0,
        "icmpCode": 0,
        "icmpVar": 0,
        "ingressNode": "ingress",
        "ipProtocol": "TCP",
        "packetLength": 0,
        "srcIp": "5.5.1.1",
        "srcPort": 0,
        "state": "NEW",
        "tag": "BASE",
        "tcpFlagsAck": 0,
        "tcpFlagsCwr": 0,
        "tcpFlagsEce": 0,
        "tcpFlagsFin": 0,
        "tcpFlagsPsh": 0,
        "tcpFlagsRst": 0,
        "tcpFlagsSyn": 0,
        "tcpFlagsUrg": 0,
    }
    assert "Firewall Classification" not in Flow.from_dict(flow_dict)._repr_html_()

    # ESTABLISHED
    flow_dict["state"] = "ESTABLISHED"
    assert (
        "Firewall Classification: ESTABLISHED"
        in Flow.from_dict(flow_dict)._repr_html_()
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
        "state": "NEW",
        "tag": "BASE",
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


def test_SetupSessionStepDetail_from_dict():
    d = {"type": "SetupSession", "action": "SETUP_SESSION"}
    assert SetupSessionStepDetail.from_dict(d) == SetupSessionStepDetail()


def test_SetupSessionStepDetail_str():
    assert str(SetupSessionStepDetail()) == ""


def test_MatchSessionStepDetail_from_dict():
    d = {"type": "MatchSession", "action": "MATCHED_SESSION"}
    assert MatchSessionStepDetail.from_dict(d) == MatchSessionStepDetail()


def test_MatchSessionStepDetail_str():
    assert str(MatchSessionStepDetail()) == ""


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
            state="new",
            tag="tag",
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
            state="new",
            tag="tag",
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


if __name__ == "__main__":
    pytest.main()
