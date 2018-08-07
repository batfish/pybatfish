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

from __future__ import absolute_import, print_function

from typing import Dict  # noqa: F401

import pybatfish
import requests
from pybatfish.client.consts import CoordConsts
from pybatfish.client.session import Session  # noqa: F401
from pybatfish.datamodel.referencelibrary import ReferenceBook
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from urllib3.exceptions import InsecureRequestWarning

from .options import Options

# suppress the urllib3 warnings due to old version of urllib3 (inside requests)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Setup a session, configure retry policy
_requests_session = requests.Session()
# Prefix "http" will cover both "http" & "https"
_requests_session.mount("http", HTTPAdapter(
    max_retries=Retry(
        connect=Options.max_tries_to_connect_to_coordinator,
        backoff_factor=Options.request_backoff_factor)))


def add_node_role_dimension(session, dimension):
    # type: (Session, Dict) -> None
    """Adds a new node role dimension to the active network."""
    urlTail = "/containers/{}/noderoles".format(session.network)
    _post(session, urlTail, dimension)


def add_reference_book(session, book):
    # type: (Session, ReferenceBook) -> None
    """Adds a new reference book to the active network."""
    urlTail = "/containers/{}/referencelibrary".format(session.network)
    _post(session, urlTail, book)


def get_node_role_dimension(session, dimension):
    # type: (Session, str) -> Dict
    """Gets the node role dimension for the active network."""
    if not session.network:
        raise ValueError("Container must be set to get node roles")
    if not dimension:
        raise ValueError("Dimension must be a non-empty string")
    urlTail = "/containers/{}/noderoles/{}".format(session.network, dimension)
    return _get(session, urlTail)


def get_node_roles(session):
    # type: (Session) -> Dict
    """Gets the node roles data for the active network."""
    if not session.network:
        raise ValueError("Container must be set to get node roles")
    urlTail = "/containers/{}/noderoles".format(session.network)
    return _get(session, urlTail)


def get_reference_book(session, book_name):
    # type: (Session, str) -> Dict
    """Gets the reference book for the active network."""
    if not session.network:
        raise ValueError("Container must be set to get a reference book")
    if not book_name:
        raise ValueError("Book name must be a non-empty string")
    urlTail = "/containers/{}/referencelibrary/{}".format(session.network,
                                                          book_name)
    return _get(session, urlTail)


def get_reference_library(session):
    # type: (Session) -> Dict
    """Gets the reference library for the active network."""
    if not session.network:
        raise ValueError("Container must be set to get the reference library")
    urlTail = "/containers/{}/referencelibrary".format(session.network)
    return _get(session, urlTail)


def _get(session, urlTail):
    # type: (Session, str) -> Dict
    """Make an HTTP(s) GET request to Batfish coordinator.

    :raises SSLError if SSL connection failed
    :raises ConnectionError if the coordinator is not available
    """
    headers = {CoordConsts.HTTP_HEADER_BATFISH_APIKEY: session.apiKey,
               CoordConsts.HTTP_HEADER_BATFISH_VERSION: pybatfish.__version__}
    url = session.get_base_url2() + urlTail

    response = requests.get(url, headers=headers, verify=session.verifySslCerts)
    response.raise_for_status()
    return dict(response.json())


def _post(session, urlTail, object):
    # type: (Session, str, Dict) -> None
    """Make an HTTP(s) POST request to Batfish coordinator.

    :raises SSLError if SSL connection failed
    :raises ConnectionError if the coordinator is not available
    """
    headers = {CoordConsts.HTTP_HEADER_BATFISH_APIKEY: session.apiKey,
               CoordConsts.HTTP_HEADER_BATFISH_VERSION: pybatfish.__version__}
    url = session.get_base_url2() + urlTail

    response = requests.post(url, json=object, headers=headers,
                             verify=session.verifySslCerts)
    response.raise_for_status()
    return None
