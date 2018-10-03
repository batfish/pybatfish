**Got questions, feedback, or feature requests? Join our community on [Slack!](https://join.slack.com/t/batfish-org/shared_invite/enQtMzA0Nzg2OTAzNzQ1LTUxOTJlY2YyNTVlNGQ3MTJkOTIwZTU2YjY3YzRjZWFiYzE4ODE5ODZiNjA4NGI5NTJhZmU2ZTllOTMwZDhjMzA)**

# pybatfish

pybatfish is a Python client for [Batfish](https://github.com/batfish/batfish). ![Analytics](https://ga-beacon.appspot.com/UA-100596389-3/open-source/pybatfish?pixel&useReferer)
It allows you to easily get started exploring and validating your network.
Run interactively within a python shell or fully automate your network validation pipeline.


## *Warning: Pybatfish public API is being updated, note that API names and parameters will soon change.*

## Getting started

There are two main options for running pybatfish, detailed below:
* **Docker** - simple, stand-alone setup utilizing Jupyter notebooks to interact with Batfish; good for new users working with Batfish
* **Python** - install pybatfish from source; good for developers or users interested in automation

### Docker Quickstart

Using the [pre-built Docker image](https://hub.docker.com/r/batfish/allinone/) from Docker Hub is a quick and easy way to get started with pybatfish and Batfish, without having to build or install either.  Checkout the [readme](https://github.com/batfish/docker/blob/master/allinone.md) for instructions on using the image.

### Python Setup

#### Prerequisites

1. Access to a running Batfish service (which could be running locally).
See the [Batfish Docker image instructions](https://github.com/batfish/docker/blob/master/batfish.md) or [Batfish setup instructions](https://github.com/batfish/batfish/wiki/Building-and-running-Batfish-service)
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

Once pybatfish is installed, jump right in, exploring with the Jupyter notebooks:
```
pip install jupyter
cd jupyter_notebooks
jupyter notebooks
```

Or see our [full documentation](https://pybatfish.readthedocs.io/en/latest/)
and the [getting started guide](https://pybatfish.readthedocs.io/en/latest/quickstart.html) for more information on how to use pybatfish.

