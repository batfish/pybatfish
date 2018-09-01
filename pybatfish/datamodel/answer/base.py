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
from string import Template
from typing import Optional  # noqa: F401

from pybatfish.datamodel.acltrace import AclTrace
from pybatfish.datamodel.answer.issue import Issue
from pybatfish.datamodel.filelines import FileLines
from pybatfish.datamodel.flow import Flow
from pybatfish.datamodel.flowtrace import FlowTrace
from pybatfish.datamodel.interface import Interface

__all__ = ['Answer']

_LIST_SCHEMA_PATTERN = re.compile(r'^List<(.+)>$')
_SET_SCHEMA_PATTERN = re.compile(r'^Set<(.+)>$')


class Answer(dict):
    """Represents a generic Batfish answer."""

    def __str__(self):
        return json.dumps(self, indent=2)

    def question_name(self):
        # type: () -> Optional[str]
        if "question" in self and "instance" in self["question"] \
                and "instanceName" in self["question"]["instance"]:
            return str(self["question"]["instance"]["instanceName"])
        return None


def get_answer_text(answerJson):
    if "question" not in answerJson:
        # strange answer; without a question object
        return json.dumps(answerJson, indent=2)
    if "status" not in answerJson or answerJson["status"] != "SUCCESS":
        # the question was not answered successfully
        return json.dumps(answerJson, indent=2)
    question = answerJson["question"]
    if "JsonPathQuestion" not in question["class"]:
        # we haven't extended display hints to other question types
        return json.dumps(answerJson, indent=2)
    queries = question["paths"]
    if "displayHints" not in queries[0]:
        # this jsonpath question template did not have display hints
        return json.dumps(answerJson, indent=2)

    return _get_display_answer_text(answerJson)


def _get_display_answer_text(answerJson):
    question = answerJson["question"]
    answerElement = answerJson["answerElements"][0]
    queries = question["paths"]
    summary = answerJson["summary"]

    displayText = "Status: " + answerJson["status"] + "\n"
    displayText += "NumPassed: {} NumFailed: {} NumResults: {}\n".format(
        summary["numPassed"], summary["numFailed"],
        summary["numResults"])
    if summary["numResults"] > 0:
        displayText += "-" * 30 + "\n"
        for index, query in enumerate(queries):
            query = queries[index]
            displayHints = query["displayHints"]

            displayValues = answerElement["results"][str(index)][
                "extractedValues"]
            result = answerElement["results"][str(index)]["result"]

            for resultKey in iter(result):
                if (resultKey not in displayValues):
                    raise ValueError("display values not found for result ",
                                     resultKey)
                displayText += _get_display_result_text(displayHints,
                                                        displayValues[
                                                            resultKey]) + "\n"
                displayText += "\n" + "-" * 30 + "\n"

    return displayText


def _get_display_result_text(displayHints, displayValues):
    displaySchemas = _get_display_schemas(displayHints)
    values = {}
    for varName in displayValues:
        values[varName] = _get_display_value(displaySchemas[varName],
                                             displayValues[varName])
    textTemplate = Template(displayHints["textDesc"])
    return "  " + textTemplate.substitute(values)


def _get_display_schemas(displayHints):
    schemas = {}
    if "compositions" in displayHints:
        for varName in displayHints["compositions"]:
            schemas[varName] = displayHints["compositions"][varName]["schema"]
    if "extractions" in displayHints:
        for varName in displayHints["extractions"]:
            schemas[varName] = displayHints["extractions"][varName]["schema"]
    return schemas


def _get_base_schema(schema):
    match = re.match(_LIST_SCHEMA_PATTERN, schema)
    if match:
        return match.group(1)

    match = re.match(_SET_SCHEMA_PATTERN, schema)
    if match:
        return match.group(1)

    return schema


def _get_display_value(schema, json_object):
    # type (str, Any) -> Any
    if json_object is None:
        return None
    if _is_list_or_set_schema(schema):
        if not isinstance(json_object, list):
            raise ValueError("Got non-list value for list/set schema", schema,
                             ":", json_object)
        output_list = [
            str(_get_display_value(_get_base_schema(schema), element)) for
            element in json_object]
        if _get_base_schema(schema) == "FlowTrace":
            return "\n".join(output_list)
        else:
            return output_list
    if schema == "AclTrace":
        return AclTrace(json_object)
    if schema == "FileLines":
        return FileLines(json_object)
    if schema == "Flow":
        return Flow(json_object)
    if schema == "FlowTrace":
        return FlowTrace(json_object)
    if schema == "Integer":
        return int(json_object)
    if schema == "Interface":
        return Interface(json_object)
    if schema == "Ip":
        return str(json_object)
    if schema == "Issue":
        return Issue(json_object)
    if schema == "Node":
        return json_object["name"]
    if schema == "Prefix":
        return str(json_object)
    if schema == "SelfDescribing":
        return _get_display_value(json_object["schema"],
                                  json_object.get("value"))
    if schema == "String":
        return str(json_object)
    return json_object


def _is_list_or_set_schema(schema):
    return re.match(_LIST_SCHEMA_PATTERN, schema) or re.match(
        _SET_SCHEMA_PATTERN, schema)
