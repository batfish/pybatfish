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
from unittest.mock import patch

import pytest

from pybatfish.client.session import Session
from pybatfish.datamodel import VariableType


class MockEntryPoint:
    def __init__(self, name, module_):
        self.name = name
        self.module = module_

    def load(self):
        return self.module


def test_get_session_types():
    """Test getting possible session types."""
    dummy_session_type = "dummy"
    dummy_session_module = "dummy_session_module"

    from importlib.metadata import entry_points

    eps = entry_points(group="batfish_session")
    mock_eps = list(eps) + [MockEntryPoint(dummy_session_type, dummy_session_module)]

    with patch("importlib.metadata.entry_points", return_value=mock_eps):
        session_types = Session.get_session_types()

    # Confirm both the base and our mock types show up
    assert "bf" in session_types.keys()
    assert dummy_session_type in session_types.keys()


def test_get_session():
    """Confirm Session object is built for a specified session type."""
    session_host = "foobar"
    session = Session.get(
        type_="bf",
        load_questions=False,
        host=session_host,
    )
    # Confirm the session is the correct type
    assert isinstance(session, Session)
    # Confirm params were passed through
    assert session.host == session_host


def test_get_session_default():
    """Confirm default Session object is built when no type is specified."""
    session_host = "foobar"
    session = Session.get(load_questions=False, host=session_host)
    # Confirm the session is the correct type
    assert isinstance(session, Session)
    # Confirm params were passed through
    assert session.host == session_host


def test_get_session_bad():
    """Confirm an exception is thrown when a bad session type passed in."""
    bogus_type = "bogus_session_type"
    with pytest.raises(ValueError) as e:
        Session.get(type_=bogus_type)
    e_msg = str(e.value)
    assert "Invalid session type" in e_msg
    assert f"type '{bogus_type}' does not match" in e_msg


def test_session_api_key():
    """Ensure we use api key from constructor."""
    s = Session(api_key="foo", load_questions=False)
    assert s.api_key == "foo"


def test_auto_complete_invalid_max_suggestions():
    """Ensure auto_complete raises with invalid max suggestions"""
    s = Session(load_questions=False)
    with pytest.raises(ValueError):
        s.auto_complete(VariableType.BGP_ROUTE_STATUS_SPEC, "foo", -1)


def test_default_port():
    s = Session(load_questions=False)
    assert s.port_v2 == 9996


def test_port_set():
    s = Session(port=8888, port_v2=1111, load_questions=False)
    assert s.port_v2 == 8888


def test_port_v2_set():
    s = Session(port_v2=8888, load_questions=False)
    assert s.port_v2 == 8888


def test_request_kwargs_defaults():
    """Confirm default request kwargs are empty with timeout=30."""
    s = Session(load_questions=False)
    assert s.proxies is None
    assert s.timeout == 30
    assert s.request_kwargs == {}
    # Default: timeout is applied, proxies are not
    assert s._get_request_kwargs() == {"timeout": 30}


def test_request_kwargs_custom_timeout():
    """Confirm custom timeout is passed through."""
    s = Session(load_questions=False, timeout=60)
    assert s._get_request_kwargs() == {"timeout": 60}


def test_request_kwargs_timeout_none():
    """Confirm timeout=None means no timeout kwarg is forwarded."""
    s = Session(load_questions=False, timeout=None)
    assert "timeout" not in s._get_request_kwargs()


def test_request_kwargs_proxies():
    """Confirm proxies are forwarded when set."""
    proxies = {"http": "http://proxy:8080", "https": "http://proxy:8080"}
    s = Session(load_questions=False, proxies=proxies)
    result = s._get_request_kwargs()
    assert result["proxies"] == proxies


def test_request_kwargs_generic():
    """Confirm generic request_kwargs are forwarded."""
    s = Session(load_questions=False, timeout=None, request_kwargs={"verify": False})
    result = s._get_request_kwargs()
    assert result == {"verify": False}


def test_request_kwargs_explicit_params_override_generic():
    """Confirm explicit params take precedence over values in request_kwargs."""
    s = Session(
        load_questions=False,
        timeout=10,
        proxies={"http": "http://proxy:8080"},
        request_kwargs={"timeout": 999, "proxies": {"http": "http://other:9090"}},
    )
    result = s._get_request_kwargs()
    # Explicit timeout and proxies should win
    assert result["timeout"] == 10
    assert result["proxies"] == {"http": "http://proxy:8080"}
