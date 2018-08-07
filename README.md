# pybatfish

pybatfish is a Python client for [Batfish](https://github.com/batfish/batfish).
It allows you to easily get started exploring and validating your network.
Run interactively within a python shell or fully automate your network validation pipeline.

## *Warning: Pybatfish public API is being updated, note that API names and parameters will soon change.*

## Getting started

### Prerequisites

1. Access to a running Batfish service (which could be running locally).
See [here](https://github.com/batfish/batfish/wiki/Building-and-running-Batfish-service) 
for building and running Batfish service.

2. Python runtime is required. We **strongly** encourage you to use Python 3.
While Python 2.7 is still supported, it is nearing end of life,
and so is our support for it.

3. For interactive use, we **strongly** encourage you to use [IPython](https://ipython.org/)
or a [Jupyter notebook](https://jupyter.org/)


### Installation

#### To install pybatfish from source:

Run the following from the top-level directory of the repository:
```
pip install .
```

To install in development mode, append the -e flag:
```
pip install -e .
```

## Using Pybatfish

See our [full documentation](https://pybatfish.readthedocs.io/en/latest/) 
and the [getting started guide](https://pybatfish.readthedocs.io/en/latest/quickstart.html)

