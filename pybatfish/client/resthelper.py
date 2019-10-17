# coding=utf-8
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

from typing import Any, Dict, Optional, TYPE_CHECKING  # noqa: F401

import requests
from requests import Response  # noqa: F401
from requests.adapters import HTTPAdapter
from requests_toolbelt.multipart.encoder import MultipartEncoder
from urllib3 import Retry
from urllib3.exceptions import InsecureRequestWarning

import pybatfish
from pybatfish.client.consts import CoordConsts
from pybatfish.exception import BatfishException
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


# uncomment line below if you want http capture by fiddler
# _requests_session.proxies = {'http': 'http://127.0.0.1:8888',
#                              'https': 'http://127.0.0.1:8888'}


def get_json_response(session, resource, jsonData=None, useHttpGet=False):
    # type: (Session, str, Optional[Dict], bool) -> Dict[str, Any]
    """Send a request (POST or GET) to Batfish.

    :param session: :py:class:`~pybatfish.client.session.Session` object to use
    :param resource: the API endpoint to call on the Batfish server, string
    :param jsonData: any HTTP POST data to send, as a dictionary
    :param useHttpGet: boolean, whether HTTP GET request should be sent
    """
    if useHttpGet:
        response = _get_data(session, resource)
    else:
        response = _post_data(session, resource, jsonData)

    json_response = response.json()
    if json_response[0] != CoordConsts.SVC_KEY_SUCCESS:
        raise BatfishException(
            "Coordinator returned failure: {}".format(json_response[1])
        )

    return dict(json_response[1])


def _post_data(session, resource, json_data, stream=False):
    # type: (Session, str, Optional[Dict], bool) -> Response
    """Send a POST request."""
    return _make_request(session, resource, json_data, stream, False)


def _get_data(session, resource, stream=False):
    # type: (Session, str, bool) -> Response
    """Send a GET request."""
    return _make_request(session, resource, stream=stream, use_http_get=True)


def _make_request(session, resource, json_data=None, stream=False, use_http_get=False):
    # type: (Session, str, Optional[Dict], bool, bool) -> Response
    """Actually make a HTTP(s) request to Batfish coordinator.

    :raises SSLError if SSL connection failed
    :raises ConnectionError if the coordinator is not available
    """
    url = session.get_url(resource)
    if use_http_get:
        response = _requests_session.get(
            url, verify=session.verify_ssl_certs, stream=stream
        )
    else:
        if json_data is None:
            json_data = {}
        json_data[CoordConsts.SVC_KEY_VERSION] = pybatfish.__version__
        multipart_data = MultipartEncoder(json_data)
        headers = {"Content-Type": multipart_data.content_type}
        response = _requests_session.post(
            url,
            data=multipart_data,
            verify=session.verify_ssl_certs,
            stream=stream,
            headers=headers,
        )
    response.raise_for_status()
    return response
