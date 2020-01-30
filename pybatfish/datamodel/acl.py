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

from typing import Dict, List, Optional  # noqa: F401
from pandas.core.indexes.frozen import FrozenList

import attr

from .primitives import DataModelElement

__all__ = [
    "AclTrace",
    "AclTraceEvent",
    "Fragment",
    "LinkFragment",
    "TextFragment",
    "TraceElement",
    "TraceTree",
    "VendorStructureId",
]


@attr.s(frozen=True)
class AclTraceEvent(DataModelElement):
    """One event corresponding to a packet's life through an ACL.

    :ivar description: The description of the event
    """

    description = attr.ib(type=Optional[str], default=None)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> AclTraceEvent
        return AclTraceEvent(json_dict.get("description"))

    def __str__(self):
        # type: () -> str
        return str(self.description)


@attr.s(frozen=True)
class AclTrace(DataModelElement):
    """The trace of a packet's life through an ACL.

    :ivar events: A list of :py:class:`AclTraceEvent`
    """

    events = attr.ib(type=List[AclTraceEvent], factory=list)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> AclTrace
        return AclTrace(
            [AclTraceEvent.from_dict(event) for event in json_dict.get("events", [])]
        )

    def __str__(self):
        # type: () -> str
        return "\n".join(
            str(event) for event in self.events if event.description is not None
        )


@attr.s(frozen=True)
class VendorStructureId(DataModelElement):
    """Identifies a vendor structure in a configuration file.

    :ivar filename: Filename of the configuration file
    :ivar structureType: Type of the vendor structure
    :ivar structureName: Name of the vendor structure
    """

    filename = attr.ib(type=str)
    structureType = attr.ib(type=str)
    structureName = attr.ib(type=str)

    @classmethod
    def from_dict(cls, json_dict: Dict) -> "VendorStructureId":
        return VendorStructureId(
            filename=json_dict.get("filename", ""),
            structureType=json_dict.get("structureType", ""),
            structureName=json_dict.get("structureName", ""),
        )


class Fragment(DataModelElement):
    """An element in :py:attr:`TraceElement.fragments`, can be one of
    :py:class:`TextFragment` or :py:class:`LinkFragment`.
    """

    @classmethod
    def from_dict(cls, json_dict: Dict) -> "Fragment":
        if json_dict["class"] == "org.batfish.datamodel.TraceElement$TextFragment":
            return TextFragment.from_dict(json_dict)
        elif json_dict["class"] == "org.batfish.datamodel.TraceElement$LinkFragment":
            return LinkFragment.from_dict(json_dict)
        raise ValueError("Unknown Fragment type {}".format(json_dict["class"]))


@attr.s(frozen=True)
class TextFragment(Fragment):
    """Represents a plain-text :py:class:`Fragment`.

    :ivar text: Text content of the fragment
    """

    text = attr.ib(type=str)

    @classmethod
    def from_dict(cls, json_dict: Dict) -> "TextFragment":
        return TextFragment(json_dict.get("text", ""))

    def __str__(self) -> str:
        return self.text


@attr.s(frozen=True)
class LinkFragment(Fragment):
    """Represents a :py:class:`Fragment` that links to a vendor structure.

    :ivar text: Text content of the fragment
    :ivar vendorStructureId: Link of the fragment
    """

    text = attr.ib(type=str)
    vendorStructureId = attr.ib(type=VendorStructureId)

    @classmethod
    def from_dict(cls, json_dict: Dict) -> "LinkFragment":
        return LinkFragment(
            json_dict.get("text", ""),
            VendorStructureId.from_dict(json_dict.get("vendorStructureId", {})),
        )

    def __str__(self) -> str:
        return self.text


@attr.s(frozen=True)
class TraceElement(DataModelElement):
    """Metadata used to create human-readable traces.

    :ivar fragments: A list of :py:class:`Fragment` which describes an element of a trace
    """

    fragments = attr.ib(type=List[Fragment])

    @classmethod
    def from_dict(cls, json_dict: Dict) -> "TraceElement":
        return TraceElement(
            [Fragment.from_dict(f) for f in json_dict.get("fragments", [])]
        )

    def __str__(self) -> str:
        return "".join(str(fragment) for fragment in self.fragments)


@attr.s(frozen=True)
class TraceTree(DataModelElement):
    """Represents a filter trace tree.

    :ivar traceElement: Metadata and description of the node
    :ivar children: A list of sub-traces, i.e. children of the node
    """

    traceElement = attr.ib(type=TraceElement)
    children = attr.ib(type=List["TraceTree"])

    @classmethod
    def from_dict(cls, json_dict: Dict) -> "TraceTree":
        return TraceTree(
            TraceElement.from_dict(json_dict.get("traceElement", {})),
            [TraceTree.from_dict(child) for child in json_dict.get("children", [])],
        )

    def __str__(self) -> str:
        lines = [str(self.traceElement)]
        stack = [iter(self.children)]
        while stack:
            children_iter = stack[-1]
            try:
                child = next(children_iter)
                lines.append("  " * len(stack) + "- " + str(child.traceElement))
                stack.append(iter(child.children))
            except StopIteration:
                stack.pop()
        return "\n".join(lines)

    def _repr_html_(self) -> str:
        if self.children:
            children_section = []
            for child in self.children:
                children_section.append("<li>{}</li>".format(child._repr_html_()))
            return "{} <ul>{}</ul>".format(self.traceElement, "".join(children_section))
        return str(self.traceElement)


class TraceTreeList(FrozenList):
    """Custom list wrapper class for List<TraceTree> that prettifies console and HTML output"""

    def __str__(self) -> str:
        return "\n".join("- " + str(tree) for tree in self)

    def _repr_html_(self) -> str:
        list_items = ["<li>" + tree._repr_html_() + "</li>" for tree in self]
        return "<ul>" + "".join(list_items) + "</ul>"
