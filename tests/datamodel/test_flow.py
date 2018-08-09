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

from pybatfish.datamodel.flow import Flow
# test if a flow is deserialized properly and its string is fine
from pybatfish.datamodel.flowtracehop import FlowTraceHop
import pytest


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
    flow = Flow(hopDict)
    assert flow.srcIp == "5.5.1.1"
    assert flow.ingressInterface == "intface"
    assert flow.ingressVrf == "vrfAbc"

    # check the string representation has the essential elements (without forcing a strict format)
    flowStr = str(flow)
    assert "5.5.1.1" in flowStr
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
    flow = Flow(hopDict)
    assert flow.srcIp == "5.5.1.1"

    # should convert to string without problems
    str(flow)


def test_flow_trace_hop_no_transformed_flow():
    """Test we don't crash on missing or None values."""
    FlowTraceHop(
        {'edge': {'node1': 'dummy', 'node1interface': 'eth0',
                  'node2': 'router1', 'node2interface': 'Ethernet1'},
         'filterIn': None, 'filterOut': None, 'routes': [
            'StaticRoute<0.0.0.0/0,nhip:10.192.48.1,nhint:eth0>_fnhip:10.192.48.1'],
         'transformedFlow': None})

    FlowTraceHop(
        {'edge': {'node1': 'dummy', 'node1interface': 'eth0',
                  'node2': 'router1', 'node2interface': 'Ethernet1'},
         'filterIn': None, 'filterOut': None, 'routes': [
            'StaticRoute<0.0.0.0/0,nhip:10.192.48.1,nhint:eth0>_fnhip:10.192.48.1']})


if __name__ == "__main__":
    pytest.main()
