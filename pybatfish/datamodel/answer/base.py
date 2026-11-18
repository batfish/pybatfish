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

from __future__ import annotations

import functools
import json
import re
from collections.abc import Callable
from typing import Any

from pybatfish.datamodel.acl import AclTrace, TraceTree, TraceTreeList
from pybatfish.datamodel.flow import Flow, FlowTrace, Trace
from pybatfish.datamodel.primitives import FileLines, Interface, ListWrapper
from pybatfish.datamodel.route import BgpRoute, BgpRouteDiffs, NextHop

__all__ = ["Answer"]

_ITERABLE_SCHEMA_PATTERN = re.compile(r"^(List|Set)<(.+)>$", re.IGNORECASE)


class Answer(dict):
    """Represents a generic Batfish answer."""

    def __str__(self):
        return json.dumps(self, indent=2)

    def question_name(self) -> str | None:
        """Return the name of the question that produced this answer."""
        if "question" in self and "instance" in self["question"] and "instanceName" in self["question"]["instance"]:
            return str(self["question"]["instance"]["instanceName"])
        return None

    def dict(self) -> dict:
        """A dictionary representation of the full answer."""
        return dict(self)


def _get_base_schema(schema: str) -> str:
    """Return the underlying base schema for an iterable (list or set)."""
    match = re.match(_ITERABLE_SCHEMA_PATTERN, schema)
    if match:
        return match.group(2)

    return schema


def _parse_json_with_schema(schema: str, json_object: Any) -> Any:
    """Process JSON object according to its schema."""
    if json_object is None:
        # Honor null/None values
        return None

    # See if it's an iterable and we need to process it
    base_schema = _get_iterable_base_schema(schema)
    if base_schema is not None:
        if not isinstance(json_object, list):
            raise ValueError(f"Got non-list value for list/set schema {schema}. Value: {json_object}")

        # Handle special iterable schemas that have a custom container class
        if base_schema == "TraceTree":
            return TraceTreeList([TraceTree.from_dict(element) for element in json_object])

        return ListWrapper([_parse_json_with_schema(base_schema, element) for element in json_object])

    parser = _SCALAR_PARSERS.get(schema)
    return json_object if parser is None else parser(json_object)


# Cached because answers are parsed cell by cell and regex matching dominated.
@functools.cache
def _get_iterable_base_schema(schema: str) -> str | None:
    """Return the element schema if schema is an iterable (list or set), else None."""
    match = _ITERABLE_SCHEMA_PATTERN.match(schema)
    return match.group(2) if match else None


def _parse_self_describing(json_object: dict[str, Any]) -> Any:
    return _parse_json_with_schema(json_object["schema"], json_object.get("value"))


_SCALAR_PARSERS: dict[str, Callable[[Any], Any]] = {
    "AclTrace": AclTrace.from_dict,
    "BgpRoute": BgpRoute.from_dict,
    "BgpRouteDiffs": BgpRouteDiffs.from_dict,
    "FileLines": FileLines.from_dict,
    "Flow": Flow.from_dict,
    "FlowTrace": FlowTrace.from_dict,
    "Integer": int,
    "Interface": Interface.from_dict,
    "Ip": str,
    "Long": int,
    "NextHop": NextHop.from_dict,
    "Node": lambda json_object: json_object["name"],
    "Prefix": str,
    "SelfDescribing": _parse_self_describing,
    "String": str,
    "Trace": Trace.from_dict,
    "TraceTree": TraceTree.from_dict,
}


def _is_iterable_schema(schema: str) -> bool:
    """Check if a given schema is an iterable/container schema."""
    return re.match(_ITERABLE_SCHEMA_PATTERN, schema) is not None
