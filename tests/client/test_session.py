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
from unittest.mock import patch

import pytest

from pybatfish.client.session import Session
from pybatfish.datamodel import VariableType


class MockEntryPoint(object):
    def __init__(self, name, module_):
        self.name = name
        self.module = module_

    def load(self):
        return self.module


def test_get_session_types():
    """Test getting possible session types."""
    dummy_session_type = "dummy"
    dummy_session_module = "dummy_session_module"

    import sys
    from importlib.metadata import entry_points

    if sys.version_info < (3, 10):
        eps = list(entry_points().get("batfish_session", [])) + [
            MockEntryPoint(dummy_session_type, dummy_session_module)
        ]
        mock_eps = {"batfish_session": eps}
    else:
        eps = entry_points(group="batfish_session")
        mock_eps = list(eps) + [
            MockEntryPoint(dummy_session_type, dummy_session_module)
        ]

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
    assert "type '{}' does not match".format(bogus_type) in e_msg


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
