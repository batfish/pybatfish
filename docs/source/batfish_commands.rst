Batfish Commands
=================

Here we describe the non-question related Batfish functions

.. currentmodule:: pybatfish.client.commands

Networks
--------
.. autofunction:: bf_set_network
.. autofunction:: bf_list_networks
.. autofunction:: bf_delete_network

Snapshots
---------
.. autofunction:: bf_init_snapshot
.. autofunction:: bf_set_snapshot
.. autofunction:: bf_list_snapshots
.. autofunction:: bf_delete_snapshot
.. autofunction:: bf_fork_snapshot

Reference Library
-----------------
.. autofunction:: bf_get_reference_library
.. autofunction:: bf_get_reference_book
.. autofunction:: bf_put_reference_book
.. autofunction:: bf_delete_reference_book

.. Excluding any role-related commands (for now)
.. .. autofunction:: bf_get_node_roles
.. .. autofunction:: bf_put_node_roles
.. .. autofunction:: bf_add_node_role_dimension
.. .. autofunction:: bf_put_node_role_dimension
.. .. autofunction:: bf_get_node_role_dimension
.. .. autofunction:: bf_delete_node_role_dimension

Diagnostics
-----------
.. autofunction:: bf_upload_diagnostics
