**Got questions, feedback, or feature requests? Join our community on [Slack!](https://join.slack.com/t/batfish-org/shared_invite/enQtMzA0Nzg2OTAzNzQ1LTUxOTJlY2YyNTVlNGQ3MTJkOTIwZTU2YjY3YzRjZWFiYzE4ODE5ODZiNjA4NGI5NTJhZmU2ZTllOTMwZDhjMzA)**

# pybatfish

pybatfish is a Python client for [Batfish](https://github.com/batfish/batfish). ![Analytics](https://ga-beacon.appspot.com/UA-100596389-3/open-source/pybatfish?pixel&useReferer)
It allows you to easily get started exploring and validating your network.
Run interactively within a python shell or fully automate your network validation pipeline.


## *Warning: Pybatfish public API is being updated, note that API names and parameters will soon change.*

## Getting started

There are two main options for utilizing pybatfish, detailed below:
* **Docker** - a docker container that combines Batfish with Pybatfish SDK and Jupyter notebooks (iPython notebook). This container has example networks and notebooks, so it is recommended for new users working with Batfish and Pybatfish
* **Python** - install pybatfish from source; recommended for developers interested in contributing to Batfish/Pybatfish or building network automation solutions.

### Docker Quickstart

Using the [pre-built Docker image](https://hub.docker.com/r/batfish/allinone/) from Docker Hub is a quick and easy way to get started with pybatfish and Batfish, without having to build or install either.  Checkout the [readme](https://github.com/batfish/docker/blob/master/allinone.md) for instructions on using the image.

### Python Setup

#### Prerequisites

1. Access to a running Batfish service (which could be running locally).
See the [Batfish Docker image instructions](https://github.com/batfish/docker/blob/master/batfish.md) 
for running Batfish service.

2. Python runtime is required. We **strongly** encourage you to use Python 3.
While Python 2.7 is still supported, it is nearing end of life,
and so is our support for it.

3. For interactive use, we **strongly** encourage you to use [IPython](https://ipython.org/)
or a [Jupyter notebook](https://jupyter.org/)


#### Installation

##### To install pybatfish from source:

Run the following from the top-level directory of the repository:
```
pip install .
```

To install in development mode, append the -e flag:
```
pip install -e .
```

#### Using pybatfish

Once pybatfish is installed, get started right away with the [Jupyter notebooks](https://github.com/batfish/pybatfish/blob/master/jupyter_notebooks/Getting%20started%20with%20Batfish.ipynb):
```
pip install jupyter
cd jupyter_notebooks
jupyter notebooks
```

Or see our [pybatfish documentation](https://pybatfish.readthedocs.io/en/latest/)
and the [introduction to pybatfish](https://pybatfish.readthedocs.io/en/latest/quickstart.html) for more information on how to use pybatfish.

