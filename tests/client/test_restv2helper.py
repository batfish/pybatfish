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
import io
import json
from unittest.mock import Mock, patch

import pytest
import requests
from requests import HTTPError, Response

from pybatfish.client import restv2helper
from pybatfish.client.consts import CoordConsts
from pybatfish.client.options import Options
from pybatfish.client.restv2helper import (
    _adapter,
    _adapter_fail_fast,
    _delete,
    _encoder,
    _get,
    _get_headers,
    _post,
    _put,
    _requests_session,
    _requests_session_fail_fast,
    get_api_version,
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
def session() -> Session:
    s = Mock(spec=Session)
    s.get_base_url2.return_value = BASE_URL
    s.api_key = "0000"
    s.verify_ssl_certs = True
    return s


@pytest.fixture(scope="module")
def request_session() -> requests.Session:
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


def test_delete(session: Session, request_session: Mock) -> None:
    """Make sure calls to _delete end up using the correct session."""
    resource_url = "/test/url"
    target_url = "{base}{url}".format(base=BASE_URL, url=resource_url)

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


def test_get(session: Session, request_session: Mock) -> None:
    """Make sure calls to _get end up using the correct session."""
    resource_url = "/test/url"
    target_url = "{base}{url}".format(base=BASE_URL, url=resource_url)

    # Regular session
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

    # Fast-failing session
    with patch(
        "pybatfish.client.restv2helper._requests_session_fail_fast", request_session
    ):
        # Execute the request, specifying fast-failing behavior
        _get(session, resource_url, None, fail_fast=True)
    # Should pass through to the correct session
    request_session.get.assert_called_with(
        target_url,
        headers=_get_headers(session),
        params=None,
        stream=False,
        verify=session.verify_ssl_certs,
    )


def test_post_json(session, request_session):
    """Make sure calls to _post of json end up using the correct session."""
    resource_url = "/test/url"
    target_url = "{base}{url}".format(base=BASE_URL, url=resource_url)
    obj = "foo"

    with patch("pybatfish.client.restv2helper._requests_session", request_session):
        # Execute the request
        _post(session, resource_url, obj)
    # Should pass through to the correct session
    request_session.post.assert_called_with(
        target_url,
        data=None,
        json=_encoder.default(obj),
        headers=_get_headers(session),
        params=None,
        verify=session.verify_ssl_certs,
    )


def test_post_stream(session, request_session):
    """Make sure calls to _post of stream end up using the correct session."""
    resource_url = "/test/url"
    target_url = "{base}{url}".format(base=BASE_URL, url=resource_url)
    with io.StringIO() as stream_data:
        with patch("pybatfish.client.restv2helper._requests_session", request_session):
            # Execute the request
            _post(session, resource_url, None, stream=stream_data)
        # Should pass through to the correct session
        expected_headers = _get_headers(session)
        expected_headers["Content-Type"] = "application/octet-stream"
        request_session.post.assert_called_with(
            target_url,
            data=stream_data,
            json=None,
            headers=expected_headers,
            params=None,
            verify=session.verify_ssl_certs,
        )


def test_put(session, request_session):
    """Make sure calls to _put end up using the correct session."""
    resource_url = "/test/url"
    target_url = "{base}{url}".format(base=BASE_URL, url=resource_url)

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
    assert retries.total == Options.max_retries_to_connect_to_coordinator
    assert retries.connect == Options.max_retries_to_connect_to_coordinator
    assert retries.read == Options.max_retries_to_connect_to_coordinator
    # All request types should be retried
    assert not retries.allowed_methods


def test_fail_fast_session_adapters():
    """Confirm fast-failing session is configured with correct http and https adapters."""
    http = _requests_session_fail_fast.adapters["http://"]
    https = _requests_session_fail_fast.adapters["https://"]
    assert http == _adapter_fail_fast
    assert https == _adapter_fail_fast
    # Also make sure retries are configured correctly
    retries = _adapter_fail_fast.max_retries
    assert retries.total == Options.max_initial_tries_to_connect_to_coordinator
    assert retries.connect == Options.max_initial_tries_to_connect_to_coordinator
    assert retries.read == Options.max_initial_tries_to_connect_to_coordinator
    # All request types should be retried
    assert not retries.allowed_methods


def test_get_api_version_old(session: Session, request_session: Mock) -> None:
    mock_response = MockResponse(json.dumps({}))
    mock_response.status_code = 200
    with patch("pybatfish.client.restv2helper._requests_session", request_session):
        request_session.get.return_value = mock_response
        assert get_api_version(session) == "2.0.0"


def test_get_api_version_new(session: Session, request_session: Mock) -> None:
    mock_response = MockResponse(json.dumps({CoordConsts.KEY_API_VERSION: "2.1.0"}))
    mock_response.status_code = 200
    with patch("pybatfish.client.restv2helper._requests_session", request_session):
        request_session.get.return_value = mock_response
        assert get_api_version(session) == "2.1.0"


if __name__ == "__main__":
    pytest.main()
