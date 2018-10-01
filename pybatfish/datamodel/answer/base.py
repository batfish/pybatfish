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

import json
import re
from typing import Dict, Optional  # noqa: F401

from pybatfish.datamodel.acl import AclTrace
from pybatfish.datamodel.flow import Flow, FlowTrace
from pybatfish.datamodel.primitives import FileLines, Interface, Issue

__all__ = ['Answer']

_LIST_SCHEMA_PATTERN = re.compile(r'^List<(.+)>$')
_SET_SCHEMA_PATTERN = re.compile(r'^Set<(.+)>$')


class Answer(dict):
    """Represents a generic Batfish answer."""

    def __str__(self):
        return json.dumps(self, indent=2)

    def question_name(self):
        # type: () -> Optional[str]
        """Return the name of the question that produced this answer."""
        if "question" in self and "instance" in self["question"] \
                and "instanceName" in self["question"]["instance"]:
            return str(self["question"]["instance"]["instanceName"])
        return None

    def dict(self):
        # type: () -> Dict
        """A dictionary representation of the full answer."""
        return dict(self)


def _get_base_schema(schema):
    match = re.match(_LIST_SCHEMA_PATTERN, schema)
    if match:
        return match.group(1)

    match = re.match(_SET_SCHEMA_PATTERN, schema)
    if match:
        return match.group(1)

    return schema


def _parse_json_with_schema(schema, json_object):
    # type (str, Any) -> Any
    if json_object is None:
        return None
    if _is_list_or_set_schema(schema):
        if not isinstance(json_object, list):
            raise ValueError("Got non-list value for list/set schema", schema,
                             ":", json_object)
        output_list = [
            str(_parse_json_with_schema(_get_base_schema(schema), element)) for
            element in json_object]
        if _get_base_schema(schema) == "FlowTrace":
            return "\n".join(output_list)
        else:
            return output_list
    if schema == "AclTrace":
        return AclTrace.from_dict(json_object)
    if schema == "FileLines":
        return FileLines.from_dict(json_object)
    if schema == "Flow":
        return Flow.from_dict(json_object)
    if schema == "FlowTrace":
        return FlowTrace.from_dict(json_object)
    if schema == "Integer":
        return int(json_object)
    if schema == "Interface":
        return Interface.from_dict(json_object)
    if schema == "Ip":
        return str(json_object)
    if schema == "Issue":
        return Issue.from_dict(json_object)
    if schema == "Node":
        return json_object["name"]
    if schema == "Prefix":
        return str(json_object)
    if schema == "SelfDescribing":
        return _parse_json_with_schema(json_object["schema"],
                                       json_object.get("value"))
    if schema == "String":
        return str(json_object)
    return json_object


def _is_list_or_set_schema(schema):
    return re.match(_LIST_SCHEMA_PATTERN, schema) or re.match(
        _SET_SCHEMA_PATTERN, schema)
