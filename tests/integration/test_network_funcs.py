from pybatfish.client.commands import bf_init_network, bf_delete_network
from pybatfish.client.options import Options


def test_init_network():
    try:
        assert bf_init_network('foobar') == 'foobar'
    finally:
        bf_delete_network('foobar')

    name = bf_init_network()
    try:
        assert name.startswith(Options.default_network_prefix)
    finally:
        bf_delete_network(name)
