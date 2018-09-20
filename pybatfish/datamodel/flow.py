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

__all__ = ['Flow', 'FlowTrace', 'FlowTraceHop', 'HeaderConstraints']


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
        iface_str = " interface={}".format(self.ingressInterface) \
            if self.ingressInterface is not None else ""
        vrf_str = " vrf={}".format(self.ingressVrf) \
            if self.ingressVrf != "default" else ""
        ip_proto_str = "ipProtocol=" + self.ipProtocol if self.is_int(
            self.ipProtocol) else self.ipProtocol
        return \
            "start={node}{iface}{vrf} [{src_ip}:{src_port}->{dst_ip}:{dst_port}" \
            " {ip_proto}{dscp}{ecn}{offset}{length}{state}{flags}]".format(
                node=self.ingressNode,
                iface=iface_str,
                vrf=vrf_str,
                src_ip=self.srcIp,
                src_port=self.srcPort,
                dst_ip=self.dstIp,
                dst_port=self.dstPort,
                ip_proto=ip_proto_str,
                dscp=" dscp={}".format(self.dscp) if self.dscp != 0 else "",
                ecn=" ecn={}".format(self.ecn) if self.ecn != 0 else "",
                offset=" fragmentOffset={}".format(self.fragmentOffset) \
                    if self.fragmentOffset != 0 else "",
                length=" length={}".format(self.packetLength) \
                    if self.packetLength != 0 else "",
                state=" state={}".format(self.state) \
                    if self.state != "NEW" else "",
                flags=" tcpFlags={}".format(self.get_flag_str()) \
                    if self.get_flag_str() != "00000000" and
                       self.ipProtocol == 6 else "")

    def get_flag_str(self):
        # type: () -> str
        return "{}{}{}{}{}{}{}{}".format(self.tcpFlagsAck,
                                         self.tcpFlagsCwr,
                                         self.tcpFlagsEce,
                                         self.tcpFlagsFin,
                                         self.tcpFlagsPsh,
                                         self.tcpFlagsRst,
                                         self.tcpFlagsSyn,
                                         self.tcpFlagsUrg)

    def is_int(self, str):
        # type: (str) -> bool
        try:
            int(str)
            return True
        except ValueError:
            return False


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


@attr.s(frozen=True)
class HeaderConstraints(DataModelElement):
    """Constraints on an IPv4 packet header space.

    Specify constraints on packet headers by specifying lists of allowed values
    in each field of IP packet.

    :ivar srcIps: Source location/IP
    :vartype srcIps: str
    :ivar dstIps: Destination location/IP
    :vartype dstIps: str
    :ivar srcPorts: Source ports as list of ranges (e.g., ``["22-22", "53-99"]``)
    :ivar dstPorts: Destination ports as list of ranges, (e.g., ``["22-22", "53-99"]``)
    :ivar applications: Shorthands for application protocols (e.g., ``SSH``, ``DNS``, ``SNMP``)
    :ivar ipProtocols: List of well-known IP protocols (e.g., ``TCP``, ``UDP``, ``ICMP``)
    :ivar icmpCodes: List of integer ICMP codes
    :ivar icmpTypes: List of integer ICMP types
    :ivar flowStates: List of flow states (e.g., "new", "established")


    Lists of values in each fields are subject to a logical "OR":

    >>> HeaderConstraints(ipProtocols=["TCP", "UDP"])
    HeaderConstraints(srcIps=None, dstIps=None, srcPorts=None, dstPorts=None, ipProtocols=['TCP', 'UDP'], applications=None,
    icmpCodes=None, icmpTypes=None, flowStates=None, ecns=None, dscps=None, packetLengths=None, fragmentOffsets=None)

    means allow TCP OR UDP.

    Different fields are ANDed together:

    >>> HeaderConstraints(srcIps="1.1.1.1", dstIps="2.2.2.2", applications=["SSH"])
    HeaderConstraints(srcIps='1.1.1.1', dstIps='2.2.2.2', srcPorts=None, dstPorts=None, ipProtocols=None, applications=['SSH'],
    icmpCodes=None, icmpTypes=None, flowStates=None, ecns=None, dscps=None, packetLengths=None, fragmentOffsets=None)

    means an SSH connection originating at ``1.1.1.1`` and going to ``2.2.2.2``

    Any ``None`` values will be treated as unconstrained.
    """

    # Order params in likelihood of specification
    srcIps = attr.ib(default=None, type=Optional[str])
    dstIps = attr.ib(default=None, type=Optional[str])
    srcPorts = attr.ib(default=None, type=Optional[List[str]])
    dstPorts = attr.ib(default=None, type=Optional[List[str]])
    ipProtocols = attr.ib(default=None, type=Optional[List[str]])
    applications = attr.ib(default=None, type=Optional[List[str]])
    icmpCodes = attr.ib(default=None, type=Optional[List[str]])
    icmpTypes = attr.ib(default=None, type=Optional[List[str]])
    flowStates = attr.ib(default=None, type=Optional[List[str]])
    ecns = attr.ib(default=None, type=Optional[List[str]])
    dscps = attr.ib(default=None, type=Optional[List[str]])
    packetLengths = attr.ib(default=None, type=Optional[List[str]])
    fragmentOffsets = attr.ib(default=None, type=Optional[List[str]])

    @classmethod
    def from_dict(cls, json_dict):
        return HeaderConstraints(
            srcIps=json_dict.get("srcIps"),
            dstIps=json_dict.get("dstIps"),
            srcPorts=json_dict.get("srcPorts"),
            dstPorts=json_dict.get("dstPorts"),
            ipProtocols=json_dict.get("ipProtocols"),
            applications=json_dict.get("applications"),
            icmpCodes=json_dict.get("icmpCodes"),
            icmpTypes=json_dict.get("icmpTypes"),
            flowStates=json_dict.get("flowStates"),
            ecns=json_dict.get("ecns"),
            dscps=json_dict.get("dscps"),
            packetLengths=json_dict.get("packetLengths"),
            fragmentOffsets=json_dict.get("fragmentOffsets"))
