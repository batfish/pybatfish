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

import pytest

from pybatfish.client.commands import (bf_fork_snapshot, bf_init_snapshot,
                                       bf_set_network)


def test_network_validation():
    with pytest.raises(ValueError):
        bf_set_network('foo/bar')


def test_snapshot_validation():
    with pytest.raises(ValueError):
        bf_init_snapshot("x", name="foo/bar")


def test_fork_snapshot_validation():
    with pytest.raises(ValueError):
        bf_fork_snapshot(base_name="x", name="foo/bar")
