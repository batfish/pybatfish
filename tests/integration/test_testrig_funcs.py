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

import pytest

from pybatfish.client.commands import bf_init_network, bf_list_snapshots, \
    bf_delete_network
from pybatfish.client.consts import CoordConsts

TEST_NETWORK = 'test_network_pytest'


@pytest.fixture(scope='module')
def network():
    yield bf_init_network(TEST_NETWORK)
    bf_delete_network(TEST_NETWORK)


def test_list_testrigs(network):
    """Expect empty list from bf_list_snapshots for an empty current network."""
    assert not bf_list_snapshots().get(CoordConsts.SVC_KEY_SNAPSHOT_LIST)
