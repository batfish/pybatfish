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

from typing import Any, Dict, List, Optional, TYPE_CHECKING, Text, Union  # noqa: F401

import requests
from requests import HTTPError, Response  # noqa: F401
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from urllib3.exceptions import InsecureRequestWarning

import pybatfish
from pybatfish.client.consts import CoordConstsV2
from pybatfish.datamodel.referencelibrary import (  # noqa: F401
    NodeRoleDimension,
    NodeRolesData,
    ReferenceBook,
)
from pybatfish.settings.issues import IssueConfig  # noqa: F401
from pybatfish.util import BfJsonEncoder
from .options import Options

if TYPE_CHECKING:
    from pybatfish.client.session import Session  # noqa: F401

# suppress the urllib3 warnings due to old version of urllib3 (inside requests)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Setup a session, configure retry policy
_requests_session = requests.Session()
# Prefix "http" will cover both "http" & "https"
_requests_session.mount(
    "http",
    HTTPAdapter(
        max_retries=Retry(
            connect=Options.max_tries_to_connect_to_coordinator,
            read=Options.max_tries_to_connect_to_coordinator,
            backoff_factor=Options.request_backoff_factor,
        )
    ),
)

_encoder = BfJsonEncoder()

__all__ = [
    "add_issue_config",
    "delete_issue_config",
    "delete_network",
    "delete_node_role_dimension",
    "delete_reference_book",
    "delete_snapshot",
    "delete_snapshot_object",
    "fork_snapshot",
    "get_answer",
    "get_issue_config",
    "get_network",
    "get_network_object",
    "get_node_role_dimension",
    "get_node_roles",
    "get_reference_book",
    "get_reference_library",
    "get_snapshot_input_object",
    "get_snapshot_object",
    "list_networks",
    "list_snapshots",
    "put_network_object",
    "put_node_role_dimension",
    "put_reference_book",
    "put_snapshot_object",
    "read_question_settings",
    "write_question_settings",
]


def add_issue_config(session, issue_config):
    # type: (Session, IssueConfig) -> None
    """Adds the issue configuration to the active network."""
    if not session.network:
        raise ValueError("Network must be set to add issue config")
    url_tail = "/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_SETTINGS,
        CoordConstsV2.RSC_ISSUES,
    )
    _post(session, url_tail, issue_config)


def delete_issue_config(session, major, minor):
    # type: (Session, str, str) -> None
    if not session.network:
        raise ValueError("Network must be set to delete issue config")
    if not major:
        raise ValueError("Major issue type must be set to delete issue config")
    if not minor:
        raise ValueError("Minor issue type must be set to delete issue config")
    url_tail = "/{}/{}/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_SETTINGS,
        CoordConstsV2.RSC_ISSUES,
        major,
        minor,
    )
    return _delete(session, url_tail)


def list_networks(session):
    # type: (Session) -> List[Dict[str, Any]]
    """List the networks in the current session."""
    url_tail = "/{}".format(CoordConstsV2.RSC_NETWORKS)
    return _get_list(session, url_tail)


def list_snapshots(session, verbose):
    # type: (Session, bool) -> Union[List[str], List[Dict[str,str]]]
    """List the snapshots in the current network."""
    if not session.network:
        raise ValueError("Network must be set to list snapshots")
    url_tail = "/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS, session.network, CoordConstsV2.RSC_SNAPSHOTS
    )
    return _get_list(session, url_tail, {CoordConstsV2.QP_VERBOSE: verbose})


def fork_snapshot(session, obj):
    # type: (Session, Dict[str, Any]) -> None
    if not session.network:
        raise ValueError("Network must be set to fork a snapshot")
    url_tail = "/{}/{}/{}:{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_SNAPSHOTS,
        CoordConstsV2.RSC_FORK,
    )
    return _post(session, url_tail, obj)


def delete_network(session, name):
    # type: (Session, Text) -> None
    """Deletes the network with the given name."""
    url_tail = "/{}/{}".format(CoordConstsV2.RSC_NETWORKS, name)
    return _delete(session, url_tail)


def delete_network_object(session, key):
    # type: (Session, Text) -> None
    """Deletes extended object with given key for the current network."""
    url_tail = "/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS, session.network, CoordConstsV2.RSC_OBJECTS
    )
    return _delete(session, url_tail, {CoordConstsV2.QP_KEY: key})


def delete_node_role_dimension(session, dimension):
    # type: (Session, str) -> None
    """Deletes the definition of the given node role dimension for the active network."""
    if not session.network:
        raise ValueError("Network must be set to delete a node role dimension")
    if not dimension:
        raise ValueError("Dimension must be a non-empty string")
    url_tail = "/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_NODE_ROLES,
        dimension,
    )
    return _delete(session, url_tail)


def delete_reference_book(session, book_name):
    # type: (Session, str) -> None
    """Deletes the definition of the given reference book name."""
    if not session.network:
        raise ValueError("Network must be set to delete a reference book")
    if not book_name:
        raise ValueError("Book name must be a non-empty string")
    url_tail = "/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_REFERENCE_LIBRARY,
        book_name,
    )
    return _delete(session, url_tail)


def delete_snapshot(session, snapshot, network):
    # type: (Session, Text, Text) -> None
    """Deletes the snapshot with the given name."""
    url_tail = "/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS, network, CoordConstsV2.RSC_SNAPSHOTS, snapshot
    )
    return _delete(session, url_tail)


def delete_snapshot_object(session, key, snapshot=None):
    # type: (Session, str, Optional[str]) -> None
    """Deletes extended object with given key for the current snapshot."""
    url_tail = "/{}/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_SNAPSHOTS,
        session.get_snapshot(snapshot),
        CoordConstsV2.RSC_OBJECTS,
    )
    _delete(session, url_tail, {CoordConstsV2.QP_KEY: key})


def get_answer(session, question, params):
    # type: (Session, str, Dict[str, Optional[str]]) -> Dict[str, Any]
    """Get answer for the specified question."""
    url_tail = "/{}/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_QUESTIONS,
        question,
        CoordConstsV2.RSC_ANSWER,
    )
    return _get_dict(session, url_tail, params)


def get_issue_config(session, major, minor):
    # type: (Session, str, str) -> Dict
    if not session.network:
        raise ValueError("Network must be set to get issue config")
    if not major:
        raise ValueError("Major issue type must be set to get issue config")
    if not minor:
        raise ValueError("Minor issue type must be set to get issue config")
    url_tail = "/{}/{}/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_SETTINGS,
        CoordConstsV2.RSC_ISSUES,
        major,
        minor,
    )
    return _get_dict(session, url_tail)


def get_network(session, network):
    # type: (Session, str) -> Dict[str, Any]
    """Gets information about the specified network."""
    url_tail = "/{}/{}".format(CoordConstsV2.RSC_NETWORKS, network)
    return _get_dict(session, url_tail)


def get_network_object(session, key):
    # type: (Session, Text) -> Any
    """Gets extended object with given key for the current network."""
    url_tail = "/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS, session.network, CoordConstsV2.RSC_OBJECTS
    )
    return _get_stream(session, url_tail, {CoordConstsV2.QP_KEY: key})


def get_snapshot_input_object(session, key, snapshot=None):
    # type: (Session, Text, Optional[Text]) -> Any
    """Gets input object with given key for the current snapshot."""
    url_tail = "/{}/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_SNAPSHOTS,
        session.get_snapshot(snapshot),
        CoordConstsV2.RSC_INPUT,
    )
    return _get_stream(session, url_tail, {CoordConstsV2.QP_KEY: key})


def get_snapshot_object(session, key, snapshot=None):
    # type: (Session, Text, Optional[Text]) -> Any
    """Gets extended object with given key for the current snapshot."""
    url_tail = "/{}/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_SNAPSHOTS,
        session.get_snapshot(snapshot),
        CoordConstsV2.RSC_OBJECTS,
    )
    return _get_stream(session, url_tail, {CoordConstsV2.QP_KEY: key})


def get_node_role_dimension(session, dimension):
    # type: (Session, str) -> Dict
    """Gets the defintion of the given node role dimension for the active network."""
    if not session.network:
        raise ValueError("Network must be set to get node roles")
    if not dimension:
        raise ValueError("Dimension must be a non-empty string")
    url_tail = "/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_NODE_ROLES,
        dimension,
    )
    return _get_dict(session, url_tail)


def get_node_roles(session):
    # type: (Session) -> Dict
    """Gets the definitions of node roles for the active network."""
    if not session.network:
        raise ValueError("Network must be set to get node roles")
    url_tail = "/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS, session.network, CoordConstsV2.RSC_NODE_ROLES
    )
    return _get_dict(session, url_tail)


def get_reference_book(session, book_name):
    # type: (Session, str) -> Dict
    """Gets the reference book for the active network."""
    if not session.network:
        raise ValueError("Network must be set to get a reference book")
    if not book_name:
        raise ValueError("Book name must be a non-empty string")
    url_tail = "/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_REFERENCE_LIBRARY,
        book_name,
    )
    return _get_dict(session, url_tail)


def get_reference_library(session):
    # type: (Session) -> Dict
    """Gets the reference library for the active network."""
    if not session.network:
        raise ValueError("Network must be set to get the reference library")
    url_tail = "/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS, session.network, CoordConstsV2.RSC_REFERENCE_LIBRARY
    )
    return _get_dict(session, url_tail)


def get_snapshot_inferred_node_roles(session, snapshot=None):
    # type: (Session, Optional[str]) -> Dict
    """Gets suggested definitions and hypothetical assignments of node roles for the active network and snapshot."""
    if not session.network:
        raise ValueError("Network must be set to get node roles")
    url_tail = "/{}/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_SNAPSHOTS,
        session.get_snapshot(snapshot),
        CoordConstsV2.RSC_INFERRED_NODE_ROLES,
    )
    return _get_dict(session, url_tail)


def get_snapshot_inferred_node_role_dimension(session, dimension, snapshot=None):
    # type: (Session, str, Optional[str]) -> Dict
    """Gets the suggested definition and hypothetical assignments of node roles for the given inferred dimension for the active network and snapshot."""
    if not session.network:
        raise ValueError("Network must be set to get node roles")
    url_tail = "/{}/{}/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_SNAPSHOTS,
        session.get_snapshot(snapshot),
        CoordConstsV2.RSC_INFERRED_NODE_ROLES,
        dimension,
    )
    return _get_dict(session, url_tail)


def get_snapshot_node_roles(session, snapshot=None):
    # type: (Session, Optional[str]) -> Dict
    """Gets the definitions and assignments of node roles for the active network and snapshot."""
    if not session.network:
        raise ValueError("Network must be set to get node roles")
    url_tail = "/{}/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_SNAPSHOTS,
        session.get_snapshot(snapshot),
        CoordConstsV2.RSC_NODE_ROLES,
    )
    return _get_dict(session, url_tail)


def get_snapshot_node_role_dimension(session, dimension, snapshot=None):
    # type: (Session, str, Optional[str]) -> Dict
    """Gets the definition and assignments of node roles for the given dimension for the active network and snapshot."""
    if not session.network:
        raise ValueError("Network must be set to get node roles")
    url_tail = "/{}/{}/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_SNAPSHOTS,
        session.get_snapshot(snapshot),
        CoordConstsV2.RSC_NODE_ROLES,
        dimension,
    )
    return _get_dict(session, url_tail)


def get_work_log(session, snapshot, work_id):
    # type: (Session, Optional[str], str) -> Text
    """Retrieve the log for a work item with a given ID."""
    if not session.network:
        raise ValueError("Network must be set to get node roles")

    url_tail = "/{}/{}/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_SNAPSHOTS,
        session.get_snapshot(snapshot),
        CoordConstsV2.RSC_WORK_LOG,
        work_id,
    )

    return _get(session, url_tail, dict()).text


def get_component_versions(session):
    # type: (Session) -> Dict[str, Any]
    """Get a dictionary of backend components (e.g. Batfish, Z3) and their versions."""
    return _get_dict(session, "/version")


def get_question_templates(session: "Session", verbose: bool) -> Dict:
    """Get question templates from the backend.

    :param verbose: if True, even hidden questions will be returned.
    """
    return _get_dict(
        session,
        url_tail="/{}".format(CoordConstsV2.RSC_QUESTION_TEMPLATES),
        params={CoordConstsV2.QP_VERBOSE: verbose},
    )


def put_network_object(session, key, data):
    # type: (Session, Text, Any) -> None
    """Put data as extended object with given key for the current network."""
    url_tail = "/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS, session.network, CoordConstsV2.RSC_OBJECTS
    )
    _put_stream(session, url_tail, data, {CoordConstsV2.QP_KEY: key})


def put_node_role_dimension(session, dimension):
    # type: (Session, NodeRoleDimension) -> None
    """Adds a new node role dimension to the active network."""
    if not session.network:
        raise ValueError("Network must be set to add node role dimension")
    url_tail = "/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_NODE_ROLES,
        dimension.name,
    )
    _put_json(session, url_tail, dimension)


def put_node_roles(session, node_roles_data):
    # type: (Session, NodeRolesData) -> None
    """Writes the definitions of node roles for the active network. Completely replaces any existing definitions."""
    if not session.network:
        raise ValueError("Network must be set to get node roles")
    url_tail = "/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS, session.network, CoordConstsV2.RSC_NODE_ROLES
    )
    return _put_json(session, url_tail, node_roles_data)


def put_reference_book(session, book):
    # type: (Session, ReferenceBook) -> None
    """Put a reference book to the active network."""
    if not session.network:
        raise ValueError("Network must be set to add reference book")
    url_tail = "/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_REFERENCE_LIBRARY,
        book.name,
    )
    _put_json(session, url_tail, book)


def put_snapshot_object(session, key, data, snapshot=None):
    # type: (Session, Text, Any, Optional[Text]) -> None
    """Put data as extended object with given key for the current snapshot."""
    url_tail = "/{}/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_SNAPSHOTS,
        session.get_snapshot(snapshot),
        CoordConstsV2.RSC_OBJECTS,
    )
    _put_stream(session, url_tail, data, {CoordConstsV2.QP_KEY: key})


def read_question_settings(session, question_class, json_path):
    # type: (Session, str, Optional[List[str]]) -> Dict[str, Any]
    """Retrieves the settings for a question class."""
    if not session.network:
        raise ValueError("Network must be set to read question class settings")
    json_path_tail = "/".join(json_path) if json_path else ""
    url_tail = "/{}/{}/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_SETTINGS,
        CoordConstsV2.RSC_QUESTIONS,
        question_class,
        json_path_tail,
    )
    return _get_dict(session, url_tail)


def write_question_settings(session, settings, question_class, json_path):
    # type: (Session, Dict[str, Any], str, Optional[List[str]]) -> None
    """Writes settings for a question class."""
    if not session.network:
        raise ValueError("Network must be set to write question class settings")
    json_path_tail = "/".join(json_path) if json_path else ""
    url_tail = "/{}/{}/{}/{}/{}/{}".format(
        CoordConstsV2.RSC_NETWORKS,
        session.network,
        CoordConstsV2.RSC_SETTINGS,
        CoordConstsV2.RSC_QUESTIONS,
        question_class,
        json_path_tail,
    )
    _put_json(session, url_tail, settings)


def _check_response_status(response):
    # type: (Response) -> None
    """Rethrows the error thrown by Response.raise_for_status() after including the detailed error message inside Response.text."""
    try:
        response.raise_for_status()
    except HTTPError as e:
        raise HTTPError("{}. {}".format(e, response.text), response=response)


def _delete(
    session: "Session", url_tail: str, params: Optional[Dict[str, Any]] = None
) -> None:
    """Make an HTTP(s) DELETE request to Batfish coordinator.

    :raises SSLError if SSL connection failed
    :raises ConnectionError if the coordinator is not available
    """
    headers = {
        CoordConstsV2.HTTP_HEADER_BATFISH_APIKEY: session.api_key,
        CoordConstsV2.HTTP_HEADER_BATFISH_VERSION: pybatfish.__version__,
    }
    url = session.get_base_url2() + url_tail
    response = requests.delete(
        url, headers=headers, params=params, verify=session.verify_ssl_certs
    )
    _check_response_status(response)


def _get(session, url_tail, params, stream=False):
    # type: (Session, str, Optional[Dict[str, Any]], bool) -> Response
    """Make an HTTP(s) GET request to Batfish coordinator.

    :raises SSLError if SSL connection failed
    :raises ConnectionError if the coordinator is not available
    """
    headers = {
        CoordConstsV2.HTTP_HEADER_BATFISH_APIKEY: session.api_key,
        CoordConstsV2.HTTP_HEADER_BATFISH_VERSION: pybatfish.__version__,
    }
    url = session.get_base_url2() + url_tail
    response = requests.get(
        url,
        headers=headers,
        params=params,
        stream=stream,
        verify=session.verify_ssl_certs,
    )
    _check_response_status(response)
    return response


def _get_dict(session, url_tail, params=None):
    # type: (Session, str, Optional[Dict[str, Any]]) -> Dict[str, Any]
    """Make an HTTP(s) GET request to Batfish coordinator that should return a JSON dict.

    :raises SSLError if SSL connection failed
    :raises ConnectionError if the coordinator is not available
    """
    response = _get(session, url_tail, params)
    return dict(response.json())


def _get_list(
    session: "Session", url_tail: str, params: Optional[Dict[str, Any]] = None
) -> List[Any]:
    """Make an HTTP(s) GET request to Batfish coordinator that should return a JSON list.

    :raises SSLError if SSL connection failed
    :raises ConnectionError if the coordinator is not available
    """
    response = _get(session, url_tail, params)
    return list(response.json())


def _get_stream(
    session: "Session", url_tail: str, params: Optional[Dict[str, Any]] = None
) -> Any:
    """Make an HTTP(s) GET request to Batfish coordinator that should return a raw stream.

    :raises SSLError if SSL connection failed
    :raises ConnectionError if the coordinator is not available
    """
    response = _get(session, url_tail, params, stream=True)
    response.raw.decode_content = True
    return response.raw


def _post(
    session: "Session", url_tail: str, obj: Any, params: Optional[Dict[str, Any]] = None
) -> None:
    """Make an HTTP(s) POST request to Batfish coordinator.

    :raises SSLError if SSL connection failed
    :raises ConnectionError if the coordinator is not available
    """
    headers = {
        CoordConstsV2.HTTP_HEADER_BATFISH_APIKEY: session.api_key,
        CoordConstsV2.HTTP_HEADER_BATFISH_VERSION: pybatfish.__version__,
    }
    url = session.get_base_url2() + url_tail
    response = requests.post(
        url,
        json=_encoder.default(obj),
        headers=headers,
        params=params,
        verify=session.verify_ssl_certs,
    )
    _check_response_status(response)
    return None


def _put(session, url_tail, params=None, json=None, stream=None):
    # type: (Session, str, Optional[Dict[str, Any]], Optional[Any], Optional[Any]) -> None
    """Make an HTTP(s) PUT request to Batfish coordinator.

    :raises SSLError if SSL connection failed
    :raises ConnectionError if the coordinator is not available
    """
    headers = {
        CoordConstsV2.HTTP_HEADER_BATFISH_APIKEY: session.api_key,
        CoordConstsV2.HTTP_HEADER_BATFISH_VERSION: pybatfish.__version__,
    }
    if stream:
        headers["Content-Type"] = "application/octet-stream"
    url = session.get_base_url2() + url_tail
    response = requests.put(
        url,
        json=json,
        data=stream,
        headers=headers,
        verify=session.verify_ssl_certs,
        params=params,
    )
    _check_response_status(response)
    return None


def _put_json(
    session: "Session", url_tail: str, obj: Any, params: Optional[Dict[str, Any]] = None
) -> None:
    """Make an HTTP(s) PUT request to Batfish coordinator.

    :raises SSLError if SSL connection failed
    :raises ConnectionError if the coordinator is not available
    """
    _put(session, url_tail, params=params, json=_encoder.default(obj))


def _put_stream(
    session: "Session",
    url_tail: str,
    stream: Any,
    params: Optional[Dict[str, Any]] = None,
) -> None:
    """Make an HTTP(s) PUT request to Batfish coordinator.

    :raises SSLError if SSL connection failed
    :raises ConnectionError if the coordinator is not available
    """
    _put(session, url_tail, params=params, stream=stream)
