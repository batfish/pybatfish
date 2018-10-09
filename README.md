**Got questions, feedback, or feature requests? Join our community on [Slack!](https://join.slack.com/t/batfish-org/shared_invite/enQtMzA0Nzg2OTAzNzQ1LTUxOTJlY2YyNTVlNGQ3MTJkOTIwZTU2YjY3YzRjZWFiYzE4ODE5ODZiNjA4NGI5NTJhZmU2ZTllOTMwZDhjMzA)**

# pybatfish

pybatfish is a Python client for [Batfish](https://github.com/batfish/batfish). ![Analytics](https://ga-beacon.appspot.com/UA-100596389-3/open-source/pybatfish?pixel&useReferer)
It allows you to interactively explore or validate your network and embed validation in your automation pipeline.

#### Note: pybatfish APIs are undergoing revision, and some API names and parameters may change.

## Getting started

There are two options for running pybatfish.

### 1. `Allinone` docker container

This container bundles Batfish and pybatfish. Use this option if you want to just play with [example networks and Jupyter notebooks](jupyter_notebooks).
 
Instructions for running this container are [here](https://github.com/batfish/docker/blob/master/allinone.md).

### 2. Python client

Use this option when you want to analyze your own networks and have access to a running Batfish service (via the [`Batfish` docker container](https://github.com/batfish/docker/blob/master/batfish.md) or [directly from sources](https://github.com/batfish/batfish/wiki/Building-and-running-Batfish-service)).

To install pybatfish, run `pip install .` from the top-level directory of the repository. (We recommend Python 3 as the Python runtime. While Python 2.7 is supported, it is nearing end of life.)

Once pybatfish is installed, you can run the example [Jupyter notebooks](jupyter_notebooks):
```
pip install jupyter
cd jupyter_notebooks
jupyter notebooks
```

You can begin analyzing your own networks by modifying the examples and pointing them at your data. 

Complete documentation of pybatfish APIs is [here](https://pybatfish.readthedocs.io/en/latest/). 
