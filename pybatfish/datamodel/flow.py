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
from typing import Any, Dict, Iterable, List, Optional, Text  # noqa: F401

import attr
import six

from pybatfish.util import escape_html
from .primitives import DataModelElement, Edge

__all__ = [
    'EnterInputIfaceStepDetail',
    'ExitOutputIfaceStepDetail',
    'FilterStepDetail',
    'Flow',
    'FlowTrace',
    'FlowTraceHop',
    'HeaderConstraints',
    'Hop',
    'InboundStepDetail',
    'MatchSessionStepDetail',
    'MatchTcpFlags',
    'OriginateStepDetail',
    'RoutingStepDetail',
    'SetupSessionStepDetail',
    'PathConstraints',
    'TcpFlags',
    'Trace',
    'TransformationStepDetail'
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
    state = attr.ib(type=str, converter=str)
    tag = attr.ib(type=str, converter=str)
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
    def from_dict(cls, json_dict):
        # type: (Dict) -> Flow
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
            json_dict["state"],
            json_dict["tag"],
            json_dict.get("tcpFlagsAck"),
            json_dict.get("tcpFlagsCwr"),
            json_dict.get("tcpFlagsEce"),
            json_dict.get("tcpFlagsFin"),
            json_dict.get("tcpFlagsPsh"),
            json_dict.get("tcpFlagsRst"),
            json_dict.get("tcpFlagsSyn"),
            json_dict.get("tcpFlagsUrg"))

    def __str__(self):
        # type: () -> str
        # exclude the tag field
        iface_str = self._iface_str()
        vrf_str = self._vrf_str()
        return \
            "start={node}{iface}{vrf} [{src}->{dst}" \
            " {ip_proto}{dscp}{ecn}{offset}{length}{state}{flags}]".format(
                node=self.ingressNode,
                iface=iface_str,
                vrf=vrf_str,
                src=self._ip_port(self.srcIp, self.srcPort),
                dst=self._ip_port(self.dstIp, self.dstPort),
                ip_proto=self.get_ip_protocol_str(),
                dscp=(" dscp={}".format(self.dscp) if self.dscp != 0 else ""),
                ecn=(" ecn={}".format(self.ecn) if self.ecn != 0 else ""),
                offset=(" fragmentOffset={}".format(self.fragmentOffset)
                        if self.fragmentOffset != 0 else ""),
                length=(" length={}".format(self.packetLength)
                        if self.packetLength != 0 else ""),
                state=(" state={}".format(self.state)
                       if self.state != "NEW" else ""),
                flags=(" tcpFlags={}".format(self.get_flag_str()) if
                       self.ipProtocol == 6 and
                       self.get_flag_str() != "00000000" else ""))

    def _vrf_str(self):
        vrf_str = " vrf={}".format(self.ingressVrf) \
            if self.ingressVrf not in ["default", None] else ""
        return vrf_str

    def _iface_str(self):
        iface_str = " interface={}".format(self.ingressInterface) \
            if self.ingressInterface is not None else ""
        return iface_str

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

    def get_ip_protocol_str(self):
        # type: () -> str
        match = self.IP_PROTOCOL_PATTERN.match(self.ipProtocol)
        if match:
            return "ipProtocol=" + match.group(1)
        else:
            return self.ipProtocol

    def _has_ports(self):
        # type: () -> bool
        return (self.ipProtocol in ['TCP', 'UDP', 'DCCP', 'SCTP']
                and self.srcPort is not None
                and self.dstPort is not None)

    def _repr_html_(self):
        # type: () -> str
        return '<br>'.join(self._repr_html_lines())

    def _repr_html_lines(self):
        # type: () -> List[str]
        lines = []
        lines.append('Start Location: {node}{iface}{vrf}'.format(
            node=self.ingressNode,
            iface=self._iface_str(),
            vrf=self._vrf_str()))
        lines.append('Src IP: %s' % self.srcIp)
        if self._has_ports():
            assert self.srcPort is not None
            lines.append('Src Port: %d' % self.srcPort)
        lines.append('Dst IP: %s' % self.dstIp)
        if self._has_ports():
            assert self.dstPort is not None
            lines.append('Dst Port: %d' % self.dstPort)
        lines.append('IP Protocol: %s' % self.get_ip_protocol_str())
        if self.state != "NEW":
            lines.append('Firewall Classification: %s' % self.state)
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
        return FlowDiff(json_dict["fieldName"],
                        json_dict["oldValue"],
                        json_dict["newValue"])

    def __str__(self):
        # type: () -> str
        return "{fieldName}: {oldValue} -> {newValue}".format(
            fieldName=self.fieldName,
            oldValue=self.oldValue,
            newValue=self.newValue)


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

    def __len__(self):
        return len(self.hops)

    def __getitem__(self, item):
        return self.hops[item]

    def _repr_html_(self):
        # type: () -> str
        return "{notes}<br>{hops}".format(
            notes=self.format_notes_html(),
            hops="<br><br>".join(
                ["<strong>{num}</strong> {hop}".format(num=num,
                                                       hop=hop._repr_html_())
                 for num, hop in enumerate(self.hops, start=1)]))

    def format_notes_html(self):
        # type: () -> str
        return '<span style="color:{color}; text-weight:bold;">{notes}</span>'.format(
            color=_get_color_for_disposition(self.disposition),
            notes=escape_html(self.notes))


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

    def _repr_html_(self):
        # type: () -> str
        indent = "&nbsp;" * 4
        result = "{edge}<br>Route(s):<br>{routes}".format(
            edge=self.edge._repr_html_(),
            routes=indent + ("<br>" + indent).join(
                [escape_html(r) for r in self.routes]))
        if self.transformedFlow:
            result += "<br>Transformed flow: {}".format(
                self.transformedFlow._repr_html_())
        return result


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
            json_dict.get("inputVrf"))

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
            json_dict.get("transformedFlow"))

    def __str__(self):
        # type: () -> str
        return str(self.outputInterface)


@attr.s(frozen=True)
class InboundStepDetail(DataModelElement):
    """Details of a step representing the receiving (acceptance) of a flow into a Hop."""

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> InboundStepDetail
        return InboundStepDetail()  # Currently has no attributes

    def __str__(self):
        return "InboundStep"


@attr.s(frozen=True)
class MatchSessionStepDetail(DataModelElement):
    """Details of a step for when a flow matches a firewall session."""

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> MatchSessionStepDetail
        return MatchSessionStepDetail()

    def __str__(self):
        # type: () -> str
        return ""


@attr.s(frozen=True)
class OriginateStepDetail(DataModelElement):
    """Details of a step representing the originating of a flow in a Hop.

    :ivar originatingVrf: VRF from which the Flow originates
    """

    originatingVrf = attr.ib(type=str)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> OriginateStepDetail
        return OriginateStepDetail(
            json_dict.get("originatingVrf", ""))

    def __str__(self):
        # type: () -> str
        return str(self.originatingVrf)


@attr.s(frozen=True)
class RoutingStepDetail(DataModelElement):
    """Details of a step representing the routing from input interface to output interface.

    :ivar routes: List of routes which were considered to select the output interface
    """

    routes = attr.ib(type=List[Any])

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> RoutingStepDetail
        return RoutingStepDetail(
            [route for route in json_dict.get("routes", [])])

    def __str__(self):
        # type: () -> str
        if not self.routes:
            return ""

        routes_str = []  # type: List[str]
        for route in self.routes:
            routes_str.append(
                "{protocol} [Network: {network}, Next Hop IP:{next_hop_ip}]".format(
                    protocol=route.get("protocol"),
                    network=route.get("network"),
                    next_hop_ip=route.get("nextHopIp")))
        return "Routes: " + ",".join(routes_str)


@attr.s(frozen=True)
class SetupSessionStepDetail(DataModelElement):
    """Details of a step for when a firewall session is created."""

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> SetupSessionStepDetail
        return SetupSessionStepDetail()

    def __str__(self):
        # type: () -> str
        return ""


@attr.s(frozen=True)
class FilterStepDetail(DataModelElement):
    """Details of a step representing a filter step.

    :ivar filter: filter name
    :ivar type: filter type
    """

    filter = attr.ib(type=str)
    filterType = attr.ib(type=str)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> FilterStepDetail
        return FilterStepDetail(json_dict.get("filter", ""), json_dict.get("type", ""))

    def __str__(self):
        # type: () -> str
        return "{} ({})".format(self.filter, self.filterType)


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
            [FlowDiff.from_dict(fd) for fd in json_dict.get("flowDiffs", [])])

    def __str__(self):
        # type: () -> str
        if not self.flowDiffs:
            return self.transformationType
        return "{type} {diffs}".format(
            type=self.transformationType,
            diffs=', '.join(str(flowDiff) for flowDiff in self.flowDiffs))


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
            "EnterInputInterface": EnterInputIfaceStepDetail.from_dict,
            "ExitOutputInterface": ExitOutputIfaceStepDetail.from_dict,
            "Inbound": InboundStepDetail.from_dict,
            "MatchSession": MatchSessionStepDetail.from_dict,
            "Originate": OriginateStepDetail.from_dict,
            "Routing": RoutingStepDetail.from_dict,
            "SetupSession": SetupSessionStepDetail.from_dict,
            "Transformation": TransformationStepDetail.from_dict,
            "Filter": FilterStepDetail.from_dict
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
        return Hop(json_dict.get('node', {}).get('name'), steps)

    def __len__(self):
        return len(self.steps)

    def __getitem__(self, item):
        return self.steps[item]

    def __str__(self):
        # type: () -> str
        return "node: {node}\n  {steps}".format(
            node=self.node,
            steps="\n  ".join(map(str, self.steps)))

    def _repr_html_(self):
        # type: () -> str
        return "node: {node}<br>&nbsp;&nbsp;{steps}".format(
            node=self.node,
            steps="<br>&nbsp;&nbsp;".join(
                [step._repr_html_() for step in self.steps]))

    @staticmethod
    def _get_routes_data(routes):
        # type: (List[Dict]) -> List[str]
        routes_str = []  # type: List[str]
        for route in routes:
            routes_str.append(
                "{protocol} [Network: {network}, Next Hop IP:{next_hop_ip}]".format(
                    protocol=route.get("protocol"),
                    network=route.get("network"),
                    next_hop_ip=route.get("nextHopIp")))
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
        return Trace(json_dict["disposition"],
                     [Hop.from_dict(hop) for hop in json_dict.get("hops", [])])

    def __len__(self):
        return len(self.hops)

    def __getitem__(self, item):
        return self.hops[item]

    def __str__(self):
        # type: () -> str
        return "{disposition}\n{hops}".format(
            disposition=self.disposition,
            hops="\n".join(
                ["{num}. {hop}".format(num=num, hop=hop) for num, hop in
                 enumerate(self.hops, start=1)]))

    def _repr_html_(self):
        # type: () -> str
        disposition_span = '<span style="color:{color}; text-weight:bold;">{disposition}</span>'.format(
            color=_get_color_for_disposition(self.disposition),
            disposition=self.disposition)
        return "{disposition_span}<br>{hops}".format(
            disposition_span=disposition_span,
            hops="<br>".join(
                ["<strong>{num}</strong>. {hop}".format(num=num,
                                                        hop=hop._repr_html_())
                 for num, hop in enumerate(self.hops, start=1)]))


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
            ack=json_dict['ack'],
            cwr=json_dict['cwr'],
            ece=json_dict['ece'],
            fin=json_dict['fin'],
            psh=json_dict['psh'],
            rst=json_dict['rst'],
            syn=json_dict['syn'],
            urg=json_dict['urg'])


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
            TcpFlags.from_dict(json_dict['tcpFlags']),
            json_dict['useAck'],
            json_dict['useCwr'],
            json_dict['useEce'],
            json_dict['useFin'],
            json_dict['usePsh'],
            json_dict['useRst'],
            json_dict['useSyn'],
            json_dict['useUrg'])

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
        return MatchTcpFlags(
            TcpFlags(ack=True, syn=True), useAck=True, useSyn=True)

    @staticmethod
    def match_established():
        # type: () -> List[MatchTcpFlags]
        """Return a list of match conditions matching an established flow (ACK or RST bit set).

        Other bits may take any value.
        """
        return [MatchTcpFlags.match_ack(), MatchTcpFlags.match_rst()]


def _get_color_for_disposition(disposition):
    # type: (str) -> str
    success_dispositions = {"ACCEPTED", "DELIVERED_TO_SUBNET", "EXITS_NETWORK"}
    if disposition in success_dispositions:
        return "#019612"
    else:
        return "#7c020e"


def _normalize_phc_intspace(value):
    # type: (Any) -> Optional[Text]
    if value is None or isinstance(value, six.string_types):
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
    elif isinstance(value, six.string_types):
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
    if value is None or isinstance(value, six.string_types):
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
    :ivar firewallClassifications: List of flow states as classified by a stateful firewall (e.g., "new", "established")
    :ivar dscps: List of allowed DSCP value ranges
    :ivar ecns: List of allowed ECN values ranges
    :ivar packetLengths: List of allowed packet length value ranges
    :ivar fragmentOffsets: List of allowed fragmentOffset value ranges
    :ivar tcpFlags: List of :py:class:`MatchTcpFlags` -- conditions on which
        TCP flags to match


    Lists of values in each fields are subject to a logical "OR":

    >>> HeaderConstraints(ipProtocols=["TCP", "UDP"])
    HeaderConstraints(srcIps=None, dstIps=None, srcPorts=None, dstPorts=None, ipProtocols=['TCP', 'UDP'], applications=None,
    icmpCodes=None, icmpTypes=None, firewallClassifications=None, ecns=None, dscps=None, packetLengths=None, fragmentOffsets=None, tcpFlags=None)

    means allow TCP OR UDP.

    Different fields are ANDed together:

    >>> HeaderConstraints(srcIps="1.1.1.1", dstIps="2.2.2.2", applications=["SSH"])
    HeaderConstraints(srcIps='1.1.1.1', dstIps='2.2.2.2', srcPorts=None, dstPorts=None, ipProtocols=None, applications=['SSH'],
    icmpCodes=None, icmpTypes=None, firewallClassifications=None, ecns=None, dscps=None, packetLengths=None, fragmentOffsets=None, tcpFlags=None)

    means an SSH connection originating at ``1.1.1.1`` and going to ``2.2.2.2``

    Any ``None`` values will be treated as unconstrained.
    """

    # Order params in likelihood of specification
    srcIps = attr.ib(default=None, type=Optional[str])
    dstIps = attr.ib(default=None, type=Optional[str])
    srcPorts = attr.ib(default=None, type=Optional[str],
                       converter=_normalize_phc_intspace)
    dstPorts = attr.ib(default=None, type=Optional[str],
                       converter=_normalize_phc_intspace)
    ipProtocols = attr.ib(default=None, type=Optional[List[str]],
                          converter=_normalize_phc_list)
    applications = attr.ib(default=None, type=Optional[List[str]],
                           converter=_normalize_phc_list)
    icmpCodes = attr.ib(default=None, type=Optional[str],
                        converter=_normalize_phc_intspace)
    icmpTypes = attr.ib(default=None, type=Optional[str],
                        converter=_normalize_phc_intspace)
    firewallClassifications = attr.ib(default=None, type=Optional[List[str]],
                                      converter=_normalize_phc_list)
    ecns = attr.ib(default=None, type=Optional[str],
                   converter=_normalize_phc_intspace)
    dscps = attr.ib(default=None, type=Optional[str],
                    converter=_normalize_phc_intspace)
    packetLengths = attr.ib(default=None, type=Optional[str],
                            converter=_normalize_phc_intspace)
    fragmentOffsets = attr.ib(default=None, type=Optional[str],
                              converter=_normalize_phc_intspace)
    tcpFlags = attr.ib(default=None, type=Optional[MatchTcpFlags],
                       converter=_normalize_phc_tcpflags)

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
            firewallClassifications=json_dict.get("flowStates"),
            ecns=json_dict.get("ecns"),
            dscps=json_dict.get("dscps"),
            packetLengths=json_dict.get("packetLengths"),
            fragmentOffsets=json_dict.get("fragmentOffsets"))

    def dict(self):
        d = super(HeaderConstraints, self).dict()
        # Rename firewallClassifications to flowStates (expected on the backend)
        d['flowStates'] = d['firewallClassifications']
        del d['firewallClassifications']
        return d


@attr.s(frozen=True)
class PathConstraints(DataModelElement):
    """
    Constraints on the path of a flow.

    :ivar startLocation: Location description of where a flow is allowed to start
    :ivar endLocation: Location description of where a flow is allowed to terminate
    :ivar transitLocation: Location description of where a flow must transit
    :ivar startLocation: Location description of where a flow is *not* allowed to transit
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
            forbiddenLocations=json_dict.get("forbiddenLocations"))
