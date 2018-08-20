Getting started
===============

To get started with ``Pybatfish``, you will need a network snapshot.  An example snapshot is packaged with ``Batfish`` at ``<batfish_repository_root>/networks/example`` (`here <https://github.com/batfish/batfish/tree/master/networks/example>`_) and can be used to step through the example below.  Alternatively, you can package a snapshot of your own network as described `here <https://github.com/batfish/batfish/wiki/Packaging-snapshots-for-analysis>`_.

The following instructions show how to upload and query a network snapshot using `Pybatfish` in an interactive python shell like ``IPython``.  In these instructions, it is assumed that ``Batfish`` is running on the same machine as the ``Pybatfish`` client and the example snasphot included in ``Batfish`` is being analyzed.

1. Import ``Pybatfish``:

.. code-block:: python

    from pybatfish.client.commands import *
    from pybatfish.question.question import load_questions, list_questions
    from pybatfish.question import bfq


2. Point the client to where ``Batfish`` service is running:

.. code-block:: python

    bf_session.coordinatorHost = 'localhost'

*Note that localhost here should be replaced if the* ``Batfish`` *service is running remotely.*

3. Load the question templates from the ``Batfish`` service into the ``bfq`` object:

.. code-block:: python

    >>> load_questions()
    Successfully loaded X questions from remote

4. Upload a network snapshot:

.. code-block:: python

    bf_init_snapshot('jupyter_notebooks/networks/example')

Here, the example network is being uploaded, but this location could also be a folder or a zip containing a custom network snapshot.

5. Ask a question about the snapshot, using one of the loaded templates.  Here, a general question is asked, fetching configured interfaces for any network node starting with ``as1border``:

.. code-block:: python

    >>> node_ans = bfq.nodeProperties(nodeRegex='as1border.*').answer()
    status: TRYINGTOASSIGN
    .... no task information
    status: TERMINATEDNORMALLY
    .... Mon Jul 30 14:55:04 2018 PDT Begin job

See the ``Batfish`` `questions directory <https://github.com/batfish/batfish/tree/master/questions>`_ for the set of question that can be asked and their parameters.

6. Print the resulting answer object's rows to view properties of the queried nodes (this corresponds to the data-model for the queried nodes ``as1border1`` and ``as1border2``):

.. code-block:: python

    >>> node_ans['rows']
    [{'as-path-access-lists': [],
      'authentication-key-chains': [],
      'canonical-ip': '1.0.1.1',
      'community-lists': ['as3_community', 'as1_community', 'as2_community'],
      'configuration-format': 'CISCO_IOS',
      'default-cross-zone-action': 'ACCEPT',
      'default-inbound-action': 'ACCEPT',
      'device-type': 'ROUTER',
      'dns-servers': [],
      'dns-source-interface': None,
      'domain-name': 'lab.local',
      'hostname': 'as1border1',
      'ike-gateways': [],
      'ike-policies': [],
      'interfaces': ['GigabitEthernet0/0',
       'GigabitEthernet1/0',
       'Ethernet0/0',
       'Loopback0'],
      'ip-access-lists': ['101', '102', '103'],
    ...


7. Ask a question retrieving the ``all-prefixes`` properties of ``GigabitEthernet0/0`` interface of ``asborder1`` and print the resulting answer:

.. code-block:: python

    >>> iface_ospf_ans = bfq.interfaceProperties(nodeRegex='as1border1', interfaceRegex='GigabitEthernet0/0', propertySpec='all-prefixes').answer()
    >>> iface_ospf_ans
                           interface  all-prefixes
    0  as1border1:GigabitEthernet0/0  [1.0.1.1/24]

Note that that a resulting answer table can be displayed in several ways:

.. code-block:: python

    >>> iface_ans = bfq.interfaceProperties(nodeRegex='as1border1', interfaceRegex='Gigabit.*').answer()
    >>> iface_ans
                           interface  ospf-enabled  rip-enabled description  proxy-arp interface-type    ...
    0  as1border1:GigabitEthernet0/0          True        False        None       True       PHYSICAL    ...
    1  as1border1:GigabitEthernet1/0         False        False        None       True       PHYSICAL    ...
    [2 rows x 39 columns]

    >>> iface_ans['rows']
    [{'interface': {'hostname': 'as1border1', 'interface': 'GigabitEthernet0/0'},
      'ospf-enabled': True,
      'rip-enabled': False,
      'description': None,
      'proxy-arp': True,
      'interface-type': 'PHYSICAL',
      'source-nats': [],
      'vrrp-groups': [],
      'routing-policy-name': None,
      'ospf-point-to-point': False,
      'access-vlan': 0,
      'ospf-area-name': 1,
    ...

    >>> iface_ans['rows'][0]['all-prefixes']
    [1.0.1.1/24]


For additional and more in-depth examples, checkout the `Jupyter Notebooks <https://github.com/batfish/pybatfish/tree/master/jupyter_notebooks>`_.
