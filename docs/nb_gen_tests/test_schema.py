# coding: utf-8
from typing import Mapping, Set

import cerberus
import pytest
from nb_gen.schema import convert_schema

from pybatfish.client.session import Session


def test_convert_schema():
    """Run a bunch of tests to normalize types (and links)"""
    assert convert_schema("Integer", "input") == "int"
    assert convert_schema("Integer", "output") == "int"
    assert convert_schema("Long", "input") == "int"
    assert convert_schema("Long", "output") == "int"
    assert convert_schema("Set<String>", "input") == "Set of str"
    assert convert_schema("Set<String>", "output") == "Set of str"
    assert convert_schema("List<String>", "input") == "List of str"
    assert convert_schema("List<String>", "output") == "List of str"
    assert (
        convert_schema("interface", "output")
        == "[Interface](../datamodel.rst#pybatfish.datamodel.primitives.Interface)"
    )
    assert (
        convert_schema("InterfaceSpec", "input")
        == "[InterfaceSpec](../specifiers.md#interface-specifier)"
    )
    assert (
        convert_schema("interfaceSpec", "input")
        == "[InterfaceSpec](../specifiers.md#interface-specifier)"
    )
    assert (
        convert_schema("InterfacesSpec", "input")
        == "[InterfaceSpec](../specifiers.md#interface-specifier)"
    )
    assert (
        convert_schema("ipSpaceSpec", "input")
        == "[IpSpec](../specifiers.md#ip-specifier)"
    )
    assert (
        convert_schema("headerConstraint", "input")
        == "[HeaderConstraints](../datamodel.rst#pybatfish.datamodel.flow.HeaderConstraints)"
    )
    assert (
        convert_schema("HeaderConstraint", "input")
        == "[HeaderConstraints](../datamodel.rst#pybatfish.datamodel.flow.HeaderConstraints)"
    )
    assert (
        convert_schema("bgproutes", "input")
        == "List of [BgpRoute](../datamodel.rst#pybatfish.datamodel.route.BgpRoute)"
    )
    assert convert_schema("SelfDescribing", "output", "bgpPeerConfiguration") == "str"
    assert (
        convert_schema("NextHop", "output")
        == "[NextHop](../datamodel.rst#pybatfish.datamodel.route.NextHop)"
    )
    with pytest.raises(ValueError):
        assert convert_schema("SelfDescribing", "output") == "str"
    with pytest.raises(KeyError):
        assert convert_schema("SelfDescribing", "output", "fooooo") == "str"


def test_questions_yaml_schema(categories):
    """Ensure that "questions.yaml" conforms to the expected schema.

    Errors should be printed so that fixing the file is easier.
    """
    snapshot_schema = {
        "type": "dict",
        "schema": {
            "name": {"type": "string", "required": True},
            "path": {"type": "string", "required": True},
        },
    }
    parameter_schema = {
        "type": "dict",
        "schema": {
            "name": {"type": "string", "required": True},
            "value": {"type": ["string", "integer"], "required": True},
        },
    }
    schema = {
        "categories": {  # list of question categories
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": {
                    "name": {"type": "string", "required": True},
                    "description": {"type": "string"},  # human-readable category name
                    "introduction": {
                        "type": "string"
                    },  # what the question category does
                    "questions": {
                        "type": "list",
                        "schema": {
                            "type": "dict",
                            "schema": {
                                # human-readable question name
                                "name": {"type": "string", "required": True},
                                # code/pybatfish question name
                                "pybf_name": {"type": "string", "required": True},
                                "type": {
                                    "type": "string",  # indicates what code to generate for result inspection
                                    "allowed": [
                                        "basic",
                                        "singleflow",
                                        "dualflow",
                                        "no-result",
                                        "diff",
                                    ],
                                },
                                "snapshot": snapshot_schema,  # snapshot to execute on, if not default
                                "reference_snapshot": snapshot_schema,  # reference_snapshot for "diff" questions
                                "parameters": {
                                    "type": "list",
                                    "schema": parameter_schema,
                                },
                            },
                        },
                    },
                },
            },
        }
    }
    v = cerberus.Validator(schema)

    if not v.validate(categories):
        raise AssertionError(v.errors)


def q_names_from_categories(categories: Mapping) -> Set[str]:
    return set(
        [
            question["pybf_name"]
            for category in categories["categories"]
            for question in category["questions"]
        ]
    )


def test_all_questions_are_in_question_yaml(session: Session, categories: Mapping):
    # do not document the following questions
    exclusions = [
        "aaaAuthenticationLogin",
        "edges",
        "filterTable",
        "interfaceMtu",
        "prefixTracer",
        "transferBDDValidation",
        "viConversionStatus",
        "viConversionWarning",
        "viModel",
    ]
    xfail = {
        "multipathConsistency",
        "eigrpEdges",
        "layer1Edges",
        "isisEdges",
        "comparePeerGroupPolicies",
        "compareRoutePolicies",
    }
    session_qs = set(
        [q["name"] for q in session.q.list() if q["name"] not in exclusions]
    )
    yaml_qs = q_names_from_categories(categories)
    undocumented = set(session_qs).difference(yaml_qs)
    if undocumented != set(xfail):
        pytest.fail(
            f"These questions are not documented: {undocumented}. Expected only these to be: {xfail}"
        )
    wrongly_documented = yaml_qs.intersection(exclusions)
    if wrongly_documented:
        pytest.fail(
            f"The following questions are documented but shouldn't be: {wrongly_documented}"
        )


def test_all_questions_in_yaml_are_valid_questions(
    session: Session, categories: Mapping
):
    session_qs = set([q["name"] for q in session.q.list()])
    yaml_qs = q_names_from_categories(categories)
    assert yaml_qs.issubset(session_qs)
