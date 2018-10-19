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

import attr
import pytest

from pybatfish.datamodel.flow import (Flow, FlowTraceHop, HeaderConstraints,
                                      Hop, Trace)


def testFlowDeserialization():
    hopDict = {
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
        "tcpFlagsUrg": 0
    }

    # check deserialization
    flow = Flow.from_dict(hopDict)
    assert flow.srcIp == "5.5.1.1"
    assert flow.ingressInterface == "intface"
    assert flow.ingressVrf == "vrfAbc"

    # check the string representation has the essential elements (without forcing a strict format)
    flowStr = str(flow)
    assert "5.5.1.1:0" in flowStr
    assert "intface" in flowStr
    assert "vrfAbc" in flowStr


# test if a flow is deserialized properly when the optional fields are missing
def testFlowDeserializationOptionalMissing():
    hopDict = {
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
        "tcpFlagsUrg": 0
    }
    # check deserialization
    flow = Flow.from_dict(hopDict)
    assert flow.srcIp == "5.5.1.1"

    # should convert to string without problems
    str(flow)


def test_flow_trace_hop_no_transformed_flow():
    """Test we don't crash on missing or None values."""
    FlowTraceHop.from_dict(
        {'edge': {'node1': 'dummy', 'node1interface': 'eth0',
                  'node2': 'router1', 'node2interface': 'Ethernet1'},
         'filterIn': None, 'filterOut': None, 'routes': [
            'StaticRoute<0.0.0.0/0,nhip:10.192.48.1,nhint:eth0>_fnhip:10.192.48.1'],
         'transformedFlow': None})

    FlowTraceHop.from_dict(
        {'edge': {'node1': 'dummy', 'node1interface': 'eth0',
                  'node2': 'router1', 'node2interface': 'Ethernet1'},
         'filterIn': None, 'filterOut': None, 'routes': [
            'StaticRoute<0.0.0.0/0,nhip:10.192.48.1,nhint:eth0>_fnhip:10.192.48.1']})


def test_get_ip_protocol_str():
    flowDict = {
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
        "tcpFlagsUrg": 0
    }
    assert Flow.from_dict(flowDict).get_ip_protocol_str() == "ipProtocol=243"

    flowDict["ipProtocol"] = "TCP"
    assert Flow.from_dict(flowDict).get_ip_protocol_str() == "TCP"


def test_header_constraints_serialization():
    hc = HeaderConstraints()
    hcd = hc.dict()
    for field in attr.fields(HeaderConstraints):
        assert hcd[field.name] is None

    hc = HeaderConstraints(srcIps="1.1.1.1")
    assert hc.dict()["srcIps"] == "1.1.1.1"

    hc = HeaderConstraints(dstPorts=["10-20", "33-33"])
    assert hc.dict()["dstPorts"] == "10-20,33-33"

    hc = HeaderConstraints(dstPorts="10-20,33")
    assert hc.dict()["dstPorts"] == "10-20,33"


def test_trace():
    trace = Trace(disposition='accepted', hops=[])
    assert len(trace) == 0
    with pytest.raises(IndexError):
        assert trace[0]

    trace = Trace(disposition='accepted', hops=[Hop('node1', [])])
    assert len(trace) == 1
    assert len(trace[0]) == 0

    trace = Trace(disposition='accepted',
                  hops=[Hop('node1',
                            [{'action': 'secret_action'}])])
    assert trace.final_detail() == {}

    trace = Trace(disposition='accepted',
                  hops=[Hop('node1',
                            [{'action': 'secret_action', 'detail': 'secret'}])])
    assert trace.final_detail() == 'secret'


def test_disposition_detail():
    trace = Trace(disposition="DENIED_IN", hops=[Hop('node1', [
        {'action': 'BLOCKED', 'detail': {
            'inputInterface': {'interface': 'in_iface1', 'hostname': 'node1'},
            'inputFilter': 'in_filter1'}}])])
    assert trace.disposition_reason() == "Flow was BLOCKED at in_iface1 by filter in_filter1"


def test_get_all_filters():
    trace = Trace(disposition="ACCEPTED", hops=[
        Hop('node1', [
            {'action': 'SENT_IN', 'detail': {'inputInterface': 'in_iface1',
                                             'inputFilter': 'in_filter1'}},
            {'action': 'FORWARDED', 'detail': {'routes': []}},
            {'action': 'SENT_OUT', 'detail': {'outputInterface': 'out_iface1',
                                              'outputFilter': 'out_filter1'}}]),
        Hop('node2', [
            {'action': 'SENT_IN', 'detail': {'inputInterface': 'in_iface2',
                                             'inputFilter': 'in_filter2'}},
            {'action': 'FORWARDED', 'detail': {'routes': []}},
            {'action': 'SENT_OUT', 'detail': {'outputInterface': 'out_iface2',
                                              'outputFilter': 'out_filter2'}}])
    ])
    assert trace.get_all_filters() == ['in_filter1', 'out_filter1', 'in_filter2', 'out_filter2']


def test_hop_repr_str():
    hop = Hop('node1', [
        {'type': 'EnterInputInterface', 'action': 'SENT_IN', 'detail': {
            'inputInterface': {'interface': 'in_iface1', 'hostname': 'node1'},
            'inputFilter': 'in_filter1'}},
        {'type': 'Routing', 'action': 'FORWARDED', 'detail': {
            'routes': [{'network': '1.1.1.1/24', 'protocol': 'bgp',
                        'nextHopIp': '1.2.3.4'},
                       {'network': '1.1.1.2/24', 'protocol': 'static',
                        'nextHopIp': '1.2.3.5'}
                       ]}}
    ])
    assert str(
        hop) == "node: node1\n steps: SENT_IN (in_iface1) -> FORWARDED (Routes: bgp [Network: 1.1.1.1/24, Next Hop IP:1.2.3.4],static [Network: 1.1.1.2/24, Next Hop IP:1.2.3.5])"


if __name__ == "__main__":
    pytest.main()
