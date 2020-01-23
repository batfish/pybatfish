# coding: utf-8
from os.path import abspath, dirname, realpath
from pathlib import Path

import pytest
import cerberus
import yaml

from nb_gen.schema import convert_schema

_THIS_DIR: Path = Path(abspath(dirname(realpath(__file__))))
_DOC_DIR: Path = _THIS_DIR.parent
_QUESTIONS_YAML: Path = _DOC_DIR / "nb_gen" / "questions.yaml"


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
    assert convert_schema("interface", "output") == "str"
    assert (
        convert_schema("interface", "input")
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
    assert convert_schema("SelfDescribing", "output", "bgpPeerConfiguration") == "str"
    with pytest.raises(ValueError):
        assert convert_schema("SelfDescribing", "output") == "str"
    with pytest.raises(KeyError):
        assert convert_schema("SelfDescribing", "output", "fooooo") == "str"


def test_questions_yaml_schema():
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
        "categories": {
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": {
                    "name": {"type": "string", "required": True},
                    "description": {"type": "string"},
                    "questions": {
                        "type": "list",
                        "schema": {
                            "type": "dict",
                            "schema": {
                                "name": {"type": "string", "required": True},
                                "pybf_name": {"type": "string", "required": True},
                                "type": {"type": "string"},
                                "snapshot": snapshot_schema,
                                "reference_snapshot": snapshot_schema,
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
    doc = yaml.safe_load(_QUESTIONS_YAML.open())
    if not v.validate(doc):
        raise AssertionError(v.errors)
