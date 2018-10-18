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

from typing import Any, Dict, List, Optional  # noqa: F401

import requests
from requests import HTTPError, Response  # noqa: F401
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from urllib3.exceptions import InsecureRequestWarning

import pybatfish
from pybatfish.client.consts import CoordConstsV2
from pybatfish.client.session import Session  # noqa: F401
from pybatfish.datamodel.referencelibrary import (  # noqa: F401
    NodeRoleDimension,
    NodeRolesData,
    ReferenceBook)
from pybatfish.settings.issues import IssueConfig  # noqa: F401
from pybatfish.util import BfJsonEncoder
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

_encoder = BfJsonEncoder()

__all__ = [
    'add_issue_config',
    'add_node_role_dimension',
    'add_reference_book',
    'delete_issue_config',
    'fork_snapshot',
    'get_issue_config',
    'get_network',
    'get_node_role_dimension',
    'get_node_roles',
    'get_reference_book',
    'get_reference_library',
    'read_question_settings',
    'write_question_settings'
]


def add_issue_config(session, issue_config):
    # type: (Session, IssueConfig) -> None
    """Adds the issue configuration to the active network."""
    if not session.network:
        raise ValueError("Network must be set to add issue config")
    url_tail = "/{}/{}/{}/{}".format(CoordConstsV2.RSC_NETWORKS,
                                     session.network,
                                     CoordConstsV2.RSC_SETTINGS,
                                     CoordConstsV2.RSC_ISSUES)
    _post(session, url_tail, issue_config)


def add_node_role_dimension(session, dimension):
    # type: (Session, NodeRoleDimension) -> None
    """Adds a new node role dimension to the active network."""
    if not session.network:
        raise ValueError("Network must be set to add node role dimension")
    url_tail = "/{}/{}/{}".format(CoordConstsV2.RSC_NETWORKS, session.network,
                                  CoordConstsV2.RSC_NODE_ROLES)
    _post(session, url_tail, dimension)


def add_reference_book(session, book):
    # type: (Session, ReferenceBook) -> None
    """Adds a new reference book to the active network."""
    if not session.network:
        raise ValueError("Network must be set to add reference book")
    url_tail = "/{}/{}/{}".format(CoordConstsV2.RSC_NETWORKS, session.network,
                                  CoordConstsV2.RSC_REFERENCE_LIBRARY)
    _post(session, url_tail, book)


def delete_issue_config(session, major, minor):
    # type: (Session, str, str) -> None
    if not session.network:
        raise ValueError("Network must be set to delete issue config")
    if not major:
        raise ValueError("Major issue type must be set to delete issue config")
    if not minor:
        raise ValueError("Minor issue type must be set to delete issue config")
    url_tail = "/{}/{}/{}/{}/{}/{}".format(CoordConstsV2.RSC_NETWORKS,
                                           session.network,
                                           CoordConstsV2.RSC_SETTINGS,
                                           CoordConstsV2.RSC_ISSUES,
                                           major,
                                           minor)
    return _delete(session, url_tail)


def fork_snapshot(session, obj):
    # type: (Session, Dict[str, Any]) -> None
    if not session.network:
        raise ValueError("Network must be set to fork a snapshot")
    url_tail = "/{}/{}/{}:{}".format(CoordConstsV2.RSC_NETWORKS,
                                     session.network,
                                     CoordConstsV2.RSC_SNAPSHOTS,
                                     CoordConstsV2.RSC_FORK)
    return _post(session, url_tail, obj)


def delete_node_role_dimension(session, dimension):
    # type: (Session, str) -> None
    """Deletes the definition of the given node role dimension for the active network."""
    if not session.network:
        raise ValueError("Network must be set to get node roles")
    if not dimension:
        raise ValueError("Dimension must be a non-empty string")
    url_tail = "/{}/{}/{}/{}".format(CoordConstsV2.RSC_NETWORKS,
                                     session.network,
                                     CoordConstsV2.RSC_NODE_ROLES,
                                     dimension)
    return _delete(session, url_tail)


def get_issue_config(session, major, minor):
    # type: (Session, str, str) -> Dict
    if not session.network:
        raise ValueError("Network must be set to get issue config")
    if not major:
        raise ValueError("Major issue type must be set to get issue config")
    if not minor:
        raise ValueError("Minor issue type must be set to get issue config")
    url_tail = "/{}/{}/{}/{}/{}/{}".format(CoordConstsV2.RSC_NETWORKS,
                                           session.network,
                                           CoordConstsV2.RSC_SETTINGS,
                                           CoordConstsV2.RSC_ISSUES,
                                           major,
                                           minor)
    return _get(session, url_tail)


def get_network(session, network):
    # type: (Session, str) -> Dict[str, Any]
    """Gets information about the specified network."""
    url_tail = "/{}/{}".format(CoordConstsV2.RSC_NETWORKS, network)
    return _get(session, url_tail)


def get_node_role_dimension(session, dimension):
    # type: (Session, str) -> Dict
    """Gets the defintion of the given node role dimension for the active network."""
    if not session.network:
        raise ValueError("Network must be set to get node roles")
    if not dimension:
        raise ValueError("Dimension must be a non-empty string")
    url_tail = "/{}/{}/{}/{}".format(CoordConstsV2.RSC_NETWORKS,
                                     session.network,
                                     CoordConstsV2.RSC_NODE_ROLES,
                                     dimension)
    return _get(session, url_tail)


def get_node_roles(session):
    # type: (Session) -> Dict
    """Gets the definitions of node roles for the active network."""
    if not session.network:
        raise ValueError("Network must be set to get node roles")
    url_tail = "/{}/{}/{}".format(CoordConstsV2.RSC_NETWORKS, session.network,
                                  CoordConstsV2.RSC_NODE_ROLES)
    return _get(session, url_tail)


def get_reference_book(session, book_name):
    # type: (Session, str) -> Dict
    """Gets the reference book for the active network."""
    if not session.network:
        raise ValueError("Network must be set to get a reference book")
    if not book_name:
        raise ValueError("Book name must be a non-empty string")
    url_tail = "/{}/{}/{}/{}".format(CoordConstsV2.RSC_NETWORKS,
                                     session.network,
                                     CoordConstsV2.RSC_REFERENCE_LIBRARY,
                                     book_name)
    return _get(session, url_tail)


def get_reference_library(session):
    # type: (Session) -> Dict
    """Gets the reference library for the active network."""
    if not session.network:
        raise ValueError("Network must be set to get the reference library")
    url_tail = "/{}/{}/{}".format(CoordConstsV2.RSC_NETWORKS, session.network,
                                  CoordConstsV2.RSC_REFERENCE_LIBRARY)
    return _get(session, url_tail)


def get_snapshot_inferred_node_roles(session):
    # type: (Session) -> Dict
    """Gets suggested definitions and hypothetical assignments of node roles for the active network and snapshot."""
    if not session.network:
        raise ValueError("Network must be set to get node roles")
    url_tail = "/{}/{}/{}/{}/{}".format(CoordConstsV2.RSC_NETWORKS,
                                        session.network,
                                        CoordConstsV2.RSC_SNAPSHOTS,
                                        session.baseSnapshot,
                                        CoordConstsV2.RSC_INFERRED_NODE_ROLES)
    return _get(session, url_tail)


def get_snapshot_inferred_node_role_dimension(session, dimension):
    # type: (Session, str) -> Dict
    """Gets the suggested definition and hypothetical assignments of node roles for the given inferred dimension for the active network and snapshot."""
    if not session.network:
        raise ValueError("Network must be set to get node roles")
    url_tail = "/{}/{}/{}/{}/{}/{}".format(CoordConstsV2.RSC_NETWORKS,
                                           session.network,
                                           CoordConstsV2.RSC_SNAPSHOTS,
                                           session.baseSnapshot,
                                           CoordConstsV2.RSC_INFERRED_NODE_ROLES,
                                           dimension)
    return _get(session, url_tail)


def get_snapshot_node_roles(session):
    # type: (Session) -> Dict
    """Gets the definitions and assignments of node roles for the active network and snapshot."""
    if not session.network:
        raise ValueError("Network must be set to get node roles")
    url_tail = "/{}/{}/{}/{}/{}".format(CoordConstsV2.RSC_NETWORKS,
                                        session.network,
                                        CoordConstsV2.RSC_SNAPSHOTS,
                                        session.baseSnapshot,
                                        CoordConstsV2.RSC_NODE_ROLES)
    return _get(session, url_tail)


def get_snapshot_node_role_dimension(session, dimension):
    # type: (Session, str) -> Dict
    """Gets the definition and assignments of node roles for the given dimension for the active network and snapshot."""
    if not session.network:
        raise ValueError("Network must be set to get node roles")
    url_tail = "/{}/{}/{}/{}/{}/{}".format(CoordConstsV2.RSC_NETWORKS,
                                           session.network,
                                           CoordConstsV2.RSC_SNAPSHOTS,
                                           session.baseSnapshot,
                                           CoordConstsV2.RSC_NODE_ROLES,
                                           dimension)
    return _get(session, url_tail)


def put_node_roles(session, node_roles_data):
    # type: (Session, NodeRolesData) -> None
    """Writes the definitions of node roles for the active network. Completely replaces any existing definitions."""
    if not session.network:
        raise ValueError("Network must be set to get node roles")
    url_tail = "/{}/{}/{}".format(CoordConstsV2.RSC_NETWORKS, session.network,
                                  CoordConstsV2.RSC_NODE_ROLES)
    return _put(session, url_tail, node_roles_data)


def read_question_settings(session, question_class, json_path):
    # type: (Session, str, Optional[List[str]]) -> Dict[str, Any]
    """Retrieves the settings for a question class."""
    if not session.network:
        raise ValueError("Network must be set to read question class settings")
    json_path_tail = '/'.join(json_path) if json_path else ""
    url_tail = "/{}/{}/{}/{}/{}/{}".format(CoordConstsV2.RSC_NETWORKS,
                                           session.network,
                                           CoordConstsV2.RSC_SETTINGS,
                                           CoordConstsV2.RSC_QUESTIONS,
                                           question_class,
                                           json_path_tail)
    return _get(session, url_tail)


def write_question_settings(session, settings, question_class, json_path):
    # type: (Session, Dict[str, Any], str, Optional[List[str]]) -> None
    """Writes settings for a question class."""
    if not session.network:
        raise ValueError("Network must be set to write question class settings")
    json_path_tail = '/'.join(json_path) if json_path else ""
    url_tail = "/{}/{}/{}/{}/{}/{}".format(CoordConstsV2.RSC_NETWORKS,
                                           session.network,
                                           CoordConstsV2.RSC_SETTINGS,
                                           CoordConstsV2.RSC_QUESTIONS,
                                           question_class,
                                           json_path_tail)
    _put(session, url_tail, settings)


def _check_response_status(response):
    # type: (Response) -> None
    """Rethrows the error thrown by Response.raise_for_status() after including the detailed error message inside Response.text."""
    try:
        response.raise_for_status()
    except HTTPError as e:
        raise HTTPError("{}. {}".format(e, response.text), response=response)


def _delete(session, url_tail):
    # type: (Session, str) -> None
    """Make an HTTP(s) DELETE request to Batfish coordinator.

    :raises SSLError if SSL connection failed
    :raises ConnectionError if the coordinator is not available
    """
    headers = {CoordConstsV2.HTTP_HEADER_BATFISH_APIKEY: session.apiKey,
               CoordConstsV2.HTTP_HEADER_BATFISH_VERSION: pybatfish.__version__}
    url = session.get_base_url2() + url_tail

    response = requests.delete(url, headers=headers,
                               verify=session.verifySslCerts)
    _check_response_status(response)


def _get(session, url_tail):
    # type: (Session, str) -> Dict[str, Any]
    """Make an HTTP(s) GET request to Batfish coordinator.

    :raises SSLError if SSL connection failed
    :raises ConnectionError if the coordinator is not available
    """
    headers = {CoordConstsV2.HTTP_HEADER_BATFISH_APIKEY: session.apiKey,
               CoordConstsV2.HTTP_HEADER_BATFISH_VERSION: pybatfish.__version__}
    url = session.get_base_url2() + url_tail

    response = requests.get(url, headers=headers, verify=session.verifySslCerts)
    _check_response_status(response)
    return dict(response.json())


def _post(session, url_tail, obj):
    # type: (Session, str, Any) -> None
    """Make an HTTP(s) POST request to Batfish coordinator.

    :raises SSLError if SSL connection failed
    :raises ConnectionError if the coordinator is not available
    """
    headers = {CoordConstsV2.HTTP_HEADER_BATFISH_APIKEY: session.apiKey,
               CoordConstsV2.HTTP_HEADER_BATFISH_VERSION: pybatfish.__version__}
    url = session.get_base_url2() + url_tail

    response = requests.post(url,
                             json=_encoder.default(obj),
                             headers=headers,
                             verify=session.verifySslCerts)
    _check_response_status(response)
    return None


def _put(session, url_tail, obj):
    # type: (Session, str, Any) -> None
    """Make an HTTP(s) PUT request to Batfish coordinator.

    :raises SSLError if SSL connection failed
    :raises ConnectionError if the coordinator is not available
    """
    headers = {CoordConstsV2.HTTP_HEADER_BATFISH_APIKEY: session.apiKey,
               CoordConstsV2.HTTP_HEADER_BATFISH_VERSION: pybatfish.__version__}
    url = session.get_base_url2() + url_tail

    response = requests.put(url,
                            json=_encoder.default(obj),
                            headers=headers,
                            verify=session.verifySslCerts)
    _check_response_status(response)
    return None
