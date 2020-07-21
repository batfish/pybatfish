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

from unittest.mock import Mock, patch

import pytest
import requests
from requests import HTTPError, Response

from pybatfish.client import restv2helper
from pybatfish.client.options import Options
from pybatfish.client.restv2helper import (
    _adapter,
    _delete,
    _encoder,
    _get,
    _get_headers,
    _post,
    _put,
    _requests_session,
)
from pybatfish.client.session import Session

BASE_URL = "base"


class MockResponse(Response):
    def __init__(self, text):
        super(MockResponse, self).__init__()
        self._text = text

    @property
    def text(self):
        return self._text


@pytest.fixture(scope="module")
def session():
    s = Mock(spec=Session)
    s.get_base_url2.return_value = BASE_URL
    s.api_key = "0000"
    s.verify_ssl_certs = True
    return s


@pytest.fixture(scope="module")
def request_session():
    return Mock(spec=requests.Session)


def test_check_response_status_error():
    response = MockResponse("error detail")
    response.status_code = 400
    with pytest.raises(HTTPError) as e:
        restv2helper._check_response_status(response)
    assert "error detail" in str(e.value)


def test_check_response_status_ok():
    response = MockResponse("no error")
    response.status_code = 200
    restv2helper._check_response_status(response)


def test_delete(session, request_session):
    """Make sure calls to _delete end up using the correct session."""
    resource_url = "/test/url"
    target_url = "base{url}".format(base=BASE_URL, url=resource_url)

    with patch("pybatfish.client.restv2helper._requests_session", request_session):
        # Execute the request
        _delete(session, resource_url)
    # Should pass through to the correct session
    request_session.delete.assert_called_with(
        target_url,
        headers=_get_headers(session),
        params=None,
        verify=session.verify_ssl_certs,
    )


def test_get(session, request_session):
    """Make sure calls to _get end up using the correct session."""
    resource_url = "/test/url"
    target_url = "base{url}".format(base=BASE_URL, url=resource_url)

    with patch("pybatfish.client.restv2helper._requests_session", request_session):
        # Execute the request
        _get(session, resource_url, None)
    # Should pass through to the correct session
    request_session.get.assert_called_with(
        target_url,
        headers=_get_headers(session),
        params=None,
        stream=False,
        verify=session.verify_ssl_certs,
    )


def test_post(session, request_session):
    """Make sure calls to _post end up using the correct session."""
    resource_url = "/test/url"
    target_url = "base{url}".format(base=BASE_URL, url=resource_url)
    obj = "foo"

    with patch("pybatfish.client.restv2helper._requests_session", request_session):
        # Execute the request
        _post(session, resource_url, obj)
    # Should pass through to the correct session
    request_session.post.assert_called_with(
        target_url,
        json=_encoder.default(obj),
        headers=_get_headers(session),
        params=None,
        verify=session.verify_ssl_certs,
    )


def test_put(session, request_session):
    """Make sure calls to _put end up using the correct session."""
    resource_url = "/test/url"
    target_url = "base{url}".format(base=BASE_URL, url=resource_url)

    with patch("pybatfish.client.restv2helper._requests_session", request_session):
        # Execute the request
        _put(session, resource_url)
    # Should pass through to the correct session
    request_session.put.assert_called_with(
        target_url,
        json=None,
        data=None,
        headers=_get_headers(session),
        verify=session.verify_ssl_certs,
        params=None,
    )


def test_session_adapters():
    """Confirm session is configured with correct http and https adapters."""
    http = _requests_session.adapters["http://"]
    https = _requests_session.adapters["https://"]

    assert http == _adapter
    assert https == _adapter
    # Also make sure retries are configured
    retries = _adapter.max_retries
    assert retries.total == Options.max_tries_to_connect_to_coordinator
    # All request types should be retried
    assert not retries.method_whitelist


if __name__ == "__main__":
    pytest.main()
