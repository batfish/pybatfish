Getting started
===============

To get started with ``Pybatfish``, you will need a network snapshot.  An example snapshot is packaged with ``Pybatfish`` (`link <https://github.com/batfish/pybatfish/tree/master/jupyter_notebooks/networks/example>`_) and can be used to step through the example below.  Alternatively, you can package a snapshot of your own network as described `here <https://github.com/batfish/batfish/wiki/Packaging-snapshots-for-analysis>`_.

The following instructions show how to upload and query a network snapshot using ``Pybatfish`` in an interactive python shell like ``IPython``.  In these instructions, it is assumed that ``Batfish`` is running on the same machine as the ``Pybatfish`` client and the example snapshot included in ``Batfish`` is being analyzed.

1. Import ``Pybatfish``:

.. code-block:: python

    from pybatfish.client.commands import *
    from pybatfish.question.question import load_questions, list_questions
    from pybatfish.question import bfq


2. Point the client to where ``Batfish`` service is running:

.. code-block:: python

    bf_session.coordinatorHost = 'localhost'

*Note that localhost here should be replaced if the* ``Batfish`` *service is running remotely.*

3. Load the question templates from the ``Batfish`` service into ``Pybatfish``:

.. code-block:: python

    >>> load_questions()
    Successfully loaded X questions from remote

4. Upload a network snapshot:

.. code-block:: python

    bf_init_snapshot('jupyter_notebooks/networks/example')

Here, the example network is being uploaded, but this location could also be a folder or a zip containing a custom network snapshot.

5. Ask a question about the snapshot, using one of the loaded templates (``bfq`` holds the questions currently loaded in ``Pybatfish``). For example here, the question ``IPOwners`` fetches the mapping between IP address, interface, node and VRF for all devices in the network. :

.. code-block:: python

    >>> ip_owners_ans = bfq.ipOwners().answer()
    
``answer()`` runs the question and returns the answer in a JSON format. See the ``Batfish`` `questions directory <https://github.com/batfish/batfish/tree/master/questions>`_ for the set of questions that can be asked and their parameters.

6. To print the answer in a nice table, call ``frame()`` which wraps the answer as `pandas dataframe <https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html>`_. Calling `head() <https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.head.html>`_ on the dataframe will print the first 5 rows. :

.. code-block:: python

    >>> ip_owners_ans.frame().head()
     Hostname      VRF           Interface          IP  Mask  Active
    0  as2border1  default  GigabitEthernet1/0   2.12.11.1    24    True
    1  as2border1  default  GigabitEthernet2/0   2.12.12.1    24    True
    2  as3border2  default           Loopback0     3.2.2.2    32    True
    3  as3border1  default  GigabitEthernet1/0  10.23.21.3    24    True
    4    as2dist2  default  GigabitEthernet0/0   2.23.22.3    24    True

7. Next, let's ask a question about interfaces. For example, to see all prefixes present on the interface ``GigabitEthernet0/0`` of the node ``as1border1`` we can use the ``interfaceProperties`` question like below:

.. code-block:: python

    >>> iface_ans = bfq.interfaceProperties(nodes='as1border1', interfaces='GigabitEthernet0/0', properties='all-prefixes').answer()
    >>> iface_ans
                           interface  all-prefixes
    0  as1border1:GigabitEthernet0/0  [1.0.1.1/24]



For additional and more in-depth examples, check out the `Jupyter Notebooks <https://github.com/batfish/pybatfish/tree/master/jupyter_notebooks>`_.
