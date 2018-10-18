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
    'Flow',
    'FlowTrace',
    'FlowTraceHop',
    'HeaderConstraints',
    'Hop',
    'MatchTcpFlags',
    'PathConstraints',
    'TcpFlags',
    'Trace'
]


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

    IP_PROTOCOL_PATTERN = re.compile("^UNNAMED_([0-9]+)$", flags=re.IGNORECASE)

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
        iface_str = self._iface_str()
        vrf_str = self._vrf_str()
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

    def _repr_html_(self):
        # type: () -> str
        return "{src_ip}:{src_port} &rarr; {dst_ip}:{dst_port}<br>start={node}{iface}{vrf}" \
            .format(node=self.ingressNode,
                    iface=escape_html(self._iface_str()),
                    vrf=escape_html(self._vrf_str()),
                    src_ip=self.srcIp,
                    src_port=self.srcPort,
                    dst_ip=self.dstIp,
                    dst_port=self.dstPort,
                    ip_proto=self.get_ip_protocol_str())


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
        color = '#019612' if 'ACCEPTED' in self.notes else '#7c020e'
        return '<span style="color:{color}; text-weight:bold;">{notes}</span>'.format(
            color=color, notes=escape_html(self.notes))


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
class Hop(DataModelElement):
    """A single hop in a flow trace.

    :ivar node: Name of node considered as the Hop
    :ivar steps: List of steps taken at this Hop
    """

    node = attr.ib(type=str)
    steps = attr.ib(type=List[Any])

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> Hop
        return Hop(json_dict.get('node', {}).get('name'), json_dict["steps"])

    def __len__(self):
        return len(self.steps)

    def __getitem__(self, item):
        return self.steps[item]

    def final_detail(self):
        # type: () -> Any
        if not self.steps:
            return None
        return self.steps[-1].get('detail')

    def __str__(self):
        # type: () -> str
        return "node: {node}\n steps: {steps}".format(
            node=self.node,
            steps=" -> ".join(map(Hop._get_step_data_, self.steps)))

    def _repr_html_(self):
        # type: () -> str
        # indent = "&nbsp;" * 4
        return "node: {node}<br>steps: {steps}".format(
            node=self.node,
            steps=" -> ".join(map(Hop._get_step_data_, self.steps)))

    @staticmethod
    def _get_step_data_(step):
        # type: (Dict) -> str
        return "{type}({action})".format(type=step.get("type"),
                                         action=step.get("action"))


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

    def final_detail(self):
        # type: () -> Any
        if not self.hops:
            return None
        return self.hops[-1].final_detail()

    def __str__(self):
        # type: () -> str
        return "{disposition}\n{hops}".format(
            disposition=self.disposition,
            hops="\n".join(["{num}. {hop}".format(num=num, hop=hop) for num, hop in
                            enumerate(self.hops, start=1)]))

    def _repr_html_(self):
        # type: () -> str
        return "{disposition}<br>{hops}".format(
            disposition=self.disposition,
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
    :ivar flowStates: List of flow states (e.g., "new", "established")
    :ivar dscps: List of allowed DSCP value ranges
    :ivar ecns: List of allowed ECN values ranges
    :ivar packetLengths: List of allowed packet length value ranges
    :ivar fragmentOffsets: List of allowed fragmentOffset value ranges
    :ivar tcpFlags: List of :py:class:`MatchTcpFlags` -- conditions on which
        TCP flags to match


    Lists of values in each fields are subject to a logical "OR":

    >>> HeaderConstraints(ipProtocols=["TCP", "UDP"])
    HeaderConstraints(srcIps=None, dstIps=None, srcPorts=None, dstPorts=None, ipProtocols=['TCP', 'UDP'], applications=None,
    icmpCodes=None, icmpTypes=None, flowStates=None, ecns=None, dscps=None, packetLengths=None, fragmentOffsets=None, tcpFlags=None)

    means allow TCP OR UDP.

    Different fields are ANDed together:

    >>> HeaderConstraints(srcIps="1.1.1.1", dstIps="2.2.2.2", applications=["SSH"])
    HeaderConstraints(srcIps='1.1.1.1', dstIps='2.2.2.2', srcPorts=None, dstPorts=None, ipProtocols=None, applications=['SSH'],
    icmpCodes=None, icmpTypes=None, flowStates=None, ecns=None, dscps=None, packetLengths=None, fragmentOffsets=None, tcpFlags=None)

    means an SSH connection originating at ``1.1.1.1`` and going to ``2.2.2.2``

    Any ``None`` values will be treated as unconstrained.
    """

    # Order params in likelihood of specification
    srcIps = attr.ib(default=None, type=Optional[str])
    dstIps = attr.ib(default=None, type=Optional[str])
    srcPorts = attr.ib(default=None, type=Optional[str],
                       converter=_normalize_phc_strings)
    dstPorts = attr.ib(default=None, type=Optional[str],
                       converter=_normalize_phc_strings)
    ipProtocols = attr.ib(default=None, type=Optional[List[str]])
    applications = attr.ib(default=None, type=Optional[List[str]])
    icmpCodes = attr.ib(default=None, type=Optional[str],
                        converter=_normalize_phc_strings)
    icmpTypes = attr.ib(default=None, type=Optional[str],
                        converter=_normalize_phc_strings)
    flowStates = attr.ib(default=None, type=Optional[List[str]])
    ecns = attr.ib(default=None, type=Optional[str],
                   converter=_normalize_phc_strings)
    dscps = attr.ib(default=None, type=Optional[str],
                    converter=_normalize_phc_strings)
    packetLengths = attr.ib(default=None, type=Optional[str],
                            converter=_normalize_phc_strings)
    fragmentOffsets = attr.ib(default=None, type=Optional[str],
                              converter=_normalize_phc_strings)
    tcpFlags = attr.ib(default=None, type=Optional[MatchTcpFlags])

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
