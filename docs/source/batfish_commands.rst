Batfish Commands
=================

Here we describe the non-question related Batfish functions

.. currentmodule:: pybatfish.client.session

Networks
--------
.. autofunction:: Session.set_network
.. autofunction:: Session.list_networks
.. autofunction:: Session.delete_network

Snapshots
---------
.. autofunction:: Session.init_snapshot
.. autofunction:: Session.set_snapshot
.. autofunction:: Session.list_snapshots
.. autofunction:: Session.delete_snapshot
.. autofunction:: Session.fork_snapshot

Reference Library
-----------------
.. autofunction:: Session.get_reference_library
.. autofunction:: Session.get_reference_book
.. autofunction:: Session.put_reference_book
.. autofunction:: Session.delete_reference_book

.. Excluding any role-related commands (for now)
.. .. autofunction:: Session.get_node_roles
.. .. autofunction:: Session.put_node_roles
.. .. autofunction:: Session.add_node_role_dimension
.. .. autofunction:: Session.put_node_role_dimension
.. .. autofunction:: Session.get_node_role_dimension
.. .. autofunction:: Session.delete_node_role_dimension

Diagnostics
-----------
.. autofunction:: Session.upload_diagnostics
