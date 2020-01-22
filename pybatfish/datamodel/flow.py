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
import re
from typing import Any, Dict, Iterable, List, Optional, Sequence, Text  # noqa: F401

import attr

from pybatfish.util import escape_html
from .primitives import DataModelElement, Edge

__all__ = [
    "ArpErrorStepDetail",
    "DeliveredStepDetail",
    "EnterInputIfaceStepDetail",
    "ExitOutputIfaceStepDetail",
    "FilterStepDetail",
    "Flow",
    "HeaderConstraints",
    "Hop",
    "InboundStepDetail",
    "MatchSessionStepDetail",
    "MatchTcpFlags",
    "OriginateStepDetail",
    "RoutingStepDetail",
    "SetupSessionStepDetail",
    "PathConstraints",
    "TcpFlags",
    "Trace",
    "TransformationStepDetail",
]


def _optional_int(x):
    # type: (Any) -> Optional[int]
    if x is None:
        return None
    return int(x)


@attr.s(frozen=True)
class Flow(DataModelElement):
    """A concrete IPv4 flow.

    Noteworthy attributes for flow inspection/filtering:

    :ivar srcIP: Source IP of the flow
    :ivar dstIP: Destination IP of the flow
    :ivar srcPort: Source port of the flow
    :ivar dstPort: Destination port of the flow
    :ivar ipProtocol: the IP protocol of the flow
        (as integer, e.g., 1=ICMP, 6=TCP, 17=UDP)
    :ivar ingressNode: the node where the flow started (or entered the network)
    :ivar ingressInterface: the interface name where the flow started (or entered the network)
    :ivar ingressVrf: the VRF name where the flow started (or entered the network)
    """

    dscp = attr.ib(type=int, converter=int)
    dstIp = attr.ib(type=str, converter=str)
    dstPort = attr.ib(type=Optional[int], converter=_optional_int)
    ecn = attr.ib(type=int, converter=int)
    fragmentOffset = attr.ib(type=int, converter=int)
    icmpCode = attr.ib(type=Optional[int], converter=_optional_int)
    icmpVar = attr.ib(type=Optional[int], converter=_optional_int)
    ingressInterface = attr.ib(type=Optional[str])
    ingressNode = attr.ib(type=Optional[str])
    ingressVrf = attr.ib(type=Optional[str])
    ipProtocol = attr.ib(type=str)
    packetLength = attr.ib(type=str)
    srcIp = attr.ib(type=str, converter=str)
    srcPort = attr.ib(type=Optional[int], converter=_optional_int)
    tcpFlagsAck = attr.ib(type=Optional[int], converter=_optional_int)
    tcpFlagsCwr = attr.ib(type=Optional[int], converter=_optional_int)
    tcpFlagsEce = attr.ib(type=Optional[int], converter=_optional_int)
    tcpFlagsFin = attr.ib(type=Optional[int], converter=_optional_int)
    tcpFlagsPsh = attr.ib(type=Optional[int], converter=_optional_int)
    tcpFlagsRst = attr.ib(type=Optional[int], converter=_optional_int)
    tcpFlagsSyn = attr.ib(type=Optional[int], converter=_optional_int)
    tcpFlagsUrg = attr.ib(type=Optional[int], converter=_optional_int)

    IP_PROTOCOL_PATTERN = re.compile("^UNNAMED_([0-9]+)$", flags=re.IGNORECASE)

    @classmethod
    def from_dict(cls, json_dict: Dict[str, Any]) -> "Flow":
        return Flow(
            json_dict["dscp"],
            json_dict["dstIp"],
            json_dict.get("dstPort"),
            json_dict["ecn"],
            json_dict["fragmentOffset"],
            json_dict.get("icmpCode"),
            json_dict.get("icmpVar"),
            json_dict.get("ingressInterface"),
            json_dict.get("ingressNode"),
            json_dict.get("ingressVrf"),
            json_dict["ipProtocol"],
            json_dict["packetLength"],
            json_dict["srcIp"],
            json_dict.get("srcPort"),
            json_dict.get("tcpFlagsAck"),
            json_dict.get("tcpFlagsCwr"),
            json_dict.get("tcpFlagsEce"),
            json_dict.get("tcpFlagsFin"),
            json_dict.get("tcpFlagsPsh"),
            json_dict.get("tcpFlagsRst"),
            json_dict.get("tcpFlagsSyn"),
            json_dict.get("tcpFlagsUrg"),
        )

    def __str__(self):
        # type: () -> str
        iface_str = self._iface_str()
        vrf_str = self._vrf_str()
        return (
            "start={node}{iface}{vrf} [{src}->{dst}"
            " {ip_proto}{dscp}{ecn}{offset}{length}{flags}]".format(
                node=self.ingressNode,
                iface=iface_str,
                vrf=vrf_str,
                src=self._ip_port(self.srcIp, self.srcPort),
                dst=self._ip_port(self.dstIp, self.dstPort),
                ip_proto=self.get_ip_protocol_str(),
                dscp=(" dscp={}".format(self.dscp) if self.dscp != 0 else ""),
                ecn=(" ecn={}".format(self.ecn) if self.ecn != 0 else ""),
                offset=(
                    " fragmentOffset={}".format(self.fragmentOffset)
                    if self.fragmentOffset != 0
                    else ""
                ),
                length=(
                    " length={}".format(self.packetLength)
                    if self.packetLength != 0
                    else ""
                ),
                flags=(
                    " tcpFlags={}".format(self.get_flag_str())
                    if self.ipProtocol == 6 and self.get_flag_str() != "00000000"
                    else ""
                ),
            )
        )

    def _vrf_str(self):
        vrf_str = (
            " vrf={}".format(self.ingressVrf)
            if self.ingressVrf not in ["default", None]
            else ""
        )
        return vrf_str

    def _iface_str(self):
        iface_str = (
            " interface={}".format(self.ingressInterface)
            if self.ingressInterface is not None
            else ""
        )
        return iface_str

    def get_flag_str(self):
        # type: () -> str
        return "{}{}{}{}{}{}{}{}".format(
            self.tcpFlagsAck,
            self.tcpFlagsCwr,
            self.tcpFlagsEce,
            self.tcpFlagsFin,
            self.tcpFlagsPsh,
            self.tcpFlagsRst,
            self.tcpFlagsSyn,
            self.tcpFlagsUrg,
        )

    def get_ip_protocol_str(self):
        # type: () -> str
        match = self.IP_PROTOCOL_PATTERN.match(self.ipProtocol)
        if match:
            return "ipProtocol=" + match.group(1)
        else:
            return self.ipProtocol

    def _has_ports(self):
        # type: () -> bool
        return (
            self.ipProtocol in ["TCP", "UDP", "DCCP", "SCTP"]
            and self.srcPort is not None
            and self.dstPort is not None
        )

    def _repr_html_(self):
        # type: () -> str
        return "<br>".join(self._repr_html_lines())

    def _repr_html_lines(self):
        # type: () -> List[str]
        lines = []
        lines.append(
            "Start Location: {node}{iface}{vrf}".format(
                node=self.ingressNode, iface=self._iface_str(), vrf=self._vrf_str()
            )
        )
        lines.append("Src IP: %s" % self.srcIp)
        if self._has_ports():
            assert self.srcPort is not None
            lines.append("Src Port: %d" % self.srcPort)
        lines.append("Dst IP: %s" % self.dstIp)
        if self._has_ports():
            assert self.dstPort is not None
            lines.append("Dst Port: %d" % self.dstPort)
        lines.append("IP Protocol: %s" % self.get_ip_protocol_str())
        return lines

    def _ip_port(self, ip, port):
        # type: (str, Optional[int]) -> str
        if self._has_ports():
            assert port is not None
            return "{ip}:{port}".format(ip=ip, port=port)
        else:
            return ip


@attr.s(frozen=True)
class FlowDiff(DataModelElement):
    """A difference between two Flows.

    :ivar fieldName: A Flow field name that has changed.
    :ivar oldValue: The old value of the field.
    :ivar newValue: The new value of the field.
    """

    fieldName = attr.ib(type=str)
    oldValue = attr.ib(type=str)
    newValue = attr.ib(type=str)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> FlowDiff
        return FlowDiff(
            json_dict["fieldName"], json_dict["oldValue"], json_dict["newValue"]
        )

    def __str__(self):
        # type: () -> str
        return "{fieldName}: {oldValue} -> {newValue}".format(
            fieldName=self.fieldName, oldValue=self.oldValue, newValue=self.newValue
        )


@attr.s(frozen=True)
class FlowTrace(DataModelElement):
    """A trace of a flow through the network.

    A flowTrace is a combination of hops and flow fate (i.e., disposition).

    :ivar disposition: Flow disposition
    :ivar hops: A list of hops (:py:class:`FlowTraceHop`) the flow took
    :ivar notes: Additional notes that help explain the disposition, if applicable.
    """

    disposition = attr.ib(type=str)
    hops = attr.ib(type=Sequence)
    notes = attr.ib(type=Any)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> FlowTrace
        return FlowTrace(
            json_dict["disposition"],
            [FlowTraceHop.from_dict(hop) for hop in json_dict.get("hops", [])],
            json_dict.get("notes"),
        )

    def __str__(self):
        # type: () -> str
        return "{hops}\n{notes}".format(
            hops="\n".join(
                ["{} {}".format(num, hop) for num, hop in enumerate(self.hops, start=1)]
            ),
            notes=self.notes,
        )

    def __len__(self):
        return len(self.hops)

    def __getitem__(self, item):
        return self.hops[item]

    def _repr_html_(self):
        # type: () -> str
        return "{notes}<br>{hops}".format(
            notes=self.format_notes_html(),
            hops="<br><br>".join(
                [
                    "<strong>{num}</strong> {hop}".format(
                        num=num, hop=hop._repr_html_()
                    )
                    for num, hop in enumerate(self.hops, start=1)
                ]
            ),
        )

    def format_notes_html(self):
        # type: () -> str
        return '<span style="color:{color}; text-weight:bold;">{notes}</span>'.format(
            color=_get_color_for_disposition(self.disposition),
            notes=escape_html(self.notes),
        )


@attr.s(frozen=True)
class FlowTraceHop(DataModelElement):
    """A single hop in a flow trace.

    :ivar edge: The :py:class:`~Edge` identifying the hop/link
    :ivar routes: The routes which caused this hop
    :ivar transformedFlow: The transformed version of the flow (if NAT is present)
    """

    edge = attr.ib(type=Edge)
    routes = attr.ib(type=List[Any])
    transformedFlow = attr.ib(type=Optional[Flow])

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> FlowTraceHop
        transformed_flow = json_dict.get("transformedFlow")
        return FlowTraceHop(
            Edge.from_dict(json_dict["edge"]),
            list(json_dict.get("routes", [])),
            Flow.from_dict(transformed_flow) if transformed_flow else None,
        )

    def __str__(self):
        # type: () -> str
        ret_str = "{}\n    Route(s):\n    {}".format(
            self.edge, "\n    ".join(self.routes)
        )
        if self.transformedFlow:
            ret_str += "\n    Transformed flow: {}".format(self.transformedFlow)
        return ret_str

    def _repr_html_(self):
        # type: () -> str
        indent = "&nbsp;" * 4
        result = "{edge}<br>Route(s):<br>{routes}".format(
            edge=self.edge._repr_html_(),
            routes=indent
            + ("<br>" + indent).join([escape_html(r) for r in self.routes]),
        )
        if self.transformedFlow:
            result += "<br>Transformed flow: {}".format(
                self.transformedFlow._repr_html_()
            )
        return result


class SessionAction(DataModelElement):
    """An action that a firewall session takes for return traffic matching the session."""

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> SessionAction
        action = json_dict.get("type")
        if action == "Accept":
            return Accept()
        if action == "FibLookup":
            return FibLookup()
        if action == "ForwardOutInterface":
            return ForwardOutInterface.from_dict(json_dict)
        raise ValueError("Invalid session action type: {}".format(action))


@attr.s(frozen=True)
class Accept(SessionAction):
    """A SessionAction whereby return traffic is accepted by the node from which it
    originated.
    """

    def __str__(self):
        # type: () -> str
        return "Accept"


@attr.s(frozen=True)
class FibLookup(SessionAction):
    """A SessionAction whereby return traffic is forwarded according to the result of a lookup
    on the FIB of the interface on which the return traffic is received.
    """

    def __str__(self):
        # type: () -> str
        return "FibLookup"


@attr.s(frozen=True)
class ForwardOutInterface(SessionAction):
    """A SessionAction whereby a return flow is forwarded out a specified interface to a
    specified next hop with neither FIB resolution nor ARP lookup.

    :ivar nextHopHostname: Hostname of the next hop
    :ivar nextHopInterface: Interface that the next hop receives
    :ivar outgoingInterface: Interface of the outgoing traffic from this hop
    """

    nextHopHostname = attr.ib(type=str)
    nextHopInterface = attr.ib(type=str)
    outgoingInterface = attr.ib(type=str)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> ForwardOutInterface
        next_hop = json_dict.get("nextHop", {})
        return ForwardOutInterface(
            next_hop.get("hostname", ""),
            next_hop.get("interface", ""),
            json_dict.get("outgoingInterface", ""),
        )

    def __str__(self):
        # type: () -> str
        return "ForwardOutInterface(Next Hop: {}, Next Hop Interface: {}, Outgoing Interface: {})".format(
            self.nextHopHostname, self.nextHopInterface, self.outgoingInterface
        )


@attr.s(frozen=True)
class SessionMatchExpr(DataModelElement):
    """
    Represents a match criteria for a firewall session.

    :ivar ipProtocol: IP protocol of the flow
    :ivar srcIp: Source IP of the flow
    :ivar dstIp: Destination IP of the flow
    :ivar srcPort: Source port of the flow
    :ivar dstPort: Destination port of the flow
    """

    ipProtocol = attr.ib(type=str)
    srcIp = attr.ib(type=str)
    dstIp = attr.ib(type=str)
    srcPort = attr.ib(type=Optional[int], default=None)
    dstPort = attr.ib(type=Optional[int], default=None)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> SessionMatchExpr
        return SessionMatchExpr(
            json_dict.get("ipProtocol", ""),
            json_dict.get("srcIp", ""),
            json_dict.get("dstIp", ""),
            json_dict.get("srcPort"),
            json_dict.get("dstPort"),
        )

    def __str__(self):
        # type: () -> str
        matchers = ["ipProtocol", "srcIp", "dstIp"]
        if self.srcPort is not None and self.dstPort is not None:
            matchers.extend(["srcPort", "dstPort"])
        strings = ["{}={}".format(field, getattr(self, field)) for field in matchers]
        return "[{}]".format(", ".join(strings))


@attr.s(frozen=True)
class ArpErrorStepDetail(DataModelElement):
    """Details of a step representing the arp error of a flow when sending out of a Hop.

    :ivar outputInterface: Interface of the Hop from which the flow exits
    :ivar resolvedNexthopIp: Resolve next hop Ip address
    """

    outputInterface = attr.ib(type=Optional[str])
    resolvedNexthopIp = attr.ib(type=Optional[str])

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> ArpErrorStepDetail
        return ArpErrorStepDetail(
            json_dict.get("outputInterface", {}).get("interface"),
            json_dict.get("resolvedNexthopIp"),
        )

    def __str__(self):
        # type: () -> str
        detail_info = []
        if self.outputInterface:
            detail_info.append("Output Interface: {}".format(self.outputInterface))
        if self.resolvedNexthopIp:
            detail_info.append(
                "Resolved Next Hop IP: {}".format(self.resolvedNexthopIp)
            )
        return ", ".join(detail_info)


@attr.s(frozen=True)
class DeliveredStepDetail(DataModelElement):
    """Details of a step representing the flow is delivered or exiting the network.

    :ivar outputInterface: Interface of the Hop from which the flow exits
    :ivar resolvedNexthopIp: Resolve next hop Ip address
    """

    outputInterface = attr.ib(type=Optional[str])
    resolvedNexthopIp = attr.ib(type=Optional[str])

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> DeliveredStepDetail
        return DeliveredStepDetail(
            json_dict.get("outputInterface", {}).get("interface"),
            json_dict.get("resolvedNexthopIp"),
        )

    def __str__(self):
        # type: () -> str
        detail_info = []
        if self.outputInterface:
            detail_info.append("Output Interface: {}".format(self.outputInterface))
        if self.resolvedNexthopIp:
            detail_info.append(
                "Resolved Next Hop IP: {}".format(self.resolvedNexthopIp)
            )
        return ", ".join(detail_info)


@attr.s(frozen=True)
class EnterInputIfaceStepDetail(DataModelElement):
    """Details of a step representing the entering of a flow into a Hop.

    :ivar inputInterface: Interface of the Hop on which this flow enters
    :ivar inputVrf: VRF associated with the input interface
    """

    inputInterface = attr.ib(type=str)
    inputVrf = attr.ib(type=Optional[str])

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> EnterInputIfaceStepDetail
        return EnterInputIfaceStepDetail(
            json_dict.get("inputInterface", {}).get("interface"),
            json_dict.get("inputVrf"),
        )

    def __str__(self):
        # type: () -> str
        str_output = str(self.inputInterface)
        return str_output


@attr.s(frozen=True)
class ExitOutputIfaceStepDetail(DataModelElement):
    """Details of a step representing the exiting of a flow out of a Hop.

    :ivar outputInterface: Interface of the Hop from which the flow exits
    :ivar transformedFlow: Transformed Flow if a source NAT was applied on the Flow
    """

    outputInterface = attr.ib(type=str)
    transformedFlow = attr.ib(type=Optional[str])

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> ExitOutputIfaceStepDetail
        return ExitOutputIfaceStepDetail(
            json_dict.get("outputInterface", {}).get("interface"),
            json_dict.get("transformedFlow"),
        )

    def __str__(self):
        # type: () -> str
        return str(self.outputInterface)


@attr.s(frozen=True)
class InboundStepDetail(DataModelElement):
    """Details of a step representing the receiving (acceptance) of a flow into a Hop.

    :ivar interface: interface that owns the destination IP
    """

    interface = attr.ib(type=str)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> InboundStepDetail
        return InboundStepDetail(json_dict.get("interface", ""))

    def __str__(self):
        return str(self.interface)


@attr.s(frozen=True)
class MatchSessionStepDetail(DataModelElement):
    """Details of a step for when a flow matches a firewall session.

    :ivar incomingInterfaces: List of incoming interfaces the session accepts
    :ivar sessionAction: A SessionAction that the firewall takes for a matching session
    :ivar matchCriteria: A SessionMatchExpr that describes the match criteria of the session
    :ivar transformation: List of FlowDiffs that will be applied after session match
    """

    incomingInterfaces = attr.ib(type=List[str])
    sessionAction = attr.ib(type=SessionAction)
    matchCriteria = attr.ib(type=SessionMatchExpr)
    transformation = attr.ib(type=Optional[List[FlowDiff]], factory=list)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> MatchSessionStepDetail
        return MatchSessionStepDetail(
            json_dict.get("incomingInterfaces", []),
            SessionAction.from_dict(json_dict.get("sessionAction", {})),
            SessionMatchExpr.from_dict(json_dict.get("matchCriteria", {})),
            [FlowDiff.from_dict(diff) for diff in json_dict.get("transformation", [])],
        )

    def __str__(self):
        # type: () -> str
        strings = [
            "Incoming Interfaces: [{}]".format(", ".join(self.incomingInterfaces)),
            "Action: {}".format(self.sessionAction),
            "Match Criteria: {}".format(self.matchCriteria),
        ]
        if self.transformation:
            strings.append(
                "Transformation: [{}]".format(", ".join(map(str, self.transformation)))
            )
        return ", ".join(strings)


@attr.s(frozen=True)
class OriginateStepDetail(DataModelElement):
    """Details of a step representing the originating of a flow in a Hop.

    :ivar originatingVrf: VRF from which the Flow originates
    """

    originatingVrf = attr.ib(type=str)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> OriginateStepDetail
        return OriginateStepDetail(json_dict.get("originatingVrf", ""))

    def __str__(self):
        # type: () -> str
        return str(self.originatingVrf)


@attr.s(frozen=True)
class RoutingStepDetail(DataModelElement):
    """Details of a step representing the routing from input interface to output interface.

    :ivar routes: List of routes which were considered to select the output interface
    """

    routes = attr.ib(type=List[Any])
    arpIp = attr.ib(type=Optional[str])
    outputInterface = attr.ib(type=Optional[str])

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> RoutingStepDetail
        return RoutingStepDetail(
            [route for route in json_dict.get("routes", [])],
            json_dict.get("arpIp"),
            json_dict.get("outputInterface"),
        )

    def __str__(self):
        # type: () -> str
        output = []
        if self.arpIp is not None:
            output.append("ARP IP: " + self.arpIp)
        if self.outputInterface is not None:
            output.append("Output Interface: " + self.outputInterface)
        if self.routes:
            routes_str = []  # type: List[str]
            for route in self.routes:
                routes_str.append(
                    "{protocol} (Network: {network}, Next Hop IP:{next_hop_ip})".format(
                        protocol=route.get("protocol"),
                        network=route.get("network"),
                        next_hop_ip=route.get("nextHopIp"),
                    )
                )
            output.append("Routes: " + "[" + ",".join(routes_str) + "]")
        return ", ".join(output)


@attr.s(frozen=True)
class SetupSessionStepDetail(DataModelElement):
    """Details of a step for when a firewall session is created.

    :ivar incomingInterfaces: List of incoming interfaces the session accepts
    :ivar sessionAction: A SessionAction that the firewall takes for a return traffic matching the session
    :ivar matchCriteria: A SessionMatchExpr that describes the match criteria of the session
    :ivar transformation: List of FlowDiffs that will be applied on the return traffic matching the session
    """

    incomingInterfaces = attr.ib(type=List[str])
    sessionAction = attr.ib(type=SessionAction)
    matchCriteria = attr.ib(type=SessionMatchExpr)
    transformation = attr.ib(type=Optional[List[FlowDiff]], factory=list)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> SetupSessionStepDetail
        return SetupSessionStepDetail(
            json_dict.get("incomingInterfaces", []),
            SessionAction.from_dict(json_dict.get("sessionAction", {})),
            SessionMatchExpr.from_dict(json_dict.get("matchCriteria", {})),
            [FlowDiff.from_dict(diff) for diff in json_dict.get("transformation", [])],
        )

    def __str__(self):
        # type: () -> str
        strings = [
            "Incoming Interfaces: [{}]".format(", ".join(self.incomingInterfaces)),
            "Action: {}".format(self.sessionAction),
            "Match Criteria: {}".format(self.matchCriteria),
        ]
        if self.transformation:
            strings.append(
                "Transformation: [{}]".format(", ".join(map(str, self.transformation)))
            )
        return ", ".join(strings)


@attr.s(frozen=True)
class FilterStepDetail(DataModelElement):
    """Details of a step representing a filter step.

    :ivar filter: filter name
    :ivar type: filter type
    :ivar inputInterface: input interface of the flow
    :ivar flow: current flow
    """

    filter = attr.ib(type=str)
    filterType = attr.ib(type=str)
    inputInterface = attr.ib(type=str)
    flow = attr.ib(type=Optional[Flow])

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> FilterStepDetail
        flowObj = json_dict.get("flow", {})
        return FilterStepDetail(
            json_dict.get("filter", ""),
            json_dict.get("type", ""),
            json_dict.get("inputInterface", ""),
            Flow.from_dict(flowObj) if flowObj else None,
        )

    def __str__(self):
        # type: () -> str
        return "{} ({})".format(self.filter, self.filterType)


@attr.s(frozen=True)
class PolicyStepDetail(DataModelElement):
    """Details of a step representing a generic policy processing step
       (e.g., PBR or equivalent).

    :ivar policy: policy name
    :ivar type: filter type
    """

    policy = attr.ib(type=str)

    @classmethod
    def from_dict(cls, json_dict: Dict[str, Any]) -> "PolicyStepDetail":
        return PolicyStepDetail(json_dict.get("policy", ""))

    def __str__(self) -> str:
        return "{}".format(self.policy)


@attr.s(frozen=True)
class TransformationStepDetail(DataModelElement):
    """Details of a step representation a packet transformation.

    :ivar transformationType: The type of the transformation
    :ivar flowDiffs: Set of changed flow fields
    """

    transformationType = attr.ib(type=str)
    flowDiffs = attr.ib(type=List[FlowDiff])

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> TransformationStepDetail
        return TransformationStepDetail(
            json_dict["transformationType"],
            [FlowDiff.from_dict(fd) for fd in json_dict.get("flowDiffs", [])],
        )

    def __str__(self):
        # type: () -> str
        if not self.flowDiffs:
            return self.transformationType
        return "{type} {diffs}".format(
            type=self.transformationType,
            diffs=", ".join(str(flowDiff) for flowDiff in self.flowDiffs),
        )


@attr.s(frozen=True)
class Step(DataModelElement):
    """Represents a step in a hop.

    :ivar detail: Details about the step
    :ivar action: Action taken in this step
    """

    detail = attr.ib(type=Any)
    action = attr.ib(type=str, converter=str)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> Optional[Step]

        from_dicts = {
            "ArpError": ArpErrorStepDetail.from_dict,
            "Delivered": DeliveredStepDetail.from_dict,
            "EnterInputInterface": EnterInputIfaceStepDetail.from_dict,
            "ExitOutputInterface": ExitOutputIfaceStepDetail.from_dict,
            "Inbound": InboundStepDetail.from_dict,
            "MatchSession": MatchSessionStepDetail.from_dict,
            "Originate": OriginateStepDetail.from_dict,
            "Routing": RoutingStepDetail.from_dict,
            "SetupSession": SetupSessionStepDetail.from_dict,
            "Transformation": TransformationStepDetail.from_dict,
            "Policy": PolicyStepDetail.from_dict,
            "Filter": FilterStepDetail.from_dict,
        }

        action = json_dict.get("action")

        detail = json_dict.get("detail", {})
        type = json_dict.get("type")

        if type not in from_dicts:
            return None
        else:
            return Step(from_dicts[type](detail), action)

    def __str__(self):
        # type: () -> str
        action_str = str(self.action)
        detail_str = str(self.detail) if self.detail else None
        if detail_str:
            return "{}({})".format(action_str, detail_str)
        else:
            return action_str

    def _repr_html_(self):
        # type: () -> str
        return str(self)


@attr.s(frozen=True)
class Hop(DataModelElement):
    """A single hop in a flow trace.

    :ivar node: Name of node considered as the Hop
    :ivar steps: List of steps taken at this Hop
    """

    node = attr.ib(type=str)
    steps = attr.ib(type=List[Step])

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> Hop
        steps = []  # type: List[Step]
        for step in json_dict["steps"]:
            step_obj = Step.from_dict(step)
            if step_obj is not None:
                steps.append(step_obj)
        return Hop(json_dict.get("node", {}).get("name"), steps)

    def __len__(self):
        return len(self.steps)

    def __getitem__(self, item):
        return self.steps[item]

    def __str__(self):
        # type: () -> str
        return "node: {node}\n  {steps}".format(
            node=self.node, steps="\n  ".join(map(str, self.steps))
        )

    def _repr_html_(self):
        # type: () -> str
        return "node: {node}<br>&nbsp;&nbsp;{steps}".format(
            node=self.node,
            steps="<br>&nbsp;&nbsp;".join([step._repr_html_() for step in self.steps]),
        )

    @staticmethod
    def _get_routes_data(routes):
        # type: (List[Dict]) -> List[str]
        routes_str = []  # type: List[str]
        for route in routes:
            routes_str.append(
                "{protocol} [Network: {network}, Next Hop IP:{next_hop_ip}]".format(
                    protocol=route.get("protocol"),
                    network=route.get("network"),
                    next_hop_ip=route.get("nextHopIp"),
                )
            )
        return routes_str


@attr.s(frozen=True)
class Trace(DataModelElement):
    """A trace of a flow through the network.

    A Trace is a combination of hops and flow fate (i.e., disposition).

    :ivar disposition: Flow disposition
    :ivar hops: A list of hops (:py:class:`Hop`) the flow took
    """

    disposition = attr.ib(type=str)
    hops = attr.ib(type=List[Hop])

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> Trace
        return Trace(
            json_dict["disposition"],
            [Hop.from_dict(hop) for hop in json_dict.get("hops", [])],
        )

    def __len__(self):
        return len(self.hops)

    def __getitem__(self, item):
        return self.hops[item]

    def __str__(self):
        # type: () -> str
        return "{disposition}\n{hops}".format(
            disposition=self.disposition,
            hops="\n".join(
                [
                    "{num}. {hop}".format(num=num, hop=hop)
                    for num, hop in enumerate(self.hops, start=1)
                ]
            ),
        )

    def _repr_html_(self):
        # type: () -> str
        disposition_span = '<span style="color:{color}; text-weight:bold;">{disposition}</span>'.format(
            color=_get_color_for_disposition(self.disposition),
            disposition=self.disposition,
        )
        return "{disposition_span}<br>{hops}".format(
            disposition_span=disposition_span,
            hops="<br>".join(
                [
                    "<strong>{num}</strong>. {hop}".format(
                        num=num, hop=hop._repr_html_()
                    )
                    for num, hop in enumerate(self.hops, start=1)
                ]
            ),
        )


@attr.s(frozen=True)
class TcpFlags(DataModelElement):
    """
    Represents a set of TCP flags in a packet.

    :ivar ack:
    :ivar cwr:
    :ivar ece:
    :ivar fin:
    :ivar psh:
    :ivar rst:
    :ivar syn:
    :ivar urg:
    """

    ack = attr.ib(default=False, type=bool)
    cwr = attr.ib(default=False, type=bool)
    ece = attr.ib(default=False, type=bool)
    fin = attr.ib(default=False, type=bool)
    psh = attr.ib(default=False, type=bool)
    rst = attr.ib(default=False, type=bool)
    syn = attr.ib(default=False, type=bool)
    urg = attr.ib(default=False, type=bool)

    @classmethod
    def from_dict(cls, json_dict):
        return TcpFlags(
            ack=json_dict["ack"],
            cwr=json_dict["cwr"],
            ece=json_dict["ece"],
            fin=json_dict["fin"],
            psh=json_dict["psh"],
            rst=json_dict["rst"],
            syn=json_dict["syn"],
            urg=json_dict["urg"],
        )


@attr.s(frozen=True)
class MatchTcpFlags(DataModelElement):
    """
    Match given :py:class:`TcpFlags`.

    For each bit in the TCP flags, a `useX`
    must be set to true, otherwise the bit is treated as "don't care".

    :ivar tcpFlags: tcp flags to match
    :ivar useAck:
    :ivar useCwr:
    :ivar useEce:
    :ivar useFin:
    :ivar usePsh:
    :ivar useRst:
    :ivar useSyn:
    :ivar useUrg:
    """

    tcpFlags = attr.ib(type=TcpFlags)
    useAck = attr.ib(default=True, type=bool)
    useCwr = attr.ib(default=True, type=bool)
    useEce = attr.ib(default=True, type=bool)
    useFin = attr.ib(default=True, type=bool)
    usePsh = attr.ib(default=True, type=bool)
    useRst = attr.ib(default=True, type=bool)
    useSyn = attr.ib(default=True, type=bool)
    useUrg = attr.ib(default=True, type=bool)

    @classmethod
    def from_dict(cls, json_dict):
        return MatchTcpFlags(
            TcpFlags.from_dict(json_dict["tcpFlags"]),
            json_dict["useAck"],
            json_dict["useCwr"],
            json_dict["useEce"],
            json_dict["useFin"],
            json_dict["usePsh"],
            json_dict["useRst"],
            json_dict["useSyn"],
            json_dict["useUrg"],
        )

    @staticmethod
    def match_ack():
        # type: () -> MatchTcpFlags
        """Return match conditions checking that ACK bit is set.

        Other bits may take any value.
        """
        return MatchTcpFlags(TcpFlags(ack=True), useAck=True)

    @staticmethod
    def match_rst():
        # type: () -> MatchTcpFlags
        """Return match conditions checking that RST bit is set.

        Other bits may take any value.
        """
        return MatchTcpFlags(TcpFlags(rst=True), useRst=True)

    @staticmethod
    def match_syn():
        # type: () -> MatchTcpFlags
        """Return match conditions checking that the SYN bit is set.

        Other bits may take any value.
        """
        return MatchTcpFlags(TcpFlags(syn=True), useSyn=True)

    @staticmethod
    def match_synack():
        # type: () -> MatchTcpFlags
        """Return match conditions checking that both the SYN and ACK bits are set.

        Other bits may take any value.
        """
        return MatchTcpFlags(TcpFlags(ack=True, syn=True), useAck=True, useSyn=True)

    @staticmethod
    def match_established():
        # type: () -> List[MatchTcpFlags]
        """Return a list of match conditions matching an established flow (ACK or RST bit set).

        Other bits may take any value.
        """
        return [MatchTcpFlags.match_ack(), MatchTcpFlags.match_rst()]

    @staticmethod
    def match_not_established():
        # type: () -> List[MatchTcpFlags]
        """Return a list of match conditions matching a non-established flow.

        Meaning both ACK and RST bits are unset.
        Other bits may take any value.
        """
        return [
            MatchTcpFlags(
                useAck=True, useRst=True, tcpFlags=TcpFlags(ack=False, rst=False)
            )
        ]


def _get_color_for_disposition(disposition):
    # type: (str) -> str
    success_dispositions = {"ACCEPTED", "DELIVERED_TO_SUBNET", "EXITS_NETWORK"}
    if disposition in success_dispositions:
        return "#019612"
    else:
        return "#7c020e"


def _normalize_phc_intspace(value):
    # type: (Any) -> Optional[Text]
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, int):
        return str(value)
    if isinstance(value, Iterable):
        result = ",".join(str(v) for v in value)
        return result
    raise ValueError("Invalid value {}".format(value))


def _normalize_phc_list(value):
    # type: (Any) -> Optional[List[Text]]
    if value is None or isinstance(value, list):
        return value
    elif isinstance(value, str):
        # only collect truthy values
        alist = [v for v in [v.strip() for v in value.split(",")] if v]
        if not alist:
            # reject empty list values
            raise ValueError("Invalid value {}".format(value))
        return alist
    raise ValueError("Invalid value {}".format(value))


def _normalize_phc_tcpflags(value):
    # type: (Any) -> Optional[List[MatchTcpFlags]]
    if value is None or isinstance(value, list):
        return value
    elif isinstance(value, MatchTcpFlags):
        return [value]
    raise ValueError("Invalid value {}".format(value))


def _normalize_phc_strings(value):
    # type: (Any) -> Optional[Text]
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, Iterable):
        result = ",".join(value)  # type: Text
        return result
    raise ValueError("Invalid value {}".format(value))


@attr.s(frozen=True)
class HeaderConstraints(DataModelElement):
    """Constraints on an IPv4 packet header space.

    Specify constraints on packet headers by specifying lists of allowed values
    in each field of IP packet.

    :ivar srcIps: Source location/IP
    :vartype srcIps: str
    :ivar dstIps: Destination location/IP
    :vartype dstIps: str
    :ivar srcPorts: Source ports as list of ranges (e.g., ``"22,53-99"``)
    :ivar dstPorts: Destination ports as list of ranges, (e.g., ``"22,53-99"``)
    :ivar applications: Shorthands for application protocols (e.g., ``SSH``, ``DNS``, ``SNMP``)
    :ivar ipProtocols: List of well-known IP protocols (e.g., ``TCP``, ``UDP``, ``ICMP``)
    :ivar icmpCodes: List of integer ICMP codes
    :ivar icmpTypes: List of integer ICMP types
    :ivar dscps: List of allowed DSCP value ranges
    :ivar ecns: List of allowed ECN values ranges
    :ivar packetLengths: List of allowed packet length value ranges
    :ivar fragmentOffsets: List of allowed fragmentOffset value ranges
    :ivar tcpFlags: List of :py:class:`MatchTcpFlags` -- conditions on which
        TCP flags to match


    Lists of values in each fields are subject to a logical "OR":

    >>> HeaderConstraints(ipProtocols=["TCP", "UDP"])
    HeaderConstraints(srcIps=None, dstIps=None, srcPorts=None, dstPorts=None, ipProtocols=['TCP', 'UDP'], applications=None,
    icmpCodes=None, icmpTypes=None, ecns=None, dscps=None, packetLengths=None, fragmentOffsets=None, tcpFlags=None)

    means allow TCP OR UDP.

    Different fields are ANDed together:

    >>> HeaderConstraints(srcIps="1.1.1.1", dstIps="2.2.2.2", applications=["SSH"])
    HeaderConstraints(srcIps='1.1.1.1', dstIps='2.2.2.2', srcPorts=None, dstPorts=None, ipProtocols=None, applications=['SSH'],
    icmpCodes=None, icmpTypes=None, ecns=None, dscps=None, packetLengths=None, fragmentOffsets=None, tcpFlags=None)

    means an SSH connection originating at ``1.1.1.1`` and going to ``2.2.2.2``

    Any ``None`` values will be treated as unconstrained.
    """

    # Order params in likelihood of specification
    srcIps = attr.ib(default=None, type=Optional[str])
    dstIps = attr.ib(default=None, type=Optional[str])
    srcPorts = attr.ib(
        default=None, type=Optional[str], converter=_normalize_phc_intspace
    )
    dstPorts = attr.ib(
        default=None, type=Optional[str], converter=_normalize_phc_intspace
    )
    ipProtocols = attr.ib(
        default=None, type=Optional[List[str]], converter=_normalize_phc_list
    )
    applications = attr.ib(
        default=None, type=Optional[List[str]], converter=_normalize_phc_list
    )
    icmpCodes = attr.ib(
        default=None, type=Optional[str], converter=_normalize_phc_intspace
    )
    icmpTypes = attr.ib(
        default=None, type=Optional[str], converter=_normalize_phc_intspace
    )
    ecns = attr.ib(default=None, type=Optional[str], converter=_normalize_phc_intspace)
    dscps = attr.ib(default=None, type=Optional[str], converter=_normalize_phc_intspace)
    packetLengths = attr.ib(
        default=None, type=Optional[str], converter=_normalize_phc_intspace
    )
    fragmentOffsets = attr.ib(
        default=None, type=Optional[str], converter=_normalize_phc_intspace
    )
    tcpFlags = attr.ib(
        default=None, type=Optional[MatchTcpFlags], converter=_normalize_phc_tcpflags
    )

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
            ecns=json_dict.get("ecns"),
            dscps=json_dict.get("dscps"),
            packetLengths=json_dict.get("packetLengths"),
            fragmentOffsets=json_dict.get("fragmentOffsets"),
        )

    @classmethod
    def of(cls, flow):
        # type: (Flow) -> HeaderConstraints
        """Create header constraints from an existing flow."""
        srcPorts = dstPorts = icmpCodes = icmpTypes = tcpFlags = None
        if flow._has_ports():
            srcPorts = str(flow.srcPort)
            dstPorts = str(flow.dstPort)
        if flow.ipProtocol.lower() == "icmp":
            icmpCodes = flow.icmpCode
            icmpTypes = flow.icmpVar
        if flow.ipProtocol.lower() == "tcp":
            tcpFlags = MatchTcpFlags(
                tcpFlags=TcpFlags(
                    bool(flow.tcpFlagsAck),
                    bool(flow.tcpFlagsCwr),
                    bool(flow.tcpFlagsEce),
                    bool(flow.tcpFlagsFin),
                    bool(flow.tcpFlagsPsh),
                    bool(flow.tcpFlagsRst),
                    bool(flow.tcpFlagsSyn),
                    bool(flow.tcpFlagsUrg),
                )
            )
        return HeaderConstraints(
            srcIps=flow.srcIp,
            dstIps=flow.dstIp,
            ipProtocols=[str(flow.ipProtocol)],
            srcPorts=srcPorts,
            dstPorts=dstPorts,
            icmpCodes=icmpCodes,
            icmpTypes=icmpTypes,
            tcpFlags=tcpFlags,
            fragmentOffsets=flow.fragmentOffset,
            packetLengths=flow.packetLength,
        )


@attr.s(frozen=True)
class PathConstraints(DataModelElement):
    """
    Constraints on the path of a flow.

    :ivar startLocation: Location description of where a flow is allowed to start
    :ivar endLocation: Location description of where a flow is allowed to terminate
    :ivar transitLocations: Location description of where a flow must transit
    :ivar forbiddenLocations: Location description of where a flow is *not* allowed to transit
    """

    startLocation = attr.ib(default=None, type=Optional[str])
    endLocation = attr.ib(default=None, type=Optional[str])
    transitLocations = attr.ib(default=None, type=Optional[str])
    forbiddenLocations = attr.ib(default=None, type=Optional[str])

    @classmethod
    def from_dict(cls, json_dict):
        return PathConstraints(
            startLocation=json_dict.get("startLocation"),
            endLocation=json_dict.get("endLocation"),
            transitLocations=json_dict.get("transitLocations"),
            forbiddenLocations=json_dict.get("forbiddenLocations"),
        )
