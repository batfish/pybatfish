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
from requests import HTTPError, Response

from pybatfish.client import restv2helper
from pybatfish.client.restv2helper import (
    _delete,
    _encoder,
    _get,
    _get_headers,
    _post,
    _put,
)


class MockResponse(Response):
    def __init__(self, text):
        super(MockResponse, self).__init__()
        self._text = text

    @property
    def text(self):
        return self._text


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


def test_delete():
    """Make sure calls to _delete end up using the correct session."""
    base_url = "base"
    resource_url = "/test/url"
    target_url = "base{url}".format(base=base_url, url=resource_url)
    session = Mock()
    session.get_base_url2.return_value = base_url

    with patch.object(restv2helper._requests_session, "delete") as mock:
        # Execute the request
        _delete(session, resource_url)
    # Should pass through to the correct session
    mock.assert_called_with(
        target_url,
        headers=_get_headers(session),
        params=None,
        verify=session.verify_ssl_certs,
    )


def test_get():
    """Make sure calls to _get end up using the correct session."""
    base_url = "base"
    resource_url = "/test/url"
    target_url = "base{url}".format(base=base_url, url=resource_url)
    session = Mock()
    session.get_base_url2.return_value = base_url

    with patch.object(restv2helper._requests_session, "get") as mock:
        # Execute the request
        _get(session, resource_url, None)
    # Should pass through to the correct session
    mock.assert_called_with(
        target_url,
        headers=_get_headers(session),
        params=None,
        stream=False,
        verify=session.verify_ssl_certs,
    )


def test_post():
    """Make sure calls to _post end up using the correct session."""
    base_url = "base"
    resource_url = "/test/url"
    target_url = "base{url}".format(base=base_url, url=resource_url)
    session = Mock()
    session.get_base_url2.return_value = base_url
    obj = "foo"

    with patch.object(restv2helper._requests_session, "post") as mock:
        # Execute the request
        _post(session, resource_url, obj)
    # Should pass through to the correct session
    mock.assert_called_with(
        target_url,
        json=_encoder.default(obj),
        headers=_get_headers(session),
        params=None,
        verify=session.verify_ssl_certs,
    )


def test_put():
    """Make sure calls to _put end up using the correct session."""
    base_url = "base"
    resource_url = "/test/url"
    target_url = "base{url}".format(base=base_url, url=resource_url)
    session = Mock()
    session.get_base_url2.return_value = base_url

    with patch.object(restv2helper._requests_session, "put") as mock:
        # Execute the request
        _put(session, resource_url)
    # Should pass through to the correct session
    mock.assert_called_with(
        target_url,
        json=None,
        data=None,
        headers=_get_headers(session),
        verify=session.verify_ssl_certs,
        params=None,
    )


if __name__ == "__main__":
    pytest.main()
