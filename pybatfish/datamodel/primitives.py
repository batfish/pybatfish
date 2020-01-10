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
from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Any, Dict, List  # noqa: F401

import attr
from pandas.core.indexes.frozen import FrozenList

from pybatfish.util import escape_html, escape_name, get_html

__all__ = [
    "Assertion",
    "AssertionType",
    "VariableType",
    "AutoCompleteSuggestion",
    "Edge",
    "FileLines",
    "Interface",
    "Issue",
    "IssueType",
    "ListWrapper",
]


@attr.s
class DataModelElement(object):
    __metaclass__ = ABCMeta

    def dict(self):
        # type: () -> Dict[str, Any]
        return attr.asdict(self, recurse=True)

    @classmethod
    @abstractmethod
    def from_dict(cls, json_dict):
        raise NotImplementedError("Datamodel elements must implement from_dict")

    def _repr_html_(self):
        # type: () -> str
        """Override this method to enable custom HTML formatting of the dataclass."""
        return escape_html(repr(self))


class AssertionType(str, Enum):
    """Assertion type."""

    COUNT_EQUALS = "countequals"  #: Number of results equals
    COUNT_LESSTHAN = "countlessthan"  #: Number of results is less than
    COUNT_MORETHAN = "countmorethan"  #: Number of results is more than
    EQUALS = "equals"  #: Result equals to value (list of rows). **Experimental**


@attr.s(frozen=True)
class Assertion(DataModelElement):
    """A Batfish assertion.

    Assertions are combined with a :py:class:`~pybatfish.question.question.Question`
    to create a Batfish check. An assertion can be on the number of results
    return by the question, or on the value of the answer itself.

    :ivar type: an :py:class:`AssertionType`
    :ivar expect: the expected value (a.k.a as right-hand side)
        for the assertion to return True.
    """

    type = attr.ib(type=AssertionType)
    expect = attr.ib(type=Any)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> Assertion
        return Assertion(AssertionType[json_dict["type"]], json_dict["expect"])

    def dict(self):
        return dict(type=self.type.value, expect=self.expect)


class VariableType(str, Enum):
    """Auto completion type."""

    # Should be in sync with org.batfish.datamodel.questions.Variable.Type

    ADDRESS_GROUP_NAME = "addressGroupName"  #: address group name
    ANSWER_ELEMENT = "answerElement"  #: answer elements
    APPLICATION_SPEC = "applicationSpec"  #: application specifier
    BGP_PEER_PROPERTY_SPEC = "bgpPeerPropertySpec"  #: bgp peer properties
    BGP_PROCESS_PROPERTY_SPEC = "bgpProcessPropertySpec"  #: bgp process properties
    BGP_ROUTES = "bgpRoutes"  #: bgp routes
    BGP_SESSION_COMPAT_STATUS_SPEC = (
        "bgpSessionCompatStatusSpec"  #: bgp session compatibility statuses
    )
    BGP_SESSION_STATUS_SPEC = "bgpSessionStatusSpec"  #: bgp session statuses
    BGP_SESSION_TYPE_SPEC = "bgpSessionTypeSpec"  #: bgp session types
    BOOLEAN = "boolean"  #: boolean values
    COMPARATOR = "comparator"  #: comparators (<, <=, ==, >=, >, !=)
    DOUBLE = "double"  #: double values
    DISPOSITION_SPEC = "dispositionSpec"  #: dispositions
    FILTER = "filter"  #: names or regex of filters
    FILTER_NAME = "filter"  #: name of filters
    FILTER_SPEC = "filterSpec"  #: filter specifier
    FLOAT = "float"  #: float values
    HEADER_CONSTRAINT = "headerConstraint"  #: packet header constraints
    INTEGER = "integer"  #: integer values
    INTEGER_SPACE = "integerSpace"  #: integer spaces
    INTERFACE = "interface"  #: names of interfaces
    INTERFACE_GROUP_NAME = "interfaceGroupName"  #: interface group name
    INTERFACE_NAME = "interfaceName"  #: name of interfaces
    INTERFACE_PROPERTY_SPEC = "interfacePropertySpec"  #: interface properties
    INTERFACES_SPEC = "interfacesSpec"  #: interfaces specifier
    IP = "ip"  #: ips
    IP_PROTOCOL = "ipProtocol"  #: ip protocols
    IP_PROTOCOL_SPEC = "ipProtocolSpec"  #: ip protocol specifier
    IP_SPACE_SPEC = "ipSpaceSpec"  #: ip space specifier
    IP_WILDCARD = "ipWildcard"  #: ip protocols
    IPSEC_SESSION_STATUS_SPEC = "ipsecSessionStatusSpec"  #: ipsec session statuses
    JAVA_REGEX = "javaRegex"  #: java regex
    JSON_PATH = "jsonPath"  #: json path
    JSON_PATH_REGEX = "jsonPathRegex"  #: json path regex
    LOCATION_SPEC = "locationSpec"  #: location specifier
    LONG = "long"  #: long values
    MLAG_ID = "mlagId"  #: mlag id
    MLAG_ID_SPEC = "mlagIdSpec"  #: mlag id specifier
    NAMED_STRUCTURE_SPEC = "namedStructureSpec"  #: named structure type
    NODE_NAME = "nodeName"  #: name of nodes
    NODE_PROPERTY_SPEC = "nodePropertySpec"  #: node properties
    NODE_ROLE_DIMENSION_NAME = "nodeRoleDimensionName"  #: names of node role dimension
    NODE_ROLE_NAME = "nodeRoleName"  #: node role name
    NODE_SPEC = "nodeSpec"  #: node specifier
    OSPF_INTERFACE_PROPERTY_SPEC = (
        "ospfInterfacePropertySpec"  #: ospf interface properties
    )
    OSPF_PROCESS_PROPERTY_SPEC = "ospfProcessPropertySpec"  #: ospf process properties
    OSPF_SESSION_STATUS_SPEC = "ospfSessionStatusSpec"  #: ospf session statuses
    PATH_CONSTRAINT = "pathConstraint"  #: path constraints
    PREFIX = "prefix"  #: prefixes
    PREFIX_RANGE = "prefixRange"  #: prefix ranges
    PROTOCOL = "protocol"  #: application-level protocols
    REFERENCE_BOOK_NAME = "referenceBookName"  #: reference book name
    QUESTION = "question"  #: questions
    ROUTING_PROTOCOL_SPEC = "routingProtocolSpec"  #: routing protocols
    STRING = "string"  #: string values
    STRUCTURE_NAME = "structureName"  #: names of structures
    SUBRANGE = "subrange"  #: subranges
    VRF = "vrf"  #: names of vrfs
    VXLAN_VNI_PROPERTY_SPEC = "vxlanVniPropertySpec"  #: vxlan vni properties
    ZONE = "zone"  #: names of zones


@attr.s(frozen=True)
class AutoCompleteSuggestion(DataModelElement):
    """Represent one auto complete suggestion.

    Auto complete suggestions are returned by Batfish for auto complete queries.

    :ivar description: A description of the suggestion (optional)
    :ivar insertion_index: Index in original input string where suggested text should be inserted
    :ivar is_partial: Whether this suggestion represents partial or full text
    :ivar rank: Batfish may assign a rank to the suggestion
    :ivar text: The actual suggested text
    """

    description = attr.ib(type=str)
    insertion_index = attr.ib(type=int)
    is_partial = attr.ib(type=bool)
    rank = attr.ib(type=int)
    text = attr.ib(type=str)

    DEFAULT_RANK = 0x7FFFFFFF

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> AutoCompleteSuggestion
        return AutoCompleteSuggestion(
            json_dict.get("description", None),
            json_dict.get("insertionIndex", 0),
            json_dict["isPartial"],
            json_dict["rank"],
            json_dict["text"],
        )

    def dict(self):
        return dict(
            description=self.description,
            insertion_index=self.insertion_index,
            is_partial=self.is_partial,
            rank=self.rank,
            text=self.text,
        )


@attr.s(frozen=True)
class Interface(DataModelElement):
    """A network interface --- a combination of node and interface names.

    :ivar hostname: Node hostname to which this interface belongs
    :ivar interface: Interface name
    """

    hostname = attr.ib(type=str)
    interface = attr.ib(type=str)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> Interface
        return Interface(json_dict["hostname"], json_dict["interface"])

    def __str__(self):
        # type: () -> str
        return "{}[{}]".format(escape_name(self.hostname), escape_name(self.interface))

    def _repr_html_(self):
        # type: () -> str
        return "{}".format(escape_html(self.__str__()))


def _interface_converter(val):
    # type: (Any) -> str
    if isinstance(val, Interface):
        return str(val.interface)
    else:
        return str(val)


@attr.s(frozen=True)
class Edge(DataModelElement):
    """A network edge (i.e., a link between two node/interface pairs).

    :ivar node1: First node name
    :ivar node1interface: First node's interface name
    :ivar node2: Second node name
    :ivar node2interface: Second node's interface name
    """

    node1 = attr.ib(type=str)
    node1interface = attr.ib(type=str, converter=_interface_converter)
    node2 = attr.ib(type=str)
    node2interface = attr.ib(type=str, converter=_interface_converter)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> Edge
        return Edge(
            node1=json_dict["node1"],
            node1interface=json_dict["node1interface"],
            node2=json_dict["node2"],
            node2interface=json_dict["node2interface"],
        )

    def __str__(self):
        # type: () -> str
        return "{}:{} -> {}:{}".format(
            self.node1, self.node1interface, self.node2, self.node2interface
        )

    def _repr_html_(self):
        # type: () -> str
        return "{}:{} &rarr; {}:{}".format(
            self.node1, self.node1interface, self.node2, self.node2interface
        )


@attr.s(frozen=True)
class FileLines(DataModelElement):
    """A class that represents a set of lines in a file.

    :ivar filename: The filename referenced
    :ivar lines: A list of lines referenced
    """

    filename = attr.ib(type=str)
    lines = attr.ib(type=List[int], factory=list)

    def __str__(self):
        # type: () -> str
        return "{filename}:{lines}".format(filename=self.filename, lines=self.lines)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> FileLines
        return FileLines(
            filename=json_dict["filename"], lines=json_dict.get("lines", [])
        )


@attr.s(frozen=True)
class IssueType(DataModelElement):
    """Details about a particular :py:class:`Issue` type.

    :ivar major: Primary type of the issue
    :ivar minor: Additional subcategory of the issue
    """

    major = attr.ib(type=str)
    minor = attr.ib(type=str)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> IssueType
        return IssueType(json_dict["major"], json_dict["minor"])


@attr.s(frozen=True)
class Issue(DataModelElement):
    """Information about a bug/issue that Batfish has discovered.

    :ivar severity: The integer severity of the issue
    :ivar explanation: An explanation for the issue
    :ivar type: An :py:class:`IssueType` containing more information about the issue
    """

    severity = attr.ib(type=int, converter=int)
    explanation = attr.ib(type=str)
    type = attr.ib(type=IssueType)

    @explanation.default
    def _default_explanation(self):
        # type: () -> str
        return "No explanation"

    @type.default
    def _default_type(self):
        # type: () -> IssueType
        return IssueType(major="Unknown", minor="Unknown")

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> Issue
        if "severity" not in json_dict:
            raise ValueError("'severity' not present in the Issue object")
        return Issue(
            json_dict["severity"],
            json_dict.get("explanation", "No explanation"),
            IssueType(**json_dict.get("type", dict(major="Unknown", minor="Unknown"))),
        )

    def __str__(self):
        # type: () -> str
        return "[{}] {}".format(self.severity, self.explanation)


class ListWrapper(FrozenList):
    """Helper list class that implements _repr_html_()."""

    def _repr_html_(self):
        # type: () -> str
        result = "<br><br>".join([get_html(element) for element in self])  # type: str
        return result
