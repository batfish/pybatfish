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
from os.path import abspath, dirname, join, pardir, realpath
import uuid

from pybatfish.client.commands import (bf_delete_network, bf_delete_snapshot,
                                       bf_generate_dataplane, bf_init_network,
                                       bf_init_snapshot, bf_list_snapshots,
                                       bf_set_network)
import pytest

_this_dir = abspath(dirname(realpath(__file__)))
_root_dir = abspath(join(_this_dir, pardir, pardir))
_snapshot_dir = join(_root_dir, 'test_rigs')


@pytest.fixture()
def network():
    name = bf_init_network()
    yield name
    # cleanup
    bf_delete_network(name)


def test_init_snapshot_no_crash(network):
    """Run some init snapshot commands. The goal is not to crash."""
    bf_set_network(network)
    uid = uuid.uuid4().hex
    try:
        bf_init_snapshot(join(_snapshot_dir, 'example'), uid)
        bf_generate_dataplane()
    finally:
        # cleanup
        bf_delete_snapshot(uid)


@pytest.fixture()
def example_snapshot(network):
    bf_set_network(network)
    name = uuid.uuid4().hex
    bf_init_snapshot(join(_snapshot_dir, 'example'), name)
    yield name
    # cleanup
    bf_delete_snapshot(name)


def test_list_snapshots_empty(network):
    bf_set_network(network)
    assert not bf_list_snapshots()
    verbose = bf_list_snapshots(verbose=True)
    assert verbose
    assert verbose['snapshotlist'] == []


def test_list_snapshots(network, example_snapshot):
    bf_set_network(network)
    assert bf_list_snapshots() == [example_snapshot]
    verbose = bf_list_snapshots(verbose=True)
    assert verbose.get('snapshotlist') is not None
    assert len(verbose.get('snapshotlist')) == 1
