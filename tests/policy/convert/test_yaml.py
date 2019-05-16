# coding utf-8
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
"""Test conversion of YAML into commands."""

import pytest

from pybatfish.policy.commands import InitSnapshot, SetNetwork, ShowFacts
from pybatfish.policy.convert.yaml import (
    convert_yml, _extract_network, _extract_show_facts, _extract_snapshot
)

YML_CONTENTS = """
bf_commands:
    - set_network: my net name
    - init_snapshot:
        path: /my/path
        overwrite: true
    - show_facts:
        nodes: mynodes
"""


def test_convert_yml(tmpdir):
    """Test converting YML into commands."""
    filename = 'filename'
    ref_file = tmpdir.join(filename)
    ref_file.write(YML_CONTENTS)

    cmds = convert_yml(ref_file)
    assert len(cmds) == 3

    # Confirm YML is converted into the correct command types,
    # in the correct order
    net = cmds[0]
    snapshot = cmds[1]
    facts = cmds[2]
    assert isinstance(net, SetNetwork)
    assert isinstance(snapshot, InitSnapshot)
    assert isinstance(facts, ShowFacts)

    # Confirm the command param extractions are correct
    assert net.name == 'my net name'
    assert snapshot.name is None
    assert snapshot.overwrite == True
    assert snapshot.upload == '/my/path'
    assert facts.nodes == 'mynodes'


def test_extract_network():
    """Test SetNetwork extraction for valid inputs."""
    name_not_none = _extract_network('not_none')

    # Explicitly specified name should end up in command object
    assert name_not_none.name == 'not_none'


def test_extract_network_invalid():
    """Test SetNetwork extraction for invalid inputs."""
    # Passing in a list instead of a string should result in TypeError
    with pytest.raises(TypeError):
        _extract_network(['foo'])

    # Passing in None instead of a string should result in TypeError
    with pytest.raises(TypeError):
        _extract_network(None)


def test_extract_show_facts():
    """Test ShowFacts extraction for valid inputs."""
    nodes_missing = _extract_show_facts({})
    nodes_none = _extract_show_facts({'nodes': None})
    nodes_not_none = _extract_show_facts({'nodes': 'not_none'})

    # No nodes specified should result in nodes = None
    assert nodes_missing.nodes is None

    # Explicitly specified nodes should end up in command object
    assert nodes_none.nodes is None
    assert nodes_not_none.nodes == 'not_none'


def test_extract_show_facts_invalid():
    """Test ShowFacts extraction for invalid inputs."""
    # Passing in a string instead of a dict should result in TypeError
    with pytest.raises(TypeError):
        _extract_show_facts('foo')

    # Passing in a list instead of a dict should result in TypeError
    with pytest.raises(TypeError):
        _extract_show_facts(['foo'])


def test_extract_snapshot():
    """Test InitSnapshot extraction for valid inputs."""
    basic_dict = _extract_snapshot({'path': 'mypath'})
    full_dict = _extract_snapshot({
        'path': 'mypath',
        'name': 'myname',
        'overwrite': True,
    })

    # Defaults should be populated for keys not specified
    assert basic_dict.upload == 'mypath'
    assert basic_dict.overwrite == False
    assert basic_dict.name is None

    # All specified values should make it into resulting command object
    assert full_dict.upload == 'mypath'
    assert full_dict.overwrite == True
    assert full_dict.name is 'myname'


def test_extract_snapshot_invalid_type():
    """Test InitSnapshot extraction for invalid input types."""
    # Passing in a string instead of a dict should result in TypeError
    with pytest.raises(TypeError):
        _extract_snapshot('foo')

    # Passing in a list instead of a dict should result in TypeError
    with pytest.raises(TypeError):
        _extract_snapshot(['foo'])


def test_extract_snapshot_invalid_dict():
    """Test InitSnapshot extraction for dict missing required key."""
    # Passing in a dict without a path should result in ValueError
    with pytest.raises(ValueError):
        _extract_snapshot({'foo': 'bar'})
