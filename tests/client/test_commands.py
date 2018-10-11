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
