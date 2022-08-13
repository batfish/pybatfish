#   Copyright 2022 The Batfish Open Source Project
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

from typing import (  # noqa: F401
    IO,
    TYPE_CHECKING,
    Any,
    Dict,
    List,
    Optional,
    Text,
    Union,
)

import requests
from requests import HTTPError, Response  # noqa: F401
from requests.adapters import HTTPAdapter
from urllib3 import Retry
from urllib3.exceptions import InsecureRequestWarning

import pybatfish
from pybatfish.client.consts import CoordConstsV2
from pybatfish.util import BfJsonEncoder

from .options import Options

if TYPE_CHECKING:
    from pybatfish.client.session import Session  # noqa: F401

# suppress the urllib3 warnings due to old version of urllib3 (inside requests)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# List of HTTP statuses to retry
_STATUS_FORCELIST = [429, 500, 502, 503, 504]

# Create session for existing connection to backend
_requests_session = requests.Session()
_adapter = HTTPAdapter(
    max_retries=Retry(
        total=Options.max_retries_to_connect_to_coordinator,
        connect=Options.max_retries_to_connect_to_coordinator,
        read=Options.max_retries_to_connect_to_coordinator,
        backoff_factor=Options.request_backoff_factor,
        # Retry on all calls, including POST
        method_whitelist=False,
        status_forcelist=_STATUS_FORCELIST,
    )
)
# Configure retries for both http and https requests
_requests_session.mount("http://", _adapter)
_requests_session.mount("https://", _adapter)

# Create request session for that fails fast in case connection is misconfigured
_requests_session_fail_fast = requests.Session()
_adapter_fail_fast = HTTPAdapter(
    max_retries=Retry(
        total=Options.max_initial_tries_to_connect_to_coordinator,
        connect=Options.max_initial_tries_to_connect_to_coordinator,
        read=Options.max_initial_tries_to_connect_to_coordinator,
        backoff_factor=Options.request_backoff_factor,
        # Retry on all calls, including POST
        method_whitelist=False,
        status_forcelist=_STATUS_FORCELIST,
    )
)
# Configure retries for both http and https requests
_requests_session_fail_fast.mount("http://", _adapter_fail_fast)
_requests_session_fail_fast.mount("https://", _adapter_fail_fast)

_encoder = BfJsonEncoder()

__all__ = ["get_api_versions"]


def get_api_versions(session: "Session") -> Optional[Dict[str, Any]]:
    """Gets API version dictionary from backend. If unavailable, returns None"""
    try:
        return _get_dict(session, "/")
    except HTTPError as e:
        if e.response.status_code == 404:
            return None
        raise


def _check_response_status(response: Response) -> None:
    """Rethrows the error thrown by Response.raise_for_status() after including the detailed error message inside Response.text."""
    try:
        response.raise_for_status()
    except HTTPError as e:
        raise HTTPError("{}. {}".format(e, response.text), response=response)


# TODO: factor out common code with restv2helper


def _get(
    session: "Session",
    url_tail: str,
    params: Optional[Dict[str, Any]],
    stream: bool = False,
    fail_fast: bool = False,
) -> Response:
    """Make an HTTP(s) GET request to Batfish coordinator api version service.

    :raises SSLError if SSL connection failed
    :raises ConnectionError if the coordinator is not available
    """
    url = session.get_base_url_api_version_service() + url_tail
    requests_session = _requests_session_fail_fast if fail_fast else _requests_session
    response = requests_session.get(
        url,
        headers=_get_headers(session),
        params=params,
        stream=stream,
        verify=session.verify_ssl_certs,
    )
    _check_response_status(response)
    return response


def _get_dict(
    session: "Session",
    url_tail: str,
    params: Optional[Dict[str, Any]] = None,
    fail_fast: bool = False,
) -> Dict[str, Any]:
    """Make an HTTP(s) GET request to Batfish coordinator that should return a JSON dict.

    :raises SSLError if SSL connection failed
    :raises ConnectionError if the coordinator is not available
    """
    response = _get(session, url_tail, params, fail_fast=fail_fast)
    return dict(response.json())


def _get_headers(session: "Session") -> Dict[str, str]:
    """Get base HTTP headers for v2 requests."""
    return {
        CoordConstsV2.HTTP_HEADER_BATFISH_APIKEY: session.api_key,
        CoordConstsV2.HTTP_HEADER_BATFISH_VERSION: pybatfish.__version__,
    }
