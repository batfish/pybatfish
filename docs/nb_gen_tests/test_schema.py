# coding: utf-8
import pytest
from nb_gen.schema import convert_schema


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
        convert_schema("InterfaceSpec", "input")
        == "[InterfaceSpec](../specifiers.md#interface-specifier)"
    )
    assert (
        convert_schema("headerConstraints", "input")
        == "[HeaderConstraints](../datamodel.rst#pybatfish.datamodel.flow.HeaderConstraints)"
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
