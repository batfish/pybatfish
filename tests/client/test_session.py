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
import os
from unittest.mock import patch

import pkg_resources
import pytest

from pybatfish.client.session import _PYBF_USE_DEPRECATED_WORKMGR_V1_ENV, Session

_OLD_RESPONSES = [None, {"1": "1.0.0", "2": "2.0.0"}]
_NEW_RESPONSE = {"1": "1.0.0", "2": "2.1.0"}


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

    # Add in a dummy entry point in addition to installed entry_points
    entry_points = [i for i in pkg_resources.iter_entry_points("batfish_session")] + [
        MockEntryPoint(dummy_session_type, dummy_session_module)
    ]
    with patch.object(pkg_resources, "iter_entry_points", return_value=entry_points):
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
        use_deprecated_workmgr_v1=False,
    )
    # Confirm the session is the correct type
    assert isinstance(session, Session)
    # Confirm params were passed through
    assert session.host == session_host


def test_get_session_default():
    """Confirm default Session object is built when no type is specified."""
    session_host = "foobar"
    session = Session.get(
        load_questions=False, host=session_host, use_deprecated_workmgr_v1=False
    )
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
    s = Session(api_key="foo", load_questions=False, use_deprecated_workmgr_v1=False)
    assert s.api_key == "foo"


def test_session_bf_version_not_called_before_checking_v1():
    """Ensure we do not query api_versions when intializing a Session without v1 override before checking v1"""
    with patch("pybatfish.client.apiversion.get_api_versions") as mock_get_api_versions:
        Session(load_questions=False)
        mock_get_api_versions.assert_not_called()


def test_session_bf_version_called():
    """Ensure we query api_versions when intializing a Session without v1 override and check v1"""
    with patch("pybatfish.client.apiversion.get_api_versions") as mock_get_api_versions:
        mock_get_api_versions.return_value = None
        s = Session(load_questions=False)
        s.use_deprecated_workmgr_v1()
        mock_get_api_versions.assert_called_with(s)


def test_session_bf_version_use_v1_response():
    """Ensure a session with old Batfish uses WorkMgrV1"""
    for response in _OLD_RESPONSES:
        with patch(
            "pybatfish.client.apiversion.get_api_versions"
        ) as mock_get_api_versions:
            mock_get_api_versions.return_value = response
            s = Session(load_questions=False)
            assert s.use_deprecated_workmgr_v1()


def test_session_bf_version_use_only_v2_response():
    """Ensure a session with new or dev Batfish uses WorkMgrV2 only"""
    with patch("pybatfish.client.apiversion.get_api_versions") as mock_get_api_versions:
        mock_get_api_versions.return_value = _NEW_RESPONSE
        s = Session(load_questions=False)
        assert not s.use_deprecated_workmgr_v1()


def test_session_bf_version_use_v1_arg():
    """Ensure a session with new Batfish uses WorkMgrV1 if forced in Session.__init__"""
    with patch(
        "pybatfish.client.apiversion.get_api_versions"
    ) as mock_get_api_versions, patch.dict(
        os.environ, {_PYBF_USE_DEPRECATED_WORKMGR_V1_ENV: "0"}
    ):
        mock_get_api_versions.return_value = _NEW_RESPONSE
        s = Session(load_questions=False, use_deprecated_workmgr_v1=True)
        assert s.use_deprecated_workmgr_v1()


def test_session_bf_version_use_only_v2_arg():
    """Ensure a session with new Batfish uses only WorkMgrV2 if forced in Session.__init__"""
    for response in _OLD_RESPONSES:
        with patch(
            "pybatfish.client.apiversion.get_api_versions"
        ) as mock_get_api_versions, patch.dict(
            os.environ, {_PYBF_USE_DEPRECATED_WORKMGR_V1_ENV: "1"}
        ):
            mock_get_api_versions.return_value = response
            s = Session(load_questions=False, use_deprecated_workmgr_v1=False)
            assert not s.use_deprecated_workmgr_v1()


def test_session_bf_version_use_v1_environ():
    """Ensure a session with new Batfish uses WorkMgrV1 if forced in environment"""
    with patch(
        "pybatfish.client.apiversion.get_api_versions"
    ) as mock_get_api_versions, patch.dict(
        os.environ, {_PYBF_USE_DEPRECATED_WORKMGR_V1_ENV: "1"}
    ):
        mock_get_api_versions.return_value = _NEW_RESPONSE
        s = Session(load_questions=False, use_deprecated_workmgr_v1=True)
        assert s.use_deprecated_workmgr_v1()


def test_session_bf_version_use_only_v2_environ():
    """Ensure a session with new Batfish uses WorkMgrV2 only if forced in environment"""
    for response in _OLD_RESPONSES:
        with patch(
            "pybatfish.client.apiversion.get_api_versions"
        ) as mock_get_api_versions, patch.dict(
            os.environ, {_PYBF_USE_DEPRECATED_WORKMGR_V1_ENV: "0"}
        ):
            mock_get_api_versions.return_value = response
            s = Session(load_questions=False, use_deprecated_workmgr_v1=False)
            assert not s.use_deprecated_workmgr_v1()
