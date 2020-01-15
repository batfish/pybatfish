Setup
=====

Installing Batfish
------------------

Getting started with Batfish is easy. Just pull and run the latest ``allinone`` Docker container.

.. code-block :: bash

    docker pull batfish/allinone
    docker run --name batfish -v batfish-data:/data -p 8888:8888 -p 9997:9997 -p 9996:9996 batfish/allinone


Upgrading Batfish
-----------------

In order to upgrade to the latest Docker container, issue these commands on the Batfish server

.. code-block :: bash

    docker stop batfish
    docker rm batfish
    docker pull batfish/allinone
    docker run --name batfish -v batfish-data:/data -p 8888:8888 -p 9997:9997 -p 9996:9996 batfish/allinone

Installing (and upgrading) Pybatfish
------------------------------------

Pybatfish requires python 3.
To install Pybatfish using ``pip``, run the following command:

.. code-block :: bash

    python -m pip install --upgrade git+https://github.com/batfish/pybatfish.git

We recommend that you install Pybatfish in a `virtual environment <https://docs.python.org/3/tutorial/venv.html>`_.
