from pybatfish.client.commands import bf_set_network, bf_init_snapshot
import pytest


def test_network_validation():
    with pytest.raises(ValueError):
        bf_set_network('foo/bar')


def test_snapshot_validation():
    with pytest.raises(ValueError):
        bf_init_snapshot("x", name="foo/bar")
