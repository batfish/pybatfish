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

from pybatfish.client.options import Options
from pybatfish.client.resthelper import _adapter, _requests_session


def test_session_adapters():
    """Confirm session is configured with correct http and https adapters."""
    http = _requests_session.adapters["http://"]
    https = _requests_session.adapters["https://"]

    assert http == _adapter
    assert https == _adapter
    # Also make sure retries are configured
    retries = _adapter.max_retries
    assert retries.connect == Options.max_retries_to_connect_to_coordinator
    assert retries.read == Options.max_retries_to_connect_to_coordinator
    # All request types should be retried
    assert not retries.method_whitelist
