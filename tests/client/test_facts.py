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
import os
from unittest.mock import Mock, patch

import pytest
import yaml
from pandas import DataFrame

from pybatfish.client._facts import (
    _assert_dict_subset,
    _encapsulate_nodes_facts,
    _unencapsulate_facts,
    get_facts,
    load_facts,
    validate_facts,
    write_facts,
)
from pybatfish.client.session import Session
from pybatfish.datamodel.answer import TableAnswer
from pybatfish.question.question import QuestionBase


class MockTableAnswer(TableAnswer):
    def __init__(self, frame_to_use=DataFrame()):
        self._frame = frame_to_use

    def frame(self):
        return self._frame


class MockQuestion(QuestionBase):
    def __init__(self, answer):
        self._answer = answer

    def answer(self, *args, **kwargs):
        return self._answer(*args, **kwargs)


def test_get_facts_questions():
    """Test that get facts calls the right questions, passing through the right args."""
    bf = Session(load_questions=False)
    nodes = "foo"
    with patch.object(bf.q, "nodeProperties", create=True) as mock_node, patch.object(
        bf.q, "interfaceProperties", create=True
    ) as mock_iface, patch.object(
        bf.q, "bgpPeerConfiguration", create=True
    ) as mock_peers, patch.object(
        bf.q, "bgpProcessConfiguration", create=True
    ) as mock_proc, patch.object(
        bf.q, "ospfProcessConfiguration", create=True
    ) as mock_ospf_proc, patch.object(
        bf.q, "ospfAreaConfiguration", create=True
    ) as mock_ospf_area, patch.object(
        bf.q, "ospfInterfaceConfiguration", create=True
    ) as mock_ospf_iface:
        mock_node.return_value = MockQuestion(MockTableAnswer)
        mock_iface.return_value = MockQuestion(MockTableAnswer)
        mock_proc.return_value = MockQuestion(MockTableAnswer)
        mock_peers.return_value = MockQuestion(MockTableAnswer)
        mock_ospf_proc.return_value = MockQuestion(MockTableAnswer)
        mock_ospf_area.return_value = MockQuestion(MockTableAnswer)
        mock_ospf_iface.return_value = MockQuestion(MockTableAnswer)
        get_facts(bf, nodes)

        mock_node.assert_called_with(nodes=nodes)
        mock_iface.assert_called_with(nodes=nodes)
        mock_proc.assert_called_with(nodes=nodes)
        mock_peers.assert_called_with(nodes=nodes)
        mock_ospf_proc.assert_called_with(nodes=nodes)
        mock_ospf_area.assert_called_with(nodes=nodes)
        mock_ospf_iface.assert_called_with(nodes=nodes)


def test_get_facts_questions_specific_snapshot():
    """Test that get facts calls the right questions, passing through the right args when a snapshot is specified."""
    bf = Session(load_questions=False)
    nodes = "foo"
    with patch.object(bf.q, "nodeProperties", create=True) as mock_node, patch.object(
        bf.q, "interfaceProperties", create=True
    ) as mock_iface, patch.object(
        bf.q, "bgpPeerConfiguration", create=True
    ) as mock_peers, patch.object(
        bf.q, "bgpProcessConfiguration", create=True
    ) as mock_proc, patch.object(
        bf.q, "ospfProcessConfiguration", create=True
    ) as mock_ospf_proc, patch.object(
        bf.q, "ospfAreaConfiguration", create=True
    ) as mock_ospf_area, patch.object(
        bf.q, "ospfInterfaceConfiguration", create=True
    ) as mock_ospf_iface:
        # Setup mock answers for each underlying question
        mock_node_a = Mock(return_value=MockTableAnswer())
        mock_iface_a = Mock(return_value=MockTableAnswer())
        mock_proc_a = Mock(return_value=MockTableAnswer())
        mock_peers_a = Mock(return_value=MockTableAnswer())
        mock_ospf_proc_a = Mock(return_value=MockTableAnswer())
        mock_ospf_area_a = Mock(return_value=MockTableAnswer())
        mock_ospf_iface_a = Mock(return_value=MockTableAnswer())

        # Setup mock questions for all underlying questions
        mock_node.return_value = MockQuestion(mock_node_a)
        mock_iface.return_value = MockQuestion(mock_iface_a)
        mock_proc.return_value = MockQuestion(mock_proc_a)
        mock_peers.return_value = MockQuestion(mock_peers_a)
        mock_ospf_proc.return_value = MockQuestion(mock_ospf_proc_a)
        mock_ospf_area.return_value = MockQuestion(mock_ospf_area_a)
        mock_ospf_iface.return_value = MockQuestion(mock_ospf_iface_a)

        get_facts(bf, nodes, snapshot="snapshot")

        # Make sure questions were all called with expected params
        mock_node.assert_called_with(nodes=nodes)
        mock_iface.assert_called_with(nodes=nodes)
        mock_proc.assert_called_with(nodes=nodes)
        mock_peers.assert_called_with(nodes=nodes)
        mock_ospf_proc.assert_called_with(nodes=nodes)
        mock_ospf_area.assert_called_with(nodes=nodes)
        mock_ospf_iface.assert_called_with(nodes=nodes)

        # Make sure answer functions were all called with expected params
        mock_node_a.assert_called_with(snapshot="snapshot")
        mock_iface_a.assert_called_with(snapshot="snapshot")
        mock_proc_a.assert_called_with(snapshot="snapshot")
        mock_peers_a.assert_called_with(snapshot="snapshot")
        mock_ospf_proc_a.assert_called_with(snapshot="snapshot")
        mock_ospf_area_a.assert_called_with(snapshot="snapshot")
        mock_ospf_iface_a.assert_called_with(snapshot="snapshot")


def test_load_facts(tmpdir):
    """Test that load_facts correctly loads facts from a fact directory."""
    version = "fake_version"
    node1 = {"node1": "foo"}
    node2 = {"node2": "foo"}
    tmpdir.join("node1.yml").write(_encapsulate_nodes_facts(node1, version))
    tmpdir.join("node2.yml").write(_encapsulate_nodes_facts(node2, version))
    facts = load_facts(str(tmpdir))

    # Confirm facts were loaded from both files
    assert facts == _encapsulate_nodes_facts({"node1": "foo", "node2": "foo"}, version)


def test_load_facts_bad_dir(tmpdir):
    """Test load facts when loading from bad directories."""
    # Empty input dir should throw ValueError
    with pytest.raises(ValueError) as e:
        load_facts(str(tmpdir))
    assert "No files present in specified dir" in str(e.value)

    f = tmpdir.join("file")
    f.write("foo")
    # File instead of dir should throw an exception about path not being a directory
    with pytest.raises(Exception) as e:
        load_facts(str(f))
    assert "Not a directory" in str(e.value)


def test_load_facts_mismatch_version(tmpdir):
    """Test load facts when loaded nodes have different format versions."""
    version1 = "version1"
    node1 = {"node1": "foo"}
    version2 = "version2"
    node2 = {"node2": "foo"}
    tmpdir.join("node1.yml").write(_encapsulate_nodes_facts(node1, version1))
    tmpdir.join("node2.yml").write(_encapsulate_nodes_facts(node2, version2))
    with pytest.raises(ValueError) as e:
        load_facts(str(tmpdir))
    assert "Input file version mismatch" in str(e.value)


def test_validate_facts():
    """Test that fact validation works for matching facts."""
    expected = {"node1": {"foo": 1}, "node2": {"foo": 2}}
    actual = {"node1": {"foo": 1}, "node2": {"foo": 2}, "node3": {"foo": 3}}
    version = "fake_version"
    res = validate_facts(
        _encapsulate_nodes_facts(expected, version),
        _encapsulate_nodes_facts(actual, version),
    )
    # No results from matching (subset) expected and actual
    assert len(res) == 0


def test_validate_facts_not_matching_version():
    """Test that fact validation detects mismatched versions."""
    expected = {"node1": {"foo": 1}, "node2": {"foo": 2}}
    actual = {"node1": {"foo": 1}, "node2": {"foo": 2}, "node3": {"foo": 3}}
    version_expected = "correct_version"
    version_actual = "fake_version"
    res = validate_facts(
        _encapsulate_nodes_facts(expected, version_expected),
        _encapsulate_nodes_facts(actual, version_actual),
    )
    # One result per expected node for mismatched version
    assert len(res) == len(expected)
    for node in expected:
        # Make sure version mismatch details are in results details
        assert res[node] == {
            "Version": {"actual": version_actual, "expected": version_expected}
        }


def test_validate_facts_not_matching_data():
    """Test that fact validation works for mismatched facts."""
    expected = {"node1": {"foo": 1, "bar": 1, "baz": 1}, "node2": {"foo": 2}}
    actual = {
        "node1": {"foo": 0, "bar": 1},  # 'foo' doesn't match expected
        # also missing 'baz': 1
        "node2": {"foo": 2},
        "node3": {"foo": 3},
    }
    version = "version"
    res = validate_facts(
        _encapsulate_nodes_facts(expected, version),
        _encapsulate_nodes_facts(actual, version),
    )

    # Result should identify the mismatched value and the missing key
    assert res == {
        "node1": {
            "foo": {"expected": 1, "actual": 0},
            "baz": {"expected": 1, "key_present": False},
        }
    }


def test_validate_facts_no_matching_node():
    """Test that fact validation works when actual facts are missing expected node."""
    expected = {"node1": {"foo": 1, "bar": 1, "baz": 1}, "node2": {"foo": 2}}
    actual = {
        "node1": {"foo": 1, "bar": 1, "baz": 1},
        # missing node2
    }
    version = "version"
    res = validate_facts(
        _encapsulate_nodes_facts(expected, version),
        _encapsulate_nodes_facts(actual, version),
    )

    # Result should identify the missing node
    assert res == {"node2": {"foo": {"expected": 2, "key_present": False}}}


def test_validate_facts_verbose():
    """Test that fact validation returns both matching and mismatched facts when running in verbose mode."""
    expected = {"node1": {"foo": 1, "bar": 1, "baz": 1}, "node2": {"foo": 2}}
    actual = {
        "node1": {"foo": 0, "bar": 1},  # 'foo' doesn't match expected
        # also missing 'baz': 1
        "node2": {"foo": 2},
        "node3": {"foo": 3},
    }
    version = "version"
    res = validate_facts(
        _encapsulate_nodes_facts(expected, version),
        _encapsulate_nodes_facts(actual, version),
        verbose=True,
    )

    # Verbose validation should return both matching and mismatched facts
    assert res == {
        "node1": {
            "foo": {"expected": 1, "actual": 0},
            "bar": {"expected": 1, "actual": 1},
            "baz": {"expected": 1, "key_present": False},
        },
        "node2": {"foo": {"expected": 2, "actual": 2}},
    }


def test_write_facts(tmpdir):
    """Test that writing facts writes nodes' facts to individual files."""
    nodes = {"node1": "foo", "node2": "bar"}
    version = "version"
    facts = _encapsulate_nodes_facts(nodes, version)
    write_facts(str(tmpdir), facts)
    for node in nodes:
        filename = node + ".yml"
        file_path = str(tmpdir.join(filename))
        assert os.path.isfile(file_path)
        with open(file_path) as f:
            node_facts_raw = yaml.safe_load(f.read())
            node_facts, node_version = _unencapsulate_facts(node_facts_raw)
            assert version == node_version, "Each file has the correct version"
            assert (
                node_facts.get(node) == nodes[node]
            ), "Each file has the correct facts"


def test_assert_dict_subset_equal():
    """Test that assert_dict_subset correctly identifies equal dicts."""
    actual = {
        "key": "value",
        "parent_key": {"nested_key": "nested_value"},
        "list": ["foo"],
        "empty_list": [],
        "none": None,
    }
    expected = {
        "key": "value",
        "parent_key": {"nested_key": "nested_value"},
        "list": ["foo"],
        "empty_list": [],
        "none": None,
    }
    # Equal dicts should result in no differences
    assert _assert_dict_subset(actual, expected) == {}


def test_assert_dict_subset_subset():
    """Test that assert_dict_subset correctly identifies expected as a subset of actual."""
    actual = {
        "key": "value",
        "key2": "value2",
        "parent_key": {"nested_key": "nested_value", "nested_key2": "nested_value2"},
    }
    expected = {"key": "value", "parent_key": {"nested_key": "nested_value"}}
    # Expected being a subset should result in no differences
    assert _assert_dict_subset(actual, expected) == {}


def test_assert_dict_subset_not_equal():
    """Test that assert_dict_subset correctly identifies when expected is not a subset of actual."""
    actual = {
        "key": "value",
        "key2": "value2",
        "parent_key": {
            "nested_key": "nested_value",
            "nested_key2": "nested_value2",
            "different_nested_key": "not_different_value",
        },
        "different_key": "not_different_value",
    }
    expected = {
        "key": "value",
        "parent_key": {
            "nested_key": "nested_value",
            "missing_nested_key": "missing_value",
            "different_nested_key": "different_value",
        },
        "missing_key": "missing_value",
        "different_key": "different_value",
    }
    # Make sure we identify missing and different values
    assert _assert_dict_subset(actual, expected) == {
        "parent_key.missing_nested_key": {
            "expected": "missing_value",
            "key_present": False,
        },
        "parent_key.different_nested_key": {
            "expected": "different_value",
            "actual": "not_different_value",
        },
        "missing_key": {"expected": "missing_value", "key_present": False},
        "different_key": {
            "expected": "different_value",
            "actual": "not_different_value",
        },
    }
