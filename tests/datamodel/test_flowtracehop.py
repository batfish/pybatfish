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

import pytest

from pybatfish.datamodel.flow import FlowTraceHop


# test if a flowtracehop is deserialized properly and converted to string properly
def testFlowTraceHopDeserialization():
    hopDict = {
        "edge": {
            "node1": "node1",
            "node1interface": "Ethernet9",
            "node2": "(none)",
            "node2interface": "null_interface",
        },
        "routes": ["BgpRoute<12.10.16.8/25,nhip:9.1.1.2,nhint:dynamic>_fnhip:9.1.1.2"],
        "transformedFlow": {
            "dscp": 0,
            "dstIp": "2.1.1.1",
            "dstPort": 0,
            "ecn": 0,
            "fragmentOffset": 0,
            "icmpCode": 255,
            "icmpVar": 255,
            "ingressNode": "ingress",
            "ingressVrf": "default",
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
    hop = FlowTraceHop.from_dict(hopDict)
    hopStr = str(hop)

    # check deserialization
    assert hop.edge
    assert len(hop.routes) == 1
    assert hop.transformedFlow

    # check the string representation has the essential elements (without forcing a strict format)
    assert str(hop.edge) in hopStr
    assert str(hop.routes[0]) in hopStr
    assert str(hop.transformedFlow) in hopStr


# test that deserialization can tolerate hops with no routes.
def testFlowTraceHopDeserialization_noRoutes():
    hopDict = {
        "edge": {
            "node1": "node1",
            "node1interface": "Ethernet9",
            "node2": "(none)",
            "node2interface": "null_interface",
        }
    }
    hop = FlowTraceHop.from_dict(hopDict)

    # check deserialization
    assert hop.routes == []


if __name__ == "__main__":
    pytest.main()
