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
import uuid
from os.path import abspath, dirname, join, pardir, realpath

import pytest
import requests
from requests import HTTPError

from pybatfish.client.commands import (bf_delete_network,
                                       bf_delete_snapshot, bf_fork_snapshot,
                                       bf_generate_dataplane,
                                       bf_get_snapshot_inferred_node_role_dimension,
                                       bf_get_snapshot_inferred_node_roles,
                                       bf_get_snapshot_node_role_dimension,
                                       bf_get_snapshot_node_roles,
                                       bf_init_snapshot, bf_list_snapshots,
                                       bf_put_node_roles,
                                       bf_session, bf_set_network,
                                       bf_set_snapshot, bf_upload_diagnostics)
from pybatfish.client.consts import BfConsts
from pybatfish.client.diagnostics import (_INIT_INFO_QUESTIONS, _S3_BUCKET,
                                          _S3_REGION,
                                          _get_snapshot_parse_status)
from pybatfish.client.extended import (bf_get_snapshot_input_object_text,
                                       bf_get_snapshot_object_text,
                                       bf_put_snapshot_object)
from pybatfish.datamodel import Edge, Interface
from pybatfish.datamodel.referencelibrary import (NodeRoleDimension,
                                                  NodeRolesData)

_this_dir = abspath(dirname(realpath(__file__)))
_root_dir = abspath(join(_this_dir, pardir, pardir))


@pytest.fixture()
def network():
    name = bf_set_network()
    yield name
    # cleanup
    bf_delete_network(name)


def test_init_snapshot_no_crash(network):
    """Run some init snapshot commands. The goal is not to crash."""
    bf_set_network(network)
    uid = uuid.uuid4().hex
    try:
        bf_init_snapshot(join(_this_dir, 'snapshot'), uid)
        bf_generate_dataplane()
    finally:
        # cleanup
        bf_delete_snapshot(uid)


@pytest.fixture()
def example_snapshot(network):
    bf_set_network(network)
    name = uuid.uuid4().hex
    bf_init_snapshot(join(_this_dir, 'snapshot'), name)
    yield name
    # cleanup
    bf_delete_snapshot(name)


@pytest.fixture()
def fully_recognized_snapshot(network):
    bf_set_network(network)
    name = uuid.uuid4().hex
    bf_init_snapshot(join(_this_dir, 'snapshot_fully_recognized'), name)
    yield name
    # cleanup
    bf_delete_snapshot(name)


@pytest.fixture()
def partially_unrecognized_snapshot(network):
    bf_set_network(network)
    name = uuid.uuid4().hex
    bf_init_snapshot(join(_this_dir, 'snapshot_partially_unrecognized'), name)
    yield name
    # cleanup
    bf_delete_snapshot(name)


@pytest.fixture()
def roles_snapshot(network):
    bf_set_network(network)
    name = uuid.uuid4().hex
    bf_init_snapshot(join(_this_dir, 'roles_snapshot'), name)
    yield name
    # cleanup
    bf_delete_snapshot(name)


def test_get_snapshot_file_status(network, example_snapshot):
    """Confirm we get correct init info statuses for example snapshot."""
    statuses = _get_snapshot_parse_status()
    assert (statuses == {
        'configs/unrecognized.cfg': 'PARTIALLY_UNRECOGNIZED',
        'configs/recognized.cfg': 'PASSED',
    })


def test_fork_snapshot(network, example_snapshot):
    """Run fork snapshot command with valid and invalid inputs."""
    name = uuid.uuid4().hex

    bf_set_network(network)
    try:
        # Should succeed with existent base snapshot and valid name
        bf_fork_snapshot(base_name=example_snapshot, name=name)

        # Fail using existing snapshot name without specifying overwrite
        with pytest.raises(ValueError):
            bf_fork_snapshot(base_name=example_snapshot, name=name)
    finally:
        bf_delete_snapshot(name)


def test_fork_snapshot_add_files(network, example_snapshot):
    """Run fork snapshot command that adds files."""
    name = uuid.uuid4().hex

    bf_set_network(network)
    try:
        # Should succeed uploading a zip with a new file
        bf_fork_snapshot(base_name=example_snapshot, name=name,
                         add_files=join(_this_dir, 'fork'))

    finally:
        bf_delete_snapshot(name)


def test_fork_snapshot_bad_restore(network, example_snapshot):
    """Run fork snapshot with invalid restore item."""
    fail_name = uuid.uuid4().hex
    node = 'as2border1'

    bf_set_network(network)
    # Should fail when trying to restore an item that was never deactivated
    # in base snapshot
    with pytest.raises(HTTPError):
        bf_fork_snapshot(base_name=example_snapshot, name=fail_name,
                         restore_nodes=[node])


def test_fork_snapshot_deactivate(network, example_snapshot):
    """Use fork snapshot to deactivate and restore items."""
    deactivate_name = uuid.uuid4().hex
    restore_name = uuid.uuid4().hex
    node = 'as2border1'
    interface = Interface(hostname='as1border1', interface='GigabitEthernet1/0')
    link = Edge(node1='as2core1', node1interface='GigabitEthernet1/0',
                node2='as2border2', node2interface='GigabitEthernet2/0')

    bf_set_network(network)
    try:
        # Should succeed with deactivations
        bf_fork_snapshot(base_name=example_snapshot, name=deactivate_name,
                         deactivate_interfaces=[interface],
                         deactivate_links=[link],
                         deactivate_nodes=[node])

        # Should succeed with valid restorations from snapshot with deactivation
        bf_fork_snapshot(base_name=deactivate_name, name=restore_name,
                         restore_interfaces=[interface], restore_links=[link],
                         restore_nodes=[node])
    finally:
        bf_delete_snapshot(deactivate_name)
        bf_delete_snapshot(restore_name)


def test_fork_snapshot_no_base(network):
    """Run fork snapshot command with a bogus base snapshot."""
    name = uuid.uuid4().hex

    bf_set_network(network)
    # Should fail with non-existent base snapshot
    with pytest.raises(HTTPError):
        bf_fork_snapshot(base_name="bogus", name=name)


def test_fork_snapshot_no_network():
    """Run fork snapshot command without setting a network."""
    name = uuid.uuid4().hex

    bf_session.network = None
    # Should fail when network is not set
    with pytest.raises(ValueError):
        bf_fork_snapshot(base_name="base_name", name=name)


def test_list_snapshots_empty(network):
    bf_set_network(network)
    assert not bf_list_snapshots()
    verbose = bf_list_snapshots(verbose=True)
    assert verbose == []


def test_list_snapshots(network, example_snapshot):
    bf_set_network(network)
    assert bf_list_snapshots() == [example_snapshot]
    verbose = bf_list_snapshots(verbose=True)
    assert verbose
    assert len(verbose) == 1
    assert verbose[0][BfConsts.PROP_NAME] == example_snapshot


def test_get_snapshot_inferred_node_role_dimension(network, roles_snapshot):
    bf_set_network(network)
    bf_set_snapshot(roles_snapshot)
    # should not crash
    bf_get_snapshot_inferred_node_role_dimension('auto1')


def test_get_snapshot_inferred_node_roles(network, roles_snapshot):
    bf_set_network(network)
    bf_set_snapshot(roles_snapshot)
    # should not be empty
    assert len(bf_get_snapshot_inferred_node_roles().roleDimensions) > 0


def test_get_snapshot_input_object(network, example_snapshot):
    bf_set_network(network)
    bf_set_snapshot(example_snapshot)
    # non-existent input object should yield 404
    with pytest.raises(HTTPError, match='404'):
        bf_get_snapshot_input_object_text('missing_object')
    # should be able to retrieve input object text
    assert bf_get_snapshot_input_object_text('other_dir/other_file') == 'hello'


def test_get_snapshot_node_role_dimension(network, roles_snapshot):
    bf_set_network(network)
    bf_set_snapshot(roles_snapshot)
    node_roles = NodeRolesData([NodeRoleDimension('dim1')])
    bf_put_node_roles(node_roles)
    # should not crash
    bf_get_snapshot_node_role_dimension('dim1')


def test_get_snapshot_node_roles(network, roles_snapshot):
    bf_set_network(network)
    bf_set_snapshot(roles_snapshot)
    dimension_name = 'dim1'
    node_roles = NodeRolesData([NodeRoleDimension(dimension_name)])
    bf_put_node_roles(node_roles)
    # there should be 1 role dimension
    snapshot_node_roles = bf_get_snapshot_node_roles()
    assert len(snapshot_node_roles.roleDimensions) == 1
    assert snapshot_node_roles.roleDimensions[0].name == dimension_name


def test_get_snapshot_object(network, example_snapshot):
    bf_set_network(network)
    bf_set_snapshot(example_snapshot)
    # non-existent object should yield 404
    with pytest.raises(HTTPError, match='404'):
        bf_get_snapshot_object_text('missing_object')
    # object should exist after being placed
    bf_put_snapshot_object('new_object', 'goodbye')
    assert bf_get_snapshot_object_text('new_object') == 'goodbye'


def test_upload_diagnostics(network, example_snapshot):
    """Upload initialization information for example snapshot."""
    # This call raises an exception if any file upload results in HTTP status != 200
    resource = bf_upload_diagnostics(dry_run=False)
    base_url = 'https://{bucket}.s3-{region}.amazonaws.com'.format(
        bucket=_S3_BUCKET, region=_S3_REGION)

    # Confirm none of the uploaded questions are accessible
    for q in _INIT_INFO_QUESTIONS:
        r = requests.get('{}/{}/{}'.format(base_url, resource, q.get_name()))
        assert (r.status_code == 403)
