#   Copyright 2018 The Batfish Open Source Project
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from __future__ import absolute_import, print_function

# To use a consistent encoding
from codecs import open
from os import path
from sys import version_info

# Always prefer setuptools over distutils
from setuptools import find_packages, setup

import pybatfish

here = path.abspath(path.dirname(__file__))
PY2 = version_info[0] == 2

# Capirca dependencies
CAPIRCA_DEPS = ['capirca', 'absl-py>=0.8.0'] + (['ipaddress'] if PY2 else [])

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=pybatfish.__name__,

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=pybatfish.__version__,

    description=pybatfish.__desc__,

    # Set description for PyPI project page
    long_description=long_description,
    long_description_content_type='text/markdown',

    # The project's main homepage.
    url=pybatfish.__url__,

    # Author details
    author='The Batfish Open Source Project',
    author_email='pybatfish-dev@intentionet.com',

    # Choose your license
    license='Apache License 2.0',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',

        # Pick your license as you wish (should match "license" above)
        'License :: Other/Proprietary License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    # What does your project relate to?
    keywords='network configuration verification',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),

    # Alternatively, if you want to distribute just a my_module.py, uncomment
    # this:
    #   py_modules=["my_module"],

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['attrs>=18.1.0',
                      'deepdiff<=3.3.0',
                      'deprecated',
                      'netconan>=0.9.2',
                      'pandas>=0.24.1,<0.25.0',
                      'python-dateutil',
                      'PyYAML',
                      'requests',
                      'requests-toolbelt',
                      'simplejson',
                      'six',
                      ] + (
                         ['backports.tempfile', 'enum34', 'typing']
                         if PY2 else []),

    # List additional groups of dependencies here (e.g. development
    # dependencies). You can install these using the following syntax,
    # for example:
    # $ pip install -e .[dev]
    extras_require={
        'capirca': CAPIRCA_DEPS,
        'dev': ['autoflake',
                'autopep8',
                'check-manifest',
                'coverage',
                'flake8',
                'flake8-docstrings',
                'flake8-import-order',
                'jupyter',
                # brought in by jupyter; needs to work with py3.5
                'matplotlib<3.1.0',
                'nbformat',
                'nbconvert',
                'pydocstyle<4.0.0',
                'pytest>=4.2.0,<5.0.0',
                'pytest-cov',
                'pytz',
                'requests_mock',
                'responses',
                'sphinx>=1.8.0',
                'sphinx_rtd_theme',
                ] + \
               CAPIRCA_DEPS + \
               (['mock'] if PY2 else ['mypy']),
    },

    # List pytest requirements for running unit tests
    setup_requires=['pytest-runner'],

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        # Indicate Pybatfish supports type hinting
        # https://www.python.org/dev/peps/pep-0561/
        'pybatfish': ['py.typed']
    },

    # Although 'package_data' is the preferred approach, in some case you may
    # need to place data files outside of your packages. See:
    # http://docs.python.org/3.4/distutils/setupscript.html#installing-additional-files # noqa
    # In this case, 'data_file' will be installed into '<sys.prefix>/my_data'
    data_files=[],

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'batfish_session': [
            'bf = pybatfish.client.session:Session',
        ],
    },
    # Required for mypy to find Pybatfish (see https://mypy.readthedocs.io/en/latest/installed_packages.html#making-pep-561-compatible-packages)
    zip_safe=False,
)
