Getting started
===============

To get started with Pybatfish, you will need a network snapshot.
An example snapshot is packaged with Pybatfish (`link <https://github.com/batfish/pybatfish/tree/master/jupyter_notebooks/networks/example>`_)
and can be used to step through the example below.  Alternatively, you can package a snapshot of your own network as described `here <https://github.com/batfish/batfish/wiki/Packaging-snapshots-for-analysis>`_.

The following instructions show how to upload and query a network snapshot using Pybatfish in an interactive python shell like IPython.
In these instructions, we assumed that Batfish is running on the same machine as Pybatfish, and the example snapshot included with Pybatfish is being analyzed.

1. Import Pybatfish:

>>> from pybatfish.client.commands import *
>>> from pybatfish.question.question import load_questions, list_questions
>>> from pybatfish.question import bfq

2. Load the question templates from the Batfish service into Pybatfish:

>>> load_questions()

4. Upload a network snapshot (you'll see some log messages followed by the
name of initialized snapshot (prefixed by ``ss_``):

>>> bf_init_snapshot('jupyter_notebooks/networks/example') # doctest: +ELLIPSIS
'ss_...'

Here, the example network is being uploaded, but this location could also be a folder or a zip containing a custom network snapshot.

5. Ask a question about the snapshot, using one of the loaded templates (``bfq`` holds the questions currently loaded in Pybatfish).
For example here, the question ``IPOwners`` fetches the mapping between IP address, interface, node and VRF for all devices in the network. :

>>> ip_owners_ans = bfq.ipOwners().answer()

``answer()`` runs the question and returns the answer in a JSON format. See the Batfish
`questions directory <https://github.com/batfish/batfish/tree/master/questions>`_
for the set of questions that can be asked and their parameters.

6. To print the answer in a nice table, call ``frame()`` which wraps the answer as `pandas dataframe <https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.html>`_.
Calling `head() <https://pandas.pydata.org/pandas-docs/stable/generated/pandas.DataFrame.head.html>`_
on the dataframe will print the first 5 rows:

>>> ip_owners_ans.frame().head()
         Node      VRF           Interface          IP  Mask  Active
0    as2dist2  default           Loopback0     2.1.3.2    32    True
1    as2dist1  default           Loopback0     2.1.3.1    32    True
2    as2dept1  default  GigabitEthernet1/0  2.34.201.4    24    True
3    as2dept1  default           Loopback0     2.1.1.2    32    True
4  as3border2  default  GigabitEthernet1/0     3.0.2.1    24    True

7. Next, let's ask a question about interfaces. For example, to see all prefixes present on the interface
``GigabitEthernet0/0`` of the node ``as1border1`` we can use the ``interfaceProperties`` question like below:

>>> iface_ans = bfq.interfaceProperties(nodes='as1border1', interfaces='GigabitEthernet0/0', properties='all-prefixes').answer()
>>> iface_ans
                           Interface
    0  as1border1:GigabitEthernet0/0

For additional and more in-depth examples, check out the
`Jupyter Notebooks <https://github.com/batfish/pybatfish/tree/master/jupyter_notebooks>`_.



