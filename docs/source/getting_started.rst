Setup
=====

Installing Batfish and Pybatfish
--------------------------------

Getting started with Batfish is easy. First, pull and run the latest ``allinone`` Docker container:

.. code-block :: bash

    docker pull batfish/allinone
    docker run --name batfish -v batfish-data:/data -p 8888:8888 -p 9996:9996 batfish/allinone

Then, install Pybatfish using ``pip``:

.. code-block :: bash

    python3 -m pip install --upgrade pybatfish

Pybatfish requires python 3 and we recommend that you install it in a `virtual environment <https://docs.python.org/3/tutorial/venv.html>`_.

Upgrading Batfish and Pybatfish
-------------------------------

In order to upgrade to the latest Docker container, issue these commands on the Batfish server:

.. code-block :: bash

    docker stop batfish
    docker rm batfish
    docker pull batfish/allinone
    docker run --name batfish -v batfish-data:/data -p 8888:8888 -p 9996:9996 batfish/allinone

To upgrade Pybatfish, use the same command as above:

.. code-block :: bash

    python3 -m pip install --upgrade pybatfish

We recommend that you upgrade Batfish and Pybatfish together.
