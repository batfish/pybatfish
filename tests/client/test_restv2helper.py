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

import pytest
from requests import HTTPError, Response

from pybatfish.client import restv2helper


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


if __name__ == "__main__":
    pytest.main()
