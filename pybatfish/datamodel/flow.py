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
from typing import Any, Dict, List, Optional  # noqa: F401

import attr

from .primitives import DataModelElement, Edge

__all__ = ['Flow', 'FlowTrace', 'FlowTraceHop']


@attr.s(frozen=True)
class Flow(DataModelElement):
    """A concrete IPv4 flow.

    Noteworthy attributes for flow inspection/filtering:

    :ivar srcIP: Source IP of the flow
    :ivar dstIP: Destination IP of the flow
    :ivar srcPort: Source port of the flow
    :ivar dstPort: Destionation port of the flow
    :ivar ipProtocol: the IP protocol of the flow
        (as integer, e.g., 1=ICMP, 6=TCP, 17=UDP)
    :ivar ingressNode: the node where the flow started (or entered the network)
    :ivar ingressInteface: the interface name where the flow started (or entered the network)
    :ivar ingressVrf: the VRF name where the flow started (or entered the network)
    """

    dscp = attr.ib(type=int, converter=int)
    dstIp = attr.ib(type=str, converter=str)
    dstPort = attr.ib(type=int, converter=int)
    ecn = attr.ib(type=int, converter=int)
    fragmentOffset = attr.ib(type=int, converter=int)
    icmpCode = attr.ib(type=int, converter=int)
    icmpVar = attr.ib(type=int, converter=int)
    ingressInterface = attr.ib(type=Optional[str])
    ingressNode = attr.ib(type=Optional[str])
    ingressVrf = attr.ib(type=Optional[str])
    ipProtocol = attr.ib(type=str)
    packetLength = attr.ib(type=str)
    srcIp = attr.ib(type=str, converter=str)
    srcPort = attr.ib(type=int, converter=int)
    state = attr.ib(type=str, converter=str)
    tag = attr.ib(type=str, converter=str)
    tcpFlagsAck = attr.ib(type=int, converter=int)
    tcpFlagsCwr = attr.ib(type=int, converter=int)
    tcpFlagsEce = attr.ib(type=int, converter=int)
    tcpFlagsFin = attr.ib(type=int, converter=int)
    tcpFlagsPsh = attr.ib(type=int, converter=int)
    tcpFlagsRst = attr.ib(type=int, converter=int)
    tcpFlagsSyn = attr.ib(type=int, converter=int)
    tcpFlagsUrg = attr.ib(type=int, converter=int)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> Flow
        return Flow(
            json_dict["dscp"],
            json_dict["dstIp"],
            json_dict["dstPort"],
            json_dict["ecn"],
            json_dict["fragmentOffset"],
            json_dict["icmpCode"],
            json_dict["icmpVar"],
            json_dict.get("ingressInterface"),
            json_dict.get("ingressNode"),
            json_dict.get("ingressVrf"),
            json_dict["ipProtocol"],
            json_dict["packetLength"],
            json_dict["srcIp"],
            json_dict["srcPort"],
            json_dict["state"],
            json_dict["tag"],
            json_dict["tcpFlagsAck"],
            json_dict["tcpFlagsCwr"],
            json_dict["tcpFlagsEce"],
            json_dict["tcpFlagsFin"],
            json_dict["tcpFlagsPsh"],
            json_dict["tcpFlagsRst"],
            json_dict["tcpFlagsSyn"],
            json_dict["tcpFlagsUrg"])

    def __str__(self):
        # type: () -> str
        # exclude the tag field
        iface_str = "ingressInterface: {}".format(self.ingressInterface) \
            if self.ingressInterface is not None else ""
        vrf_str = "vrf: {}".format(self.ingressVrf) \
            if self.ingressVrf != "default" else ""
        return \
            "{node}{iface}{vrf}->[{src_ip}:{src_port}->{dst_ip}:{dst_port}" \
            " proto: {proto} dscp:{dscp} ecn:{ecn} fragOff:{offset} length" \
            ":{length} state:{state} flags: {flags}".format(
                node=self.ingressNode,
                iface=iface_str,
                vrf=vrf_str,
                src_ip=self.srcIp,
                src_port=self.srcPort,
                dst_ip=self.dstIp,
                dst_port=self.dstPort,
                proto=self.ipProtocol,
                dscp=self.dscp,
                ecn=self.ecn,
                offset=self.fragmentOffset,
                length=self.packetLength,
                state=self.state,
                flags=self.get_flag_str())

    def get_flag_str(self):
        # type: () -> str
        if self.ipProtocol == 6:  # TCP
            return "{}{}{}{}{}{}{}{}".format(self.tcpFlagsAck, self.tcpFlagsCwr,
                                             self.tcpFlagsEce, self.tcpFlagsFin,
                                             self.tcpFlagsPsh, self.tcpFlagsRst,
                                             self.tcpFlagsSyn, self.tcpFlagsUrg)
        else:
            return "n/a"


@attr.s(frozen=True)
class FlowTrace(DataModelElement):
    """A trace of a flow through the network.

    A flowTrace is a combination of hops and flow fate (i.e., disposition).

    :ivar disposition: Flow disposition
    :ivar hops: A list of hops (:py:class:`FlowTraceHop`) the flow took
    :ivar notes: Additional notes that help explain the disposition, if applicable.
    """

    disposition = attr.ib()
    hops = attr.ib()
    notes = attr.ib()

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> FlowTrace
        return FlowTrace(json_dict["disposition"],
                         [FlowTraceHop.from_dict(hop) for hop in
                          json_dict.get("hops", [])],
                         json_dict.get("notes"))

    def __str__(self):
        # type: () -> str
        return "{hops}\n{notes}".format(
            hops="\n".join(["{} {}".format(num, hop) for num, hop in
                            enumerate(self.hops, start=1)]),
            notes=self.notes)


@attr.s(frozen=True)
class FlowTraceHop(DataModelElement):
    """A single hop in a flow trace.

    :ivar edge: The :py:class:`~Edge` identifying the hop/link
    :ivar routes: The routes which caused this hop
    :ivar transformed_flow: The transformed version of the flow (if NAT is present)
    """

    edge = attr.ib(type=Edge)
    routes = attr.ib(type=List[Any])
    transformedFlow = attr.ib(type=Optional[Flow])

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> FlowTraceHop
        transformed_flow = json_dict.get("transformedFlow")
        return FlowTraceHop(Edge.from_dict(json_dict["edge"]),
                            list(json_dict.get("routes", [])),
                            Flow.from_dict(transformed_flow)
                            if transformed_flow else None)

    def __str__(self):
        # type: () -> str
        ret_str = "{}\n    Route(s):\n    {}".format(
            self.edge, "\n    ".join(self.routes))
        if self.transformedFlow:
            ret_str += "\n    Transformed flow: {}".format(
                self.transformedFlow)
        return ret_str
