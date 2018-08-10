import pytest

from pybatfish.client.commands import bf_init_snapshot, bf_set_network


def test_network_validation():
    with pytest.raises(ValueError):
        bf_set_network('foo/bar')


def test_snapshot_validation():
    with pytest.raises(ValueError):
        bf_init_snapshot("x", name="foo/bar")
