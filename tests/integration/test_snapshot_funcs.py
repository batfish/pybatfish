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
import typing
import uuid
from os.path import abspath, dirname, join, pardir, realpath

import pytest
from requests import HTTPError

from pybatfish.client.consts import BfConsts
from pybatfish.client.session import Session
from pybatfish.datamodel import Interface
from pybatfish.datamodel.referencelibrary import NodeRolesData, RoleMapping
from tests.common_util import requires_bf

_this_dir = abspath(dirname(realpath(__file__)))
_root_dir = abspath(join(_this_dir, pardir, pardir))


@pytest.fixture(scope="module")
def bf() -> Session:
    return Session()


@pytest.fixture()
def network(bf: Session) -> typing.Generator[str, None, None]:
    name = bf.set_network()
    yield name
    # cleanup
    bf.delete_network(name)


@pytest.fixture()
def example_snapshot(bf: Session, network: str) -> typing.Generator[str, None, None]:
    bf.set_network(network)
    name = uuid.uuid4().hex
    bf.init_snapshot(join(_this_dir, "snapshot"), name)
    yield name
    # cleanup
    bf.delete_snapshot(name)


@pytest.fixture()
def file_status_snapshot(
    bf: Session, network: str
) -> typing.Generator[str, None, None]:
    bf.set_network(network)
    name = uuid.uuid4().hex
    bf.init_snapshot(join(_this_dir, "snapshot_file_status"), name)
    yield name
    # cleanup
    bf.delete_snapshot(name)


@pytest.fixture()
def roles_snapshot(bf: Session, network: str) -> typing.Generator[str, None, None]:
    bf.set_network(network)
    name = uuid.uuid4().hex
    bf.init_snapshot(join(_this_dir, "roles_snapshot"), name)
    yield name
    # cleanup
    bf.delete_snapshot(name)


def test_init_snapshot_no_crash(bf: Session, network: str) -> None:
    """Run some init snapshot commands. The goal is not to crash."""
    bf.set_network(network)
    uid = uuid.uuid4().hex
    try:
        bf.init_snapshot(join(_this_dir, "snapshot"), uid)
        bf.generate_dataplane()
    finally:
        # cleanup
        bf.delete_snapshot(uid)


def test_fork_snapshot(bf: Session, network: str, example_snapshot: str) -> None:
    """Run fork snapshot command with valid and invalid inputs."""
    name = uuid.uuid4().hex

    bf.set_network(network)
    try:
        # Should succeed with existent base snapshot and valid name
        bf.fork_snapshot(base_name=example_snapshot, name=name)

        # Fail using existing snapshot name without specifying overwrite
        with pytest.raises(ValueError):
            bf.fork_snapshot(base_name=example_snapshot, name=name)
    finally:
        bf.delete_snapshot(name)


def test_fork_snapshot_add_files(
    bf: Session, network: str, example_snapshot: str
) -> None:
    """Run fork snapshot command that adds files."""
    name = uuid.uuid4().hex

    bf.set_network(network)
    try:
        # Should succeed uploading a zip with a new file
        bf.fork_snapshot(
            base_name=example_snapshot, name=name, add_files=join(_this_dir, "fork")
        )

    finally:
        bf.delete_snapshot(name)


def test_fork_snapshot_bad_restore(
    bf: Session, network: str, example_snapshot: str
) -> None:
    """Run fork snapshot with invalid restore item."""
    fail_name = uuid.uuid4().hex
    node = "as2border1"

    bf.set_network(network)
    # Should fail when trying to restore an item that was never deactivated
    # in base snapshot
    with pytest.raises(HTTPError):
        bf.fork_snapshot(
            base_name=example_snapshot, name=fail_name, restore_nodes=[node]
        )


def test_fork_snapshot_deactivate(
    bf: Session, network: str, example_snapshot: str
) -> None:
    """Use fork snapshot to deactivate and restore items."""
    deactivate_name = uuid.uuid4().hex
    restore_name = uuid.uuid4().hex
    node = "as2border1"
    interface = Interface(hostname="as1border1", interface="GigabitEthernet1/0")

    bf.set_network(network)
    try:
        # Should succeed with deactivations
        bf.fork_snapshot(
            base_name=example_snapshot,
            name=deactivate_name,
            deactivate_interfaces=[interface],
            deactivate_nodes=[node],
        )

        # Should succeed with valid restorations from snapshot with deactivation
        bf.fork_snapshot(
            base_name=deactivate_name,
            name=restore_name,
            restore_interfaces=[interface],
            restore_nodes=[node],
        )
    finally:
        bf.delete_snapshot(deactivate_name)
        bf.delete_snapshot(restore_name)


def test_fork_snapshot_no_base(bf: Session, network: str) -> None:
    """Run fork snapshot command with a bogus base snapshot."""
    name = uuid.uuid4().hex

    bf.set_network(network)
    # Should fail with non-existent base snapshot
    with pytest.raises(HTTPError):
        bf.fork_snapshot(base_name="bogus", name=name)


def test_fork_snapshot_no_network(bf: Session) -> None:
    """Run fork snapshot command without setting a network."""
    name = uuid.uuid4().hex

    bf.network = None
    # Should fail when network is not set
    with pytest.raises(ValueError):
        bf.fork_snapshot(base_name="base_name", name=name)


def test_list_snapshots_empty(bf: Session, network: str) -> None:
    bf.set_network(network)
    assert not bf.list_snapshots()
    verbose = bf.list_snapshots(verbose=True)
    assert verbose == []


def test_list_snapshots(bf: Session, network: str, example_snapshot: str) -> None:
    bf.set_network(network)
    assert bf.list_snapshots() == [example_snapshot]
    verbose = bf.list_snapshots(verbose=True)
    assert isinstance(verbose, list)
    assert len(verbose) == 1
    assert isinstance(verbose[0], dict)
    assert verbose[0][BfConsts.PROP_NAME] == example_snapshot


def test_get_snapshot_inferred_node_roles(
    bf: Session, network: str, roles_snapshot: str
) -> None:
    bf.set_network(network)
    bf.set_snapshot(roles_snapshot)
    # should not be empty
    assert len(bf.get_node_roles(inferred=True).roleMappings) > 0


@requires_bf("2024.07.01")
def test_get_snapshot_input_object(
    bf: Session, network: str, example_snapshot: str
) -> None:
    bf.set_network(network)
    bf.set_snapshot(example_snapshot)
    # non-existent input object should yield 404
    with pytest.raises(HTTPError, match="404"):
        bf.get_snapshot_input_object_text("missing_object")
    # should be able to retrieve input object text
    assert bf.get_snapshot_input_object_text("other_dir/other_file") == "hello"


def test_get_snapshot_node_roles(
    bf: Session, network: str, roles_snapshot: str
) -> None:
    bf.set_network(network)
    bf.set_snapshot(roles_snapshot)
    dimension_name = "dim1"
    mapping = RoleMapping(
        name="mapping", regex="regex", roleDimensionGroups={dimension_name: [1]}
    )
    node_roles = NodeRolesData(
        roleDimensionOrder=[dimension_name], roleMappings=[mapping]
    )
    bf.put_node_roles(node_roles)
    # there should be 1 role dimension
    snapshot_node_roles = bf.get_node_roles()
    assert len(snapshot_node_roles.roleDimensionOrder) == 1
    assert snapshot_node_roles.roleDimensionOrder[0] == dimension_name


@requires_bf("2024.07.01")
def test_delete_snapshot_object(
    bf: Session, network: str, example_snapshot: str
) -> None:
    bf.set_network(network)
    bf.set_snapshot(example_snapshot)
    # object should exist after being placed
    bf.put_snapshot_object("new_object", "goodbye")
    assert bf.get_snapshot_object_text("new_object") == "goodbye"
    # object should no longer exist after being deleted
    bf.delete_snapshot_object("new_object")
    with pytest.raises(HTTPError, match="404"):
        bf.get_snapshot_object_text("new_object")


@requires_bf("2024.07.01")
def test_get_snapshot_object(bf: Session, network: str, example_snapshot: str) -> None:
    bf.set_network(network)
    bf.set_snapshot(example_snapshot)
    # non-existent object should yield 404
    with pytest.raises(HTTPError, match="404"):
        bf.get_snapshot_object_text("missing_object")
    # object should exist after being placed
    bf.put_snapshot_object("new_object", "goodbye")
    assert bf.get_snapshot_object_text("new_object") == "goodbye"
