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

import attr

from .primitives import DataModelElement

__all__ = ["AclTrace", "AclTraceEvent"]


@attr.s(frozen=True)
class AclTraceEvent(DataModelElement):
    """One event corresponding to a packet's life through an ACL.

    :ivar class_name: The type of the event that occurred while tracing.
    :ivar description: The description of the event
    :ivar lineDescription: ACL line that caused the event (if applicable)
    """

    class_name = attr.ib(type=Optional[str], default=None)
    description = attr.ib(type=Optional[str], default=None)
    lineDescription = attr.ib(type=Optional[str], default=None)

    @classmethod
    def from_dict(cls, json_dict):
        # type: (Dict) -> AclTraceEvent
        return AclTraceEvent(
            json_dict.get("class"),
            json_dict.get("description"),
            json_dict.get("lineDescription"),
        )

    def __str__(self):
        # type: () -> str
        if self.description is not None:
            return self.description
        if self.lineDescription is not None:
            return self.lineDescription
        return repr(self)


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
        return "\n".join(str(event) for event in self.events)


@attr.s(frozen=True)
class VendorStructureId(DataModelElement):
    filename = attr.ib(type=str)
    structureType = attr.ib(type=str)
    structureName = attr.ib(type=str)

    @classmethod
    def from_dict(cls, json_dict):
        return VendorStructureId(
            filename=json_dict.get("filename", ""),
            structureType=json_dict.get("structureType", ""),
            structureName=json_dict.get("structureName", ""),
        )


class Fragment(DataModelElement):
    @classmethod
    def from_dict(cls, json_dict):
        if json_dict["class"] == "TextFragment":
            return TextFragment.from_dict(json_dict)
        elif json_dict["class"] == "LinkFragment":
            return LinkFragment.from_dict(json_dict)


@attr.s(frozen=True)
class TextFragment(Fragment):
    text = attr.ib(type=str)

    @classmethod
    def from_dict(cls, json_dict):
        return TextFragment(json_dict.get("text"))

    def __str__(self):
        return self.text


@attr.s(frozen=True)
class LinkFragment(Fragment):
    text = attr.ib(type=str)
    vendorStructureId = attr.ib(type=VendorStructureId)

    @classmethod
    def from_dict(cls, json_dict):
        return LinkFragment(
            json_dict.get("text", ""),
            VendorStructureId.from_dict(json_dict.get("vendorStructureId", {})),
        )

    def __str__(self):
        return self.text


@attr.s(frozen=True)
class TraceElement(DataModelElement):
    fragments = attr.ib(type=List[Fragment])

    @classmethod
    def from_dict(cls, json_dict):
        return TraceElement([Fragment.from_dict(f) for f in json_dict.get("fragments", [])])

    def __str__(self):
        return " ".join(str(fragment) for fragment in self.fragments)


@attr.s(frozen=True)
class TraceNode(DataModelElement):
    traceElement = attr.ib(type=TraceElement)
    children = attr.ib(type=List["TraceNode"])

    @classmethod
    def from_dict(cls, json_dict):
        return TraceNode(
            TraceElement.from_dict(json_dict.get("traceElement", {})),
            [TraceNode.from_dict(child) for child in json_dict.get("children", [])],
        )

    def __str__(self):
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

    def _repr_html_(self):
        if self.children:
            children_section = []
            for child in self.children:
                children_section.append("<li>{}</li>".format(child._repr_html_()))
            return "{} <ul>{}</ul>".format(self.traceElement, "".join(children_section))
        return str(self.traceElement)


if __name__ == "__main__":
    tree = TraceNode.from_dict({
        "traceElement": {
            "fragments": [
                {"class": "TextFragment", "text": "Matched rule"},
                {
                    "class": "LinkFragment",
                    "text": "PERMIT-DMVPN",
                    "vendorStructureId": {"filename": "configs/some-config", "structureType": "??", "structureName": "???"}
                }
            ]
        },
        "children": [{
            "traceElement": {
                "fragments": [
                    {"class": "TextFragment", "text": "Matched"},
                    {"class": "TextFragment", "text": "source-address"},
                    {"class": "TextFragment", "text": "any-ipv4"}
                ]
            }
        }, {
            "traceElement": {
                "fragments": [
                    {"class": "TextFragment", "text": "Matched"},
                    {"class": "TextFragment", "text": "destination-address"},
                    {
                        "class": "LinkFragment",
                        "text": "GBL_SEA-PUBLIC-NETS",
                        "vendorStructureId": {"filename": "configs/some-config", "structureType": "??", "structureName": "???"}
                    }
                ]
            },
            "children": [{
                "traceElement": {
                    "fragments": [
                        {"class": "TextFragment", "text": "Matched"},
                        {"class": "TextFragment", "text": "address"},
                        {
                            "class": "LinkFragment",
                            "text": "GBL_SEA-PUBLIC-NET-101.45.24.0",
                            "vendorStructureId": {"filename": "configs/some-config", "structureType": "??", "structureName": "???"}
                        }
                    ]
                }
            }]
        }, {
            "traceElement": {
                "fragments": [
                    {"class": "TextFragment", "text": "Matched"},
                    {"class": "TextFragment", "text": "application"},
                    {"class": "TextFragment", "text": "junos-ike"}
                ]
            }
        }]
    })
    print(tree)
    print(tree._repr_html_())
